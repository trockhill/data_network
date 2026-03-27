import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Node, Edge, NodeColumn, NodeScript
from schemas import NodeCreate, NodeUpdate, NodeOut

router = APIRouter(prefix="/api/nodes", tags=["nodes"])


def _to_out(node: Node) -> NodeOut:
    tags = []
    try:
        tags = json.loads(node.tags or "[]")
    except Exception:
        pass
    return NodeOut(
        id=node.id, name=node.name, node_type=node.node_type,
        owner=node.owner or "", description=node.description or "",
        update_frequency=node.update_frequency or "", tags=tags
    )


@router.get("", response_model=list[NodeOut])
def list_nodes(db: Session = Depends(get_db)):
    return [_to_out(n) for n in db.query(Node).all()]


@router.post("", response_model=NodeOut, status_code=201)
def create_node(body: NodeCreate, db: Session = Depends(get_db)):
    if db.query(Node).filter(Node.id == body.id).first():
        raise HTTPException(409, f"Node '{body.id}' already exists")
    node = Node(
        id=body.id, name=body.name, node_type=body.node_type,
        owner=body.owner, description=body.description,
        update_frequency=body.update_frequency,
        tags=json.dumps(body.tags, ensure_ascii=False)
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return _to_out(node)


@router.put("/{node_id}", response_model=NodeOut)
def update_node(node_id: str, body: NodeUpdate, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(404, "Node not found")
    node.name = body.name
    node.node_type = body.node_type
    node.owner = body.owner
    node.description = body.description
    node.update_frequency = body.update_frequency
    node.tags = json.dumps(body.tags, ensure_ascii=False)
    db.commit()
    db.refresh(node)
    return _to_out(node)


@router.delete("/{node_id}", status_code=204)
def delete_node(node_id: str, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(404, "Node not found")
    db.query(Edge).filter(
        (Edge.source_id == node_id) | (Edge.target_id == node_id)
    ).delete(synchronize_session=False)
    db.query(NodeColumn).filter(NodeColumn.node_id == node_id).delete(synchronize_session=False)
    db.query(NodeScript).filter(NodeScript.node_id == node_id).delete(synchronize_session=False)
    db.delete(node)
    db.commit()
