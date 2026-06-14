import { ACTION_ZH, POSITION_ZH, type PreflopResult } from "./preflop";

interface Props {
  result: PreflopResult;
  path: string; // current node path ("" = root)
  onNavigate: (path: string) => void;
}

function segments(path: string): string[] {
  return path ? path.split("/") : [];
}

/** Action-tree navigation: breadcrumb of the line so far + the current node's
 * available actions as chips to walk deeper. */
export function PositionTree({ result, path, onNavigate }: Props) {
  const node = result.nodes[path];
  const steps = segments(path);

  return (
    <div data-tour="tree" className="postree">
      <div className="breadcrumb">
        <button className="crumb" onClick={() => onNavigate("")}>開局</button>
        {steps.map((action, i) => {
          const upto = steps.slice(0, i + 1).join("/");
          return (
            <span key={upto}>
              <span className="sep">›</span>
              <button className="crumb" onClick={() => onNavigate(upto)}>
                {ACTION_ZH[action] ?? action}
              </button>
            </span>
          );
        })}
      </div>

      {node && !node.is_terminal && (
        <div className="turn">
          輪到:<b>{POSITION_ZH[node.player ?? 0]}</b> · 點動作可往下看對手怎麼回應
          <div className="next-actions">
            {node.actions.map((a) => (
              <button
                key={a}
                className="navact"
                onClick={() => onNavigate(node.children[a])}
              >
                {ACTION_ZH[a] ?? a} <span aria-hidden="true">↘</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
