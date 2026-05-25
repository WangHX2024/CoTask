import pytest
from app.modules.ai.schemas import TreeGenOut, validate_tree, count_nodes


def test_tree_gen_ok():
    data = {
        "summary": "ok",
        "nodes": [
            {
                "title": "Root",
                "is_leaf": False,
                "children": [
                    {"title": "Leaf", "is_leaf": True},
                ],
            }
        ],
    }
    out = TreeGenOut(**data)
    validate_tree(out)
    assert count_nodes(out.nodes) == 2


def test_tree_gen_reject_too_deep():
    nested = {"title": "L0", "children": []}
    cur = nested
    for i in range(7):
        cur["children"] = [{"title": f"L{i+1}", "children": []}]
        cur = cur["children"][0]
    out = TreeGenOut(**{"nodes": [nested]})
    with pytest.raises(ValueError):
        validate_tree(out)
