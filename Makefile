.PHONY: install test perf-smoke perf-ui

install:
\tpython -m pip install --upgrade pip
\tpip install -r requirements.txt

test:
\tpytest -q --alluredir=allure-results --html=pytest_report.html --self-contained-html

perf-smoke:
\tlocust -f perf/locustfile.py --headless -u 10 -r 5 -t 20s --csv=perf/stats --html perf/report.html
\tpython perf/check_thresholds.py perf/stats_stats.csv

perf-ui:
\tlocust -f perf/locustfile.py
