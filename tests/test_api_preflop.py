import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_preflop_rejects_bad_stack():
    r = client.post("/preflop", json={"stack_bb": 0, "iterations": 100})
    assert r.status_code == 422


@pytest.mark.slow
def test_preflop_returns_tree_and_charts():
    r = client.post("/preflop", json={"stack_bb": 50, "iterations": 300})
    assert r.status_code == 200
    body = r.json()
    assert body["root"] == ""
    root = body["nodes"][""]
    assert root["player"] == 0  # SB first-in
    assert len(root["chart"]) == 169
    assert root["chart"]["AA"]["raise"] > 0.9
    # a deeper node exists (BB facing the open)
    assert "raise" in body["nodes"]
    assert body["nodes"]["raise"]["player"] == 1
