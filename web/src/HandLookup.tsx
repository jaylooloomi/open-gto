import {
  RANKS,
  SUITS,
  classFromCards,
  representativeCards,
  type Chart,
} from "./hands";
import { verdict, type View } from "./verdict";

interface Props {
  view: View;
  chart: Chart;
  selected: string; // current 169-class label
  onSelect: (label: string) => void;
}

const RED_SUITS = new Set(["h", "d"]);

/** Beginner hero: pick your two cards, get a plain-language recommendation. */
export function HandLookup({ view, chart, selected, onSelect }: Props) {
  const cards = representativeCards(selected);
  const sameCard =
    cards.rank1 === cards.rank2 && cards.suit1 === cards.suit2;

  function update(part: Partial<typeof cards>) {
    const next = { ...cards, ...part };
    onSelect(classFromCards(next.rank1, next.suit1, next.rank2, next.suit2));
  }

  const freq = chart[selected] ?? 0;
  const v = verdict(view, freq);
  const tone =
    v.kind === "do"
      ? { bg: "#e4564a", fg: "#fff" }
      : v.kind === "fold"
        ? { bg: "#33414f", fg: "#fff" }
        : { bg: "#c98a2b", fg: "#fff" };

  return (
    <div data-tour="lookup" className="lookup">
      <div className="lookup-head">查你的手牌</div>
      <div className="pickers">
        <CardPicker
          card={{ rank: cards.rank1, suit: cards.suit1 }}
          onRank={(r) => update({ rank1: r })}
          onSuit={(s) => update({ suit1: s })}
        />
        <CardPicker
          card={{ rank: cards.rank2, suit: cards.suit2 }}
          onRank={(r) => update({ rank2: r })}
          onSuit={(s) => update({ suit2: s })}
        />
        <span className="as-class">= {selected}</span>
      </div>

      {sameCard ? (
        <p className="warn">請選兩張不同的牌。</p>
      ) : (
        <div className="verdict" style={{ background: tone.bg, color: tone.fg }}>
          <div className="verdict-head">{v.headline}</div>
          <div className="verdict-detail">{v.detail}</div>
        </div>
      )}
    </div>
  );
}

function CardPicker({
  card,
  onRank,
  onSuit,
}: {
  card: { rank: string; suit: string };
  onRank: (r: string) => void;
  onSuit: (s: string) => void;
}) {
  return (
    <div className="card-picker">
      <select
        aria-label="點數"
        value={card.rank}
        onChange={(e) => onRank(e.target.value)}
      >
        {RANKS.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>
      <div className="suits">
        {SUITS.map((s) => (
          <button
            key={s.key}
            type="button"
            aria-label={s.name}
            className={card.suit === s.key ? "suit active" : "suit"}
            style={{ color: RED_SUITS.has(s.key) ? "#e4564a" : "#dfe7ee" }}
            onClick={() => onSuit(s.key)}
          >
            {s.symbol}
          </button>
        ))}
      </div>
    </div>
  );
}
