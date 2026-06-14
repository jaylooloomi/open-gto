"""Terminal valuation for the preflop tree (SB-perspective net, in bb).

Each function returns ``(net_sb, net_bb)`` with ``net_bb == -net_sb`` (zero-sum).

- ``fold_value``: the folder loses what it committed; the other player wins it.
- ``showdown_value``: an all-in was called; both committed ``stake``; the SB wins
  ``stake`` with probability ``eq`` and loses it otherwise -> EV ``(2*eq-1)*stake``.
- ``seeflop_value``: betting closed without all-in. With no postflop model we use
  an **equity-realization** approximation: realized edge = raw edge scaled by
  ``realization`` (R=1 -> raw equity; R<1 shrinks the edge toward a coin flip).
  Contributions are equal at a see-flop node, so EV = (2*eq-1)*R*contrib.
"""
from __future__ import annotations


def fold_value(folder: int, contrib: tuple[float, float]) -> tuple[float, float]:
    if folder == 0:  # SB folded -> SB loses its own contribution
        net_sb = -contrib[0]
    else:  # BB folded -> SB wins BB's contribution
        net_sb = contrib[1]
    return (net_sb, -net_sb)


def showdown_value(eq: float, stake: float) -> tuple[float, float]:
    net_sb = (2.0 * eq - 1.0) * stake
    return (net_sb, -net_sb)


def seeflop_value(
    eq: float, contrib: tuple[float, float], realization: float = 1.0
) -> tuple[float, float]:
    stake = contrib[0]  # equal for both players at a see-flop node
    net_sb = (2.0 * eq - 1.0) * realization * stake
    return (net_sb, -net_sb)
