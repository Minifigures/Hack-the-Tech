export const fmtMs = (ms: number) =>
  ms < 1000 ? `${ms.toFixed(0)} ms` : `${(ms / 1000).toFixed(2)} s`;

export const fmtUsd = (n: number) => {
  if (n === 0) return "$0";
  if (n < 0.001) return `$${(n * 1000).toFixed(2)}m`;
  return `$${n.toFixed(4)}`;
};

export const fmtPct = (n: number, digits = 1) => `${(n * 100).toFixed(digits)}%`;

export const fmtScore = (n: number) => n.toFixed(3);

export const titleizeMetric = (name: string) =>
  name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
