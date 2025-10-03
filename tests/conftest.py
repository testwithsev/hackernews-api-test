import pytest
from hackernews.client import HackerNewsClient


@pytest.fixture(scope="session")
def client():
    return HackerNewsClient()
