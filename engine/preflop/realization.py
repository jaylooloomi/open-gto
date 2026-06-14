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

# Shared defaults so the generic and vectorized solvers model terminals
# identically (keeps the cross-validation valid).
DEFAULT_REALIZATION = 1.0
DEFAULT_IP_PREMIUM = 0.0  # tunable; a uniform premium just inflates pot-entry, so off


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
    eq: float,
    contrib: tuple[float, float],
    realization: float = 1.0,
    ip_premium: float = 0.0,
) -> tuple[float, float]:
    """See-flop EV with an equity-realization scale and an IP positional premium.

    In HU the SB (button) is in position postflop. ``ip_premium`` grants the SB a
    small zero-sum edge proportional to the pot, so building bigger pots is more
    attractive to the IP player (curbs degenerate limping; BB defends tighter).
    Still a heuristic for the missing postflop EV; documented as such.
    """
    stake = contrib[0]  # equal for both players at a see-flop node
    net_sb = (2.0 * eq - 1.0) * realization * stake + ip_premium * stake
    return (net_sb, -net_sb)
