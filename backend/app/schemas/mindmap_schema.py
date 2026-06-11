# schemas/mindmap_schema.py
from pydantic import BaseModel
from typing import Any


class Position(BaseModel):
    x: float = 0
    y: float = 0


class NodeData(BaseModel):
    label:    str
    keywords: list[str] = []
    summary:  str = ""
    depth:    int = 0


class FlowNode(BaseModel):
    id:       str
    type:     str           # "root" | "branch" | "leaf"
    data:     NodeData
    position: Position


class FlowEdge(BaseModel):
    id:     str
    source: str
    target: str
    type:   str = "smoothstep"


class MindmapStats(BaseModel):
    total_nodes: int
    total_edges: int
    depth:       int
    keywords:    list[str]


class MindmapResponse(BaseModel):
    title: str
    nodes: list[FlowNode]
    edges: list[FlowEdge]
    stats: MindmapStats
