from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import NodeColumn
from schemas import ColumnItem, ColumnOut

router = APIRouter(prefix="/api/columns", tags=["columns"])


@router.get("/{node_id}", response_model=list[ColumnOut])
def get_columns(node_id: str, db: Session = Depends(get_db)):
    return db.query(NodeColumn).filter(NodeColumn.node_id == node_id).all()


@router.put("/{node_id}", response_model=list[ColumnOut])
def upsert_columns(node_id: str, body: list[ColumnItem], db: Session = Depends(get_db)):
    db.query(NodeColumn).filter(NodeColumn.node_id == node_id).delete()
    new_cols = [
        NodeColumn(
            node_id=node_id, name=c.name, data_type=c.data_type,
            pk=c.pk, description=c.description
        )
        for c in body
    ]
    db.add_all(new_cols)
    db.commit()
    return db.query(NodeColumn).filter(NodeColumn.node_id == node_id).all()
