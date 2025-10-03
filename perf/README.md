# Performance (Locust)

## Quick commands

Headless smoke (~20s, 10 users):
```bash
locust -f perf/locustfile.py --headless -u 10 -r 5 -t 20s --csv=perf/stats --html perf/report.html
python perf/check_thresholds.py perf/stats_stats.csv
```

UI mode:
```bash
locust -f perf/locustfile.py
# open http://localhost:8089
```

Distributed example:
```bash
# master
locust -f perf/locustfile.py --master
# worker(s)
locust -f perf/locustfile.py --worker --master-host=127.0.0.1
```

### Thresholds
CI will fail if aggregated p95 > **800ms** or failure rate > **5%**.
Artifacts uploaded: Locust HTML (`perf/report.html`) and CSV (`perf/stats_stats.csv`).
