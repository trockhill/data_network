import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Node, Edge

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/relations")
def export_relations(db: Session = Depends(get_db)):
    nodes = {n.id: n for n in db.query(Node).all()}
    edges = db.query(Edge).all()

    buf = io.StringIO()
    buf.write("\ufeff")  # UTF-8 BOM
    writer = csv.writer(buf)
    writer.writerow(["接続元ノード名", "接続元ID", "接続元種別",
                     "接続先ノード名", "接続先ID", "接続先種別",
                     "ラベル", "説明"])
    for e in edges:
        src = nodes.get(e.source_id)
        tgt = nodes.get(e.target_id)
        writer.writerow([
            src.name if src else e.source_id, e.source_id, src.node_type if src else "",
            tgt.name if tgt else e.target_id, e.target_id, tgt.node_type if tgt else "",
            e.label or "", e.description or ""
        ])

    buf.seek(0)
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode("utf-8-sig")),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename*=UTF-8''network_relations.csv"}
    )
