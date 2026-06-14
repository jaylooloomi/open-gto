import json

import pytest

from engine.cli import main


def test_kuhn_cli_outputs_metrics(capsys):
    rc = main(["kuhn", "--iters", "2000", "--variant", "cfr_plus"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert "exploitability" in out
    assert out["exploitability"] < 0.05


@pytest.mark.slow
def test_push_fold_cli_outputs_169_keys(capsys):
    rc = main(["push_fold", "--stack", "10", "--iters", "500"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert len(out["sb_jam"]) == 169
    assert all(0.0 <= v <= 1.0 for v in out["sb_jam"].values())
