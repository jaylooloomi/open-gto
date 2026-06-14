import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_solve_rejects_unknown_game():
    # Validation happens before any solving, so this is fast and needs no data.
    r = client.post("/solve", json={"game": "nope", "params": {}, "iterations": 10})
    assert r.status_code == 422


def test_solve_rejects_bad_iterations():
    r = client.post(
        "/solve", json={"game": "push_fold", "params": {"stack_bb": 10}, "iterations": 0}
    )
    assert r.status_code == 422


@pytest.mark.slow
def test_solve_push_fold_returns_charts():
    r = client.post(
        "/solve",
        json={"game": "push_fold", "params": {"stack_bb": 10}, "iterations": 1000},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["sb_jam"]) == 169
    assert all(0.0 <= v <= 1.0 for v in body["sb_jam"].values())
    assert body["sb_jam"]["AA"] > 0.99
    assert "exploitability" in body
