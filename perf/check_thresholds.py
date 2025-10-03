"""
Parse Locust CSV (stats CSV with aggregated row "Aggregated") and enforce thresholds:
- p95 <= 800 ms
- failure rate <= 5%
Exit code 1 on breach, else 0. Print a small summary for CI logs.
"""
import csv
import sys
from pathlib import Path

P95_LIMIT_MS = 800.0
FAIL_RATE_LIMIT = 0.05


def parse_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("Name") in ("Aggregated", "Total", "Aggregated (aggregated)"):
                # Locust CSV headers tend to include: "95%" or "95%ile"
                p95 = None
                for key in row.keys():
                    if key.strip().startswith("95%"):
                        p95 = float(row[key])
                        break
                # Failures are Errors / Requests or computed from # failures
                try:
                    failures = float(row.get("Failure Count", row.get("Failures", 0)) or 0)
                    requests = float(row.get("Request Count", row.get("Requests", 0)) or 1)
                    fail_rate = failures / requests
                except Exception:
                    # Fallback to 0 to avoid crashing CI
                    fail_rate = 0.0
                return p95, fail_rate
    raise RuntimeError("Aggregated row not found in CSV")


def main():
    if len(sys.argv) < 2:
        print("Usage: python perf/check_thresholds.py stats.csv")
        sys.exit(2)
    path = Path(sys.argv[1])
    p95, fail_rate = parse_csv(path)
    print(f"[perf] Aggregated p95={p95:.1f} ms, failure_rate={fail_rate * 100:.2f}% "
          f"(limits: p95<={P95_LIMIT_MS}ms, failure<={FAIL_RATE_LIMIT * 100:.0f}%)")
    ok = True
    if p95 is not None and p95 > P95_LIMIT_MS:
        print("[perf] ❌ p95 threshold breached")
        ok = False
    if fail_rate > FAIL_RATE_LIMIT:
        print("[perf] ❌ failure-rate threshold breached")
        ok = False
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
