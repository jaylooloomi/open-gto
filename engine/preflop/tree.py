"""Public betting tree for heads-up NLHE preflop.

Nodes are *public* states (whose turn, chips committed, action history) — they do
NOT depend on the private hands. The solver layers per-hand range vectors on top.

Blinds: SB (button) posts 0.5, BB posts 1.0; effective stack ``S`` bb. SB acts
first. Action abstraction (single open size; multi-size deferred to post-postflop):

  SB (facing the blind):  fold | limp | raise(open) | allin
  BB vs limp:             check | raise(iso) | allin
  facing a bet:           fold | call | <sized re-raise> | allin
  facing an all-in:       fold | call

Terminal kinds:
  fold     — a player folded; ``folder`` set.
  showdown — an all-in was called (both committed the full stake).
  seeflop  — betting closed without all-in (check-behind or a non-allin call).

Re-raise sizing: 3bet = facing level x threebet_mult, 4bet = x fourbet_mult,
then all-in only (raise_cap total raises). A sized raise that reaches the stack
is replaced by all-in.
"""
from __future__ import annotations

from dataclasses import dataclass, field

SB, BB = 0, 1
_EPS = 1e-9


@dataclass
class Sizes:
    open_to: float = 2.5
    iso_to: float = 3.5
    threebet_mult: float = 3.0
    fourbet_mult: float = 2.2
    raise_cap: int = 4


@dataclass
class Node:
    player: int | None  # acting player (0=SB, 1=BB), or None if terminal
    contrib: tuple[float, float]  # chips committed (sb, bb)
    actions: list[str] = field(default_factory=list)
    children: dict[str, "Node"] = field(default_factory=dict)
    is_terminal: bool = False
    kind: str | None = None  # "fold" | "showdown" | "seeflop"
    folder: int | None = None

    def child(self, action: str) -> "Node":
        return self.children[action]

    def node_at(self, path: list[str]) -> "Node":
        node = self
        for action in path:
            node = node.children[action]
        return node

    def decision_nodes(self) -> list["Node"]:
        out: list[Node] = []

        def walk(n: "Node") -> None:
            if not n.is_terminal:
                out.append(n)
                for c in n.children.values():
                    walk(c)

        walk(self)
        return out


_RAISE_NAME = {1: "3bet", 2: "4bet", 3: "5bet"}


def _sized_raise_to(level: float, num_raises: int, sizes: Sizes) -> float:
    mult = sizes.threebet_mult if num_raises == 1 else sizes.fourbet_mult
    return level * mult


def build_tree(stack_bb: float, sizes: Sizes | None = None) -> Node:
    s = sizes or Sizes()
    S = float(stack_bb)

    def fold_node(contrib, folder):
        return Node(None, (contrib[0], contrib[1]), is_terminal=True, kind="fold", folder=folder)

    def end(contrib, kind):
        return Node(None, (contrib[0], contrib[1]), is_terminal=True, kind=kind)

    def build(contrib, to_act, num_raises):
        contrib = [float(contrib[0]), float(contrib[1])]
        opp = 1 - to_act
        level = max(contrib)
        facing_bet = contrib[to_act] < level - _EPS
        opp_allin = contrib[opp] >= S - _EPS
        node = Node(player=to_act, contrib=(contrib[0], contrib[1]))

        if facing_bet:
            node.actions.append("fold")
            node.children["fold"] = fold_node(contrib, to_act)

            called = list(contrib)
            called[to_act] = level
            node.actions.append("call")
            node.children["call"] = end(called, "showdown" if level >= S - _EPS else "seeflop")

            if not opp_allin and num_raises < s.raise_cap - 1:
                target = _sized_raise_to(level, num_raises, s)
                if target < S - _EPS:
                    rc = list(contrib)
                    rc[to_act] = target
                    name = _RAISE_NAME.get(num_raises, "raise")
                    node.actions.append(name)
                    node.children[name] = build(rc, opp, num_raises + 1)

            if not opp_allin:
                ac = list(contrib)
                ac[to_act] = S
                node.actions.append("allin")
                node.children["allin"] = build(ac, opp, num_raises + 1)
        else:
            # No outstanding bet: BB checking behind a limp.
            node.actions.append("check")
            node.children["check"] = end(contrib, "seeflop")
            if num_raises < s.raise_cap - 1 and s.iso_to < S - _EPS:
                rc = list(contrib)
                rc[to_act] = s.iso_to
                node.actions.append("raise")
                node.children["raise"] = build(rc, opp, num_raises + 1)
            ac = list(contrib)
            ac[to_act] = S
            node.actions.append("allin")
            node.children["allin"] = build(ac, opp, num_raises + 1)
        return node

    # Root: SB faces the big blind. Name SB's call "limp" and its raise "raise".
    root = Node(player=SB, contrib=(0.5, 1.0))
    root.actions.append("fold")
    root.children["fold"] = fold_node([0.5, 1.0], SB)
    root.actions.append("limp")
    root.children["limp"] = build([1.0, 1.0], BB, 0)
    root.actions.append("raise")
    root.children["raise"] = build([s.open_to, 1.0], BB, 1)
    root.actions.append("allin")
    root.children["allin"] = build([S, 1.0], BB, 1)
    return root
