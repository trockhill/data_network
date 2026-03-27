import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Edge
from schemas import EdgeCreate, EdgeUpdate, EdgeOut

router = APIRouter(prefix="/api/edges", tags=["edges"])


@router.get("", response_model=list[EdgeOut])
def list_edges(db: Session = Depends(get_db)):
    return db.query(Edge).all()


@router.post("", response_model=EdgeOut, status_code=201)
def create_edge(body: EdgeCreate, db: Session = Depends(get_db)):
    edge_id = body.id or str(uuid.uuid4())[:8]
    edge = Edge(
        id=edge_id, source_id=body.source_id, target_id=body.target_id,
        label=body.label, description=body.description
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)
    return edge


@router.put("/{edge_id}", response_model=EdgeOut)
def update_edge(edge_id: str, body: EdgeUpdate, db: Session = Depends(get_db)):
    edge = db.query(Edge).filter(Edge.id == edge_id).first()
    if not edge:
        raise HTTPException(404, "Edge not found")
    edge.source_id = body.source_id
    edge.target_id = body.target_id
    edge.label = body.label
    edge.description = body.description
    db.commit()
    db.refresh(edge)
    return edge


@router.delete("/{edge_id}", status_code=204)
def delete_edge(edge_id: str, db: Session = Depends(get_db)):
    edge = db.query(Edge).filter(Edge.id == edge_id).first()
    if not edge:
        raise HTTPException(404, "Edge not found")
    db.delete(edge)
    db.commit()
