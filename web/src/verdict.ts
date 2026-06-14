// Turns a raw action frequency into a plain-language recommendation for a
// beginner. View "sb_jam" = the small blind's jam-or-fold decision; "bb_call"
// = the big blind's call-or-fold decision facing a jam.

export type View = "sb_jam" | "bb_call";

export interface Verdict {
  kind: "do" | "fold" | "mix";
  action: string; // the aggressive action label for this view
  headline: string; // big plain-language recommendation
  detail: string; // one-line explanation
  pct: number; // rounded % for the aggressive action
}

const ACTION: Record<View, string> = {
  sb_jam: "全下推注 (Jam)",
  bb_call: "跟注 (Call)",
};

export function verdict(view: View, freq: number): Verdict {
  const action = ACTION[view];
  const pct = Math.round(freq * 100);

  if (freq >= 0.995) {
    return {
      kind: "do",
      action,
      pct,
      headline: `GTO 建議:${action}`,
      detail:
        view === "sb_jam"
          ? "這手牌夠強,每次都該全下,不要蓋掉。"
          : "對手全下時,這手牌每次都該跟注。",
    };
  }
  if (freq <= 0.005) {
    return {
      kind: "fold",
      action,
      pct,
      headline: "GTO 建議:蓋牌 (Fold)",
      detail:
        view === "sb_jam"
          ? "這手牌不夠強,直接蓋牌最划算。"
          : "面對全下,這手牌跟注會虧,蓋牌即可。",
    };
  }
  return {
    kind: "mix",
    action,
    pct,
    headline: `混合策略:${action} ${pct}%`,
    detail: `GTO 在這手牌會混著打:約 ${pct}% ${action}、${100 - pct}% 蓋牌。新手可先固定選頻率較高的那個。`,
  };
}
