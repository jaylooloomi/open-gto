"""Compare CFR / CFR+ / DCFR convergence (on fast Kuhn poker).

Documents the research-confirmed ordering: the accelerated variants reach far
lower exploitability than vanilla CFR at the same iteration count.
"""
from engine.cfr import CFRSolver
from engine.exploitability import exploitability
from engine.games.kuhn import KuhnPoker

_ITERS = 5000


def _expl(variant):
    g = KuhnPoker()
    solver = CFRSolver(g, variant=variant)
    solver.run(_ITERS)
    return exploitability(g, solver.solution_strategy())


def test_accelerated_variants_beat_vanilla_cfr():
    cfr = _expl("cfr")
    cfr_plus = _expl("cfr_plus")
    dcfr = _expl("dcfr")
    # Both CFR+ and DCFR converge substantially faster than vanilla CFR.
    assert cfr_plus < cfr
    assert dcfr < cfr
    # DCFR is in the same fast tier as (typically better than) CFR+.
    assert dcfr < cfr_plus * 2.0
