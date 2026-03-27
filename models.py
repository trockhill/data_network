from sqlalchemy import Column, String, Text, Integer, DateTime
from database import Base


class Node(Base):
    __tablename__ = "nodes"
    id               = Column(String, primary_key=True)
    name             = Column(String, nullable=False)
    node_type        = Column(String, nullable=False, default="table")
    owner            = Column(String, default="")
    description      = Column(Text, default="")
    update_frequency = Column(String, default="")
    tags             = Column(Text, default="[]")   # JSON配列文字列


class Edge(Base):
    __tablename__ = "edges"
    id          = Column(String, primary_key=True)
    source_id   = Column(String, nullable=False)
    target_id   = Column(String, nullable=False)
    label       = Column(String, default="")
    description = Column(Text, default="")


class NodeColumn(Base):
    __tablename__ = "columns"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    node_id     = Column(String, nullable=False)
    name        = Column(String, nullable=False, default="")
    data_type   = Column(String, default="")
    pk          = Column(String, default="")
    description = Column(Text, default="")


class NodeScript(Base):
    __tablename__ = "scripts"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    node_id     = Column(String, nullable=False, unique=True)
    script_type = Column(String, default="sql")
    content     = Column(Text, default="")
    file_path   = Column(String, default="")
    description = Column(Text, default="")


class AppLock(Base):
    __tablename__ = "app_lock"
    id        = Column(Integer, primary_key=True, default=1)
    locked_by = Column(String, nullable=True)
    locked_at = Column(DateTime, nullable=True)
    hostname  = Column(String, nullable=True)
    heartbeat = Column(DateTime, nullable=True)
