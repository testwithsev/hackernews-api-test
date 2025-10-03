FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 

COPY . .
ENV HACKERNEWS_BASE_URL=https://hacker-news.firebaseio.com/v0
CMD ["pytest", "-q", "--alluredir=allure-results", "--html=pytest_report.html", "--self-contained-html"]
