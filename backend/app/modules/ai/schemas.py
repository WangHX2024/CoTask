"""Pydantic output schemas for LLM responses."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_DEPTH = 5
MAX_NODES = 200


class TreeNodeOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(..., max_length=200)
    description: str | None = Field(default="", max_length=1000)
    start_date: date | None = None
    end_date: date | None = None
    assignees: list[int] = Field(default_factory=list, max_length=3)
    children: list["TreeNodeOut"] = Field(default_factory=list)

    @field_validator("assignees")
    @classmethod
    def normalize_assignees(cls, v: list[int]) -> list[int]:
        return [int(x) for x in (v or [])]

    @field_validator("title")
    @classmethod
    def trim_title(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("title required")
        return v


TreeNodeOut.model_rebuild()


class TreeGenOut(BaseModel):
    nodes: list[TreeNodeOut]
    summary: str = ""


class TreeEditOut(BaseModel):
    nodes: list[TreeNodeOut]
    diff_summary: str = ""


class DailyAdviceOut(BaseModel):
    advice: str
    suggestions: list[str] = Field(default_factory=list, max_length=8)


class AssignmentSuggestion(BaseModel):
    task_id: int
    assignees: list[int]
    reason: str = ""


class AssignmentOut(BaseModel):
    suggestions: list[AssignmentSuggestion]


def count_nodes(nodes: list[TreeNodeOut]) -> int:
    return sum(1 + count_nodes(n.children) for n in nodes)


def _check_assignees(nodes: list[TreeNodeOut], member_ids: set[int]) -> None:
    for node in nodes:
        for uid in node.assignees:
            if uid not in member_ids:
                raise ValueError(f"assignee {uid} is not a group member")
        if node.children:
            _check_assignees(node.children, member_ids)


def validate_tree(out: TreeGenOut | TreeEditOut, *, member_ids: set[int] | None = None):
    n = count_nodes(out.nodes)
    if n == 0:
        raise ValueError("tree must have at least one node")
    if n > MAX_NODES:
        raise ValueError(f"tree too large: {n} > {MAX_NODES}")

    def _check_depth(node: TreeNodeOut, depth: int):
        if depth > MAX_DEPTH:
            raise ValueError("tree too deep")
        for c in node.children:
            _check_depth(c, depth + 1)

    for r in out.nodes:
        _check_depth(r, 1)
    if member_ids is not None:
        _check_assignees(out.nodes, member_ids)
    return out
