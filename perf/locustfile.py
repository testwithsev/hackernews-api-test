from locust import HttpUser, task, between
import os
import random
import json


class HNUser(HttpUser):
    host = os.getenv("HACKERNEWS_BASE_URL", "https://hacker-news.firebaseio.com/v0")
    wait_time = between(0.2, 0.8)

    @task(3)
    def topstories(self):
        self.client.get("/topstories.json", name="/topstories.json")

    @task(1)
    def item(self):
        resp = self.client.get("/topstories.json", name="/topstories.json (seed)")
        if not resp.ok:
            return
        try:
            ids = resp.json()
        except (ValueError, json.JSONDecodeError):
            return

        if isinstance(ids, list) and ids:
            sid = random.choice(ids[:100])
            self.client.get(f"/item/{sid}.json", name="/item/{id}.json")
