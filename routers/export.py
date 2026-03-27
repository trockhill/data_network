import csv
import io
import json
from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Node, Edge, NodeColumn, NodeScript

router = APIRouter(prefix="/api/export", tags=["export"])


def _make_response(buf: io.StringIO, filename: str) -> StreamingResponse:
    buf.seek(0)
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode("utf-8-sig")),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    )


def _parse_ids(node_ids: Optional[str]):
    if not node_ids:
        return None
    return [i.strip() for i in node_ids.split(",") if i.strip()]


# ───── nodes.csv ─────
@router.get("/nodes")
def export_nodes(node_ids: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Node)
    ids = _parse_ids(node_ids)
    if ids:
        q = q.filter(Node.id.in_(ids))
    nodes = q.all()

    buf = io.StringIO()
    buf.write("\ufeff")
    w = csv.writer(buf)
    w.writerow(["id", "name", "node_type", "owner", "description", "update_frequency", "tags"])
    for n in nodes:
        try:
            tags_str = ",".join(json.loads(n.tags or "[]"))
        except Exception:
            tags_str = n.tags or ""
        w.writerow([n.id, n.name, n.node_type, n.owner or "", n.description or "",
                    n.update_frequency or "", tags_str])
    return _make_response(buf, "nodes.csv")


# ───── edges.csv ─────
@router.get("/edges")
def export_edges(node_ids: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Edge)
    ids = _parse_ids(node_ids)
    if ids:
        id_set = set(ids)
        # keep edges where either endpoint is in the selected set
        q = q.filter((Edge.source_id.in_(id_set)) | (Edge.target_id.in_(id_set)))
    edges = q.all()

    buf = io.StringIO()
    buf.write("\ufeff")
    w = csv.writer(buf)
    w.writerow(["id", "source_id", "target_id", "label", "description"])
    for e in edges:
        w.writerow([e.id, e.source_id, e.target_id, e.label or "", e.description or ""])
    return _make_response(buf, "edges.csv")


# ───── columns.csv ─────
@router.get("/columns")
def export_columns(node_ids: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(NodeColumn)
    ids = _parse_ids(node_ids)
    if ids:
        q = q.filter(NodeColumn.node_id.in_(ids))
    cols = q.all()

    buf = io.StringIO()
    buf.write("\ufeff")
    w = csv.writer(buf)
    w.writerow(["node_id", "name", "data_type", "pk", "description"])
    for c in cols:
        w.writerow([c.node_id, c.name, c.data_type or "", c.pk or "", c.description or ""])
    return _make_response(buf, "columns.csv")


# ───── scripts.csv ─────
@router.get("/scripts")
def export_scripts(node_ids: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(NodeScript)
    ids = _parse_ids(node_ids)
    if ids:
        q = q.filter(NodeScript.node_id.in_(ids))
    scripts = q.all()

    buf = io.StringIO()
    buf.write("\ufeff")
    w = csv.writer(buf)
    w.writerow(["node_id", "script_type", "content", "file_path", "description"])
    for s in scripts:
        w.writerow([s.node_id, s.script_type or "sql", s.content or "",
                    s.file_path or "", s.description or ""])
    return _make_response(buf, "scripts.csv")


# ───── relations.csv（既存 + node_ids フィルター追加）─────
@router.get("/relations")
def export_relations(node_ids: Optional[str] = None, db: Session = Depends(get_db)):
    nodes = {n.id: n for n in db.query(Node).all()}
    q = db.query(Edge)
    ids = _parse_ids(node_ids)
    if ids:
        id_set = set(ids)
        q = q.filter((Edge.source_id.in_(id_set)) | (Edge.target_id.in_(id_set)))
    edges = q.all()

    buf = io.StringIO()
    buf.write("\ufeff")
    w = csv.writer(buf)
    w.writerow(["接続元ノード名", "接続元ID", "接続元種別",
                "接続先ノード名", "接続先ID", "接続先種別",
                "ラベル", "説明"])
    for e in edges:
        src = nodes.get(e.source_id)
        tgt = nodes.get(e.target_id)
        w.writerow([
            src.name if src else e.source_id, e.source_id, src.node_type if src else "",
            tgt.name if tgt else e.target_id, e.target_id, tgt.node_type if tgt else "",
            e.label or "", e.description or ""
        ])
    return _make_response(buf, "relations.csv")
