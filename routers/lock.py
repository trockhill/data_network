from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import AppLock
from schemas import LockStatus, LockAcquireRequest

router = APIRouter(prefix="/api/lock", tags=["lock"])

STALE_MINUTES = 5


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_stale(heartbeat: datetime | None) -> bool:
    if heartbeat is None:
        return True
    return (_now() - heartbeat) > timedelta(minutes=STALE_MINUTES)


def _to_status(row: AppLock) -> LockStatus:
    locked = row.locked_by is not None
    if not locked:
        return LockStatus(locked=False)
    stale = _is_stale(row.heartbeat)
    minutes_ago = None
    if row.heartbeat:
        minutes_ago = int((_now() - row.heartbeat).total_seconds() / 60)
    return LockStatus(
        locked=True, locked_by=row.locked_by, locked_at=row.locked_at,
        hostname=row.hostname, is_stale=stale, minutes_ago=minutes_ago
    )


def init_lock(db: Session):
    row = db.query(AppLock).filter(AppLock.id == 1).first()
    if not row:
        db.add(AppLock(id=1, locked_by=None))
        db.commit()


def release_lock_on_shutdown(db: Session):
    row = db.query(AppLock).filter(AppLock.id == 1).first()
    if row:
        row.locked_by = None
        row.locked_at = None
        row.hostname = None
        row.heartbeat = None
        db.commit()


@router.get("", response_model=LockStatus)
def get_lock(db: Session = Depends(get_db)):
    row = db.query(AppLock).filter(AppLock.id == 1).first()
    if not row:
        return LockStatus(locked=False)
    return _to_status(row)


@router.post("/acquire", response_model=LockStatus)
def acquire_lock(body: LockAcquireRequest, db: Session = Depends(get_db)):
    row = db.query(AppLock).filter(AppLock.id == 1).first()
    if not row:
        row = AppLock(id=1)
        db.add(row)

    if row.locked_by is not None and not _is_stale(row.heartbeat):
        raise HTTPException(409, f"{row.locked_by} が使用中です ({row.hostname})")

    now = _now()
    row.locked_by = body.user_name
    row.locked_at = now
    row.hostname = body.hostname
    row.heartbeat = now
    db.commit()
    db.refresh(row)
    return _to_status(row)


@router.post("/release", status_code=204)
def release_lock(db: Session = Depends(get_db)):
    row = db.query(AppLock).filter(AppLock.id == 1).first()
    if row:
        row.locked_by = None
        row.locked_at = None
        row.hostname = None
        row.heartbeat = None
        db.commit()


@router.post("/heartbeat", response_model=LockStatus)
def heartbeat(db: Session = Depends(get_db)):
    row = db.query(AppLock).filter(AppLock.id == 1).first()
    if not row or not row.locked_by:
        raise HTTPException(400, "ロックが取得されていません")
    row.heartbeat = _now()
    db.commit()
    db.refresh(row)
    return _to_status(row)


@router.post("/force-release", response_model=LockStatus)
def force_release(db: Session = Depends(get_db)):
    row = db.query(AppLock).filter(AppLock.id == 1).first()
    if not row:
        return LockStatus(locked=False)
    if not _is_stale(row.heartbeat):
        raise HTTPException(403, "アクティブなセッションは強制解放できません")
    row.locked_by = None
    row.locked_at = None
    row.hostname = None
    row.heartbeat = None
    db.commit()
    return LockStatus(locked=False)
