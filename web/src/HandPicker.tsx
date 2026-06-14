import {
  RANKS,
  SUITS,
  classFromCards,
  representativeCards,
} from "./hands";

interface Props {
  selected: string; // current 169-class label
  onSelect: (label: string) => void;
}

const RED_SUITS = new Set(["h", "d"]);

/** Two card slots (rank + suit) that resolve to a 169-class label. */
export function HandPicker({ selected, onSelect }: Props) {
  const cards = representativeCards(selected);

  function update(part: Partial<typeof cards>) {
    const next = { ...cards, ...part };
    onSelect(classFromCards(next.rank1, next.suit1, next.rank2, next.suit2));
  }

  return (
    <div className="pickers">
      <Slot
        rank={cards.rank1}
        suit={cards.suit1}
        onRank={(r) => update({ rank1: r })}
        onSuit={(s) => update({ suit1: s })}
      />
      <Slot
        rank={cards.rank2}
        suit={cards.suit2}
        onRank={(r) => update({ rank2: r })}
        onSuit={(s) => update({ suit2: s })}
      />
      <span className="as-class">= {selected}</span>
    </div>
  );
}

function Slot({
  rank,
  suit,
  onRank,
  onSuit,
}: {
  rank: string;
  suit: string;
  onRank: (r: string) => void;
  onSuit: (s: string) => void;
}) {
  return (
    <div className="card-picker">
      <select aria-label="點數" value={rank} onChange={(e) => onRank(e.target.value)}>
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
            className={suit === s.key ? "suit active" : "suit"}
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
