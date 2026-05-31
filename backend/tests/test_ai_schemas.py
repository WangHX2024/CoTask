import pytest
from app.modules.ai.schemas import TreeGenOut, validate_tree, count_nodes


def test_tree_gen_ok():
    data = {
        "summary": "ok",
        "nodes": [
            {
                "title": "Root",
                "start_date": "2026-05-01",
                "end_date": "2026-06-01",
                "assignees": [1],
                "children": [
                    {
                        "title": "Leaf",
                        "start_date": "2026-05-10",
                        "end_date": "2026-05-20",
                        "assignees": [2],
                        "children": [],
                    },
                ],
            }
        ],
    }
    out = TreeGenOut(**data)
    validate_tree(out, member_ids={1, 2})
    assert count_nodes(out.nodes) == 2


def test_tree_gen_ignores_extra_is_leaf():
    data = {
        "summary": "ok",
        "nodes": [
            {
                "title": "Root",
                "is_leaf": True,
                "assignees": [],
                "children": [{"title": "Child", "is_leaf": False, "children": []}],
            }
        ],
    }
    out = TreeGenOut(**data)
    validate_tree(out)
    assert len(out.nodes[0].children) == 1


def test_tree_gen_reject_invalid_assignee():
    data = {
        "summary": "ok",
        "nodes": [{"title": "Root", "assignees": [99], "children": []}],
    }
    out = TreeGenOut(**data)
    with pytest.raises(ValueError, match="assignee"):
        validate_tree(out, member_ids={1, 2})


def test_tree_gen_reject_too_deep():
    nested = {"title": "L0", "children": []}
    cur = nested
    for i in range(7):
        cur["children"] = [{"title": f"L{i+1}", "children": []}]
        cur = cur["children"][0]
    out = TreeGenOut(**{"nodes": [nested]})
    with pytest.raises(ValueError):
        validate_tree(out)
