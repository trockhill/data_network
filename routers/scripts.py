from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import NodeScript
from schemas import ScriptUpsert, ScriptOut

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


@router.get("/{node_id}", response_model=ScriptOut | None)
def get_script(node_id: str, db: Session = Depends(get_db)):
    return db.query(NodeScript).filter(NodeScript.node_id == node_id).first()


@router.put("/{node_id}", response_model=ScriptOut)
def upsert_script(node_id: str, body: ScriptUpsert, db: Session = Depends(get_db)):
    sc = db.query(NodeScript).filter(NodeScript.node_id == node_id).first()
    if sc:
        sc.script_type = body.script_type
        sc.content = body.content
        sc.file_path = body.file_path
        sc.description = body.description
    else:
        sc = NodeScript(
            node_id=node_id, script_type=body.script_type,
            content=body.content, file_path=body.file_path,
            description=body.description
        )
        db.add(sc)
    db.commit()
    db.refresh(sc)
    return sc
