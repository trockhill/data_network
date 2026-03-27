import csv
import io
import json
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Node, Edge, NodeColumn, NodeScript

router = APIRouter(prefix="/api/import", tags=["import"])

# 各CSVの必須ヘッダー / 許可ヘッダー
REQUIRED_HEADERS = {
    "nodes":   {"id", "name"},
    "edges":   {"source_id", "target_id"},
    "columns": {"node_id", "name"},
    "scripts": {"node_id"},
}
ALLOWED_HEADERS = {
    "nodes":   {"id", "name", "node_type", "owner", "description", "update_frequency", "tags"},
    "edges":   {"id", "source_id", "target_id", "label", "description"},
    "columns": {"node_id", "name", "data_type", "pk", "description"},
    "scripts": {"node_id", "script_type", "content", "file_path", "description"},
}


def parse_csv(content: bytes) -> list[dict]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader), set(reader.fieldnames or [])


def validate_headers(kind: str, actual: set[str]):
    """必須ヘッダーが揃っているか・不明ヘッダーがないか検証"""
    required = REQUIRED_HEADERS[kind]
    allowed  = ALLOWED_HEADERS[kind]

    missing  = required - actual
    unknown  = actual - allowed

    errors = []
    if missing:
        errors.append(f"必須列が不足しています: {', '.join(sorted(missing))}")
    if unknown:
        errors.append(f"不明な列が含まれています: {', '.join(sorted(unknown))}")
    if errors:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "CSVのヘッダーが正しくありません。",
                "errors": errors,
                "required": sorted(required),
                "allowed": sorted(allowed),
                "actual": sorted(actual),
            }
        )


@router.post("/nodes")
def import_nodes(file: UploadFile = File(...), db: Session = Depends(get_db)):
    rows, headers = parse_csv(file.file.read())
    validate_headers("nodes", headers)
    count = 0
    for r in rows:
        nid = (r.get("id") or "").strip()
        if not nid:
            continue
        tags_raw = (r.get("tags") or "").strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        existing = db.query(Node).filter(Node.id == nid).first()
        if existing:
            existing.name             = r.get("name", existing.name)
            existing.node_type        = r.get("node_type", existing.node_type)
            existing.owner            = r.get("owner", existing.owner or "")
            existing.description      = r.get("description", existing.description or "")
            existing.update_frequency = r.get("update_frequency", existing.update_frequency or "")
            existing.tags             = json.dumps(tags, ensure_ascii=False)
        else:
            db.add(Node(
                id=nid,
                name=r.get("name", nid),
                node_type=r.get("node_type", "table"),
                owner=r.get("owner", ""),
                description=r.get("description", ""),
                update_frequency=r.get("update_frequency", ""),
                tags=json.dumps(tags, ensure_ascii=False)
            ))
        count += 1
    db.commit()
    return {"imported": count}


@router.post("/edges")
def import_edges(file: UploadFile = File(...), db: Session = Depends(get_db)):
    rows, headers = parse_csv(file.file.read())
    validate_headers("edges", headers)
    count = 0
    for r in rows:
        eid = (r.get("id") or "").strip() or str(uuid.uuid4())[:8]
        src = (r.get("source_id") or "").strip()
        tgt = (r.get("target_id") or "").strip()
        if not src or not tgt:
            continue
        existing = db.query(Edge).filter(Edge.id == eid).first()
        if existing:
            existing.source_id   = src
            existing.target_id   = tgt
            existing.label       = r.get("label", existing.label or "")
            existing.description = r.get("description", existing.description or "")
        else:
            db.add(Edge(
                id=eid, source_id=src, target_id=tgt,
                label=r.get("label", ""),
                description=r.get("description", "")
            ))
        count += 1
    db.commit()
    return {"imported": count}


@router.post("/columns")
def import_columns(file: UploadFile = File(...), db: Session = Depends(get_db)):
    rows, headers = parse_csv(file.file.read())
    validate_headers("columns", headers)
    node_ids = {r.get("node_id", "").strip() for r in rows if r.get("node_id", "").strip()}
    for nid in node_ids:
        db.query(NodeColumn).filter(NodeColumn.node_id == nid).delete()
    for r in rows:
        nid = r.get("node_id", "").strip()
        if not nid:
            continue
        db.add(NodeColumn(
            node_id=nid,
            name=r.get("name") or "",
            data_type=r.get("data_type", ""),
            pk=r.get("pk", ""),
            description=r.get("description", "")
        ))
    db.commit()
    return {"imported": len(rows)}


@router.post("/scripts")
def import_scripts(file: UploadFile = File(...), db: Session = Depends(get_db)):
    rows, headers = parse_csv(file.file.read())
    validate_headers("scripts", headers)
    count = 0
    for r in rows:
        nid = r.get("node_id", "").strip()
        if not nid:
            continue
        sc = db.query(NodeScript).filter(NodeScript.node_id == nid).first()
        if sc:
            sc.script_type = r.get("script_type", sc.script_type)
            sc.content     = r.get("content", sc.content or "")
            sc.file_path   = r.get("file_path", sc.file_path or "")
            sc.description = r.get("description", sc.description or "")
        else:
            db.add(NodeScript(
                node_id=nid,
                script_type=r.get("script_type", "sql"),
                content=r.get("content", ""),
                file_path=r.get("file_path", ""),
                description=r.get("description", "")
            ))
        count += 1
    db.commit()
    return {"imported": count}
