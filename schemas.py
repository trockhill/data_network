from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ===== Node =====
class NodeBase(BaseModel):
    name: str
    node_type: str = "table"
    owner: str = ""
    description: str = ""
    update_frequency: str = ""
    tags: List[str] = []


class NodeCreate(NodeBase):
    id: str


class NodeUpdate(NodeBase):
    pass


class NodeOut(NodeCreate):
    model_config = {"from_attributes": True}


# ===== Edge =====
class EdgeBase(BaseModel):
    source_id: str
    target_id: str
    label: str = ""
    description: str = ""


class EdgeCreate(EdgeBase):
    id: str


class EdgeUpdate(EdgeBase):
    pass


class EdgeOut(EdgeCreate):
    model_config = {"from_attributes": True}


# ===== NodeColumn =====
class ColumnItem(BaseModel):
    name: str
    data_type: str = ""
    pk: str = ""
    description: str = ""


class ColumnOut(ColumnItem):
    id: int
    node_id: str
    model_config = {"from_attributes": True}


# ===== NodeScript =====
class ScriptUpsert(BaseModel):
    script_type: str = "sql"
    content: str = ""
    file_path: str = ""
    description: str = ""


class ScriptOut(ScriptUpsert):
    id: int
    node_id: str
    model_config = {"from_attributes": True}


# ===== Lock =====
class LockStatus(BaseModel):
    locked: bool
    locked_by: Optional[str] = None
    locked_at: Optional[datetime] = None
    hostname: Optional[str] = None
    is_stale: bool = False
    minutes_ago: Optional[int] = None


class LockAcquireRequest(BaseModel):
    user_name: str
    hostname: str
