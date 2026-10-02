"""Fixtures shared across test modules.

Only one Playwright instance may exist per process - a second
`sync_playwright()` in the same session fails with "Sync API inside the asyncio
loop". The browser fixtures and the API request context both need one, so it
lives here where both can reach it. It was previously defined inside
test_script_main.py, where a second module could not reuse it.
"""

import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as playwright:
        yield playwright
