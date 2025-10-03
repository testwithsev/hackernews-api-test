# HackerNews API Test Framework

Python-only test & performance framework for the public **Hacker News (Firebase) API**.

- **Client**: thin `requests` wrapper with retry/backoff & timeouts
- **Contracts**: `jsonschema` for item types (story/comment/etc.)
- **Tests**: functional & non-functional suites; positive/negative markers
- **Performance**: Locust smoke with **p95 ≤ 800 ms** and **≤ 5%** error gate
- **CI**: GitHub Actions uploads **pytest HTML**, **Allure**, and **Locust HTML/CSV**
- **Docker/Compose**: reproducible runs; Locust UI at `http://localhost:8089`

Default base URL: `https://hacker-news.firebaseio.com/v0` (override with `HACKERNEWS_BASE_URL`).

---

## Quickstart (local)

```bash
# Python 3.11+ recommended
python -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# Run tests with reports
pytest -q \  --alluredir=allure-results \  --html=pytest_report.html --self-contained-html
```


## Markers
- `@pytest.mark.positive`
- `@pytest.mark.negative`

Useful subsets:
```bash
pytest -m positive -q
pytest -m negative -q
pytest -m "positive or negative" -q
```

## Performance

**Headless (artifacts + gate):**
```bash
locust -f perf/locustfile.py --headless -u 12 -r 6 -t 25s \  --csv=perf/stats --html perf/report.html

python perf/check_thresholds.py perf/stats_stats.csv
```
Thresholds (editable in `perf/check_thresholds.py`):
- p95 ≤ **800 ms**
- failure rate ≤ **5%**

**UI mode:**
```bash
locust -f perf/locustfile.py
# open http://localhost:8089 and start a short run
```

---

## Docker

**Build once:**
```bash
docker compose build --pull --no-cache tests
```

**Functional tests (artifacts to ./out):**
```bash
mkdir -p out
docker compose run --rm tests
# open ./out/pytest_report.html
```

**Perf headless (artifacts to ./out/perf):**
```bash
mkdir -p out/perf
docker compose run --rm locust-master -f /mnt/locust/locustfile.py --headless -u 12 -r 6 -t 25s --csv=/mnt/perf/stats --html /mnt/perf/report.html

python perf/check_thresholds.py out/perf/stats_stats.csv
# open out/perf/report.html
```

**Perf UI:**
```bash
docker compose up -d locust-master
# open http://localhost:8089
docker compose down
```


---

## CI (GitHub Actions)

On each push/PR, `.github/workflows/ci.yml` runs:
- **test**: `pytest` → uploads `pytest_report.html` + `allure-results/`
- **perf**: headless Locust (~25s) → gates p95 & failure → uploads `perf/report.html` + `perf/stats_stats.csv`


---


