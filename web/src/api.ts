import type { Chart } from "./hands";
import type { PreflopResult } from "./preflop";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface SolveResult {
  stack_bb: number;
  sb_jam: Chart;
  bb_call: Chart;
  exploitability: number;
}

export async function solve(
  stackBb: number,
  iterations = 1500,
): Promise<SolveResult> {
  const res = await fetch(`${API_URL}/solve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      game: "push_fold",
      params: { stack_bb: stackBb },
      iterations,
    }),
  });
  if (!res.ok) {
    throw new Error(`Solver error (${res.status})`);
  }
  return (await res.json()) as SolveResult;
}

export async function solvePreflop(
  stackBb: number,
  iterations = 1000,
): Promise<PreflopResult> {
  const res = await fetch(`${API_URL}/preflop`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ stack_bb: stackBb, iterations }),
  });
  if (!res.ok) {
    throw new Error(`Solver error (${res.status})`);
  }
  return (await res.json()) as PreflopResult;
}
