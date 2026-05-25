export function VerdictPill({ verdict }: { verdict: "PASS" | "FAIL" }) {
  if (verdict === "PASS") {
    return (
      <span className="badge-pass" data-testid={`verdict-${verdict.toLowerCase()}`}>
        <span className="h-1.5 w-1.5 rounded-full bg-forge-green" /> PASS
      </span>
    );
  }
  return (
    <span className="badge-fail" data-testid={`verdict-${verdict.toLowerCase()}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-forge-red" /> FAIL
    </span>
  );
}
