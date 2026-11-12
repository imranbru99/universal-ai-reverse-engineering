from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

from app.security.url_guard import UrlGuardError, assert_in_scope
from workers.exploration.fingerprint import canonicalize_url, state_fingerprint


@dataclass
class ExploreResult:
    states: list[dict[str, Any]] = field(default_factory=list)
    transitions: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[dict[str, Any]] = field(default_factory=list)
    screenshots: dict[str, bytes] = field(default_factory=dict)


def explore_site(
    start_url: str,
    *,
    allowlist_domains: list[str],
    path_prefixes: list[str],
    max_depth: int = 4,
    max_pages: int = 30,
    max_minutes: int = 8,
    kill_check=None,
) -> ExploreResult:
    result = ExploreResult()
    visited: set[str] = set()
    queue: deque[tuple[str, int, str | None, str]] = deque()
    queue.append((start_url, 0, None, "seed"))
    started = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        while queue and len(visited) < max_pages:
            if kill_check and kill_check():
                result.skipped.append({"url": "", "reason": "kill_switch"})
                break
            if (time.time() - started) / 60.0 >= max_minutes:
                result.skipped.append({"url": "", "reason": "budget_time"})
                break

            url, depth, from_fp, trigger = queue.popleft()
            try:
                assert_in_scope(
                    url,
                    allowlist_domains=allowlist_domains,
                    path_prefixes=path_prefixes,
                    allow_trusted_internal=True,
                )
            except UrlGuardError as exc:
                result.skipped.append({"url": url, "reason": "out_of_scope", "detail": str(exc)})
                result.transitions.append(
                    {
                        "from_fingerprint": from_fp,
                        "to_fingerprint": None,
                        "trigger": trigger,
                        "skipped_reason": "out_of_scope",
                        "inputs": {"url": url},
                    }
                )
                continue

            if depth > max_depth:
                result.skipped.append({"url": url, "reason": "budget_depth"})
                continue

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(300)
            except Exception as exc:  # noqa: BLE001
                result.skipped.append({"url": url, "reason": "navigation_error", "detail": str(exc)})
                continue

            final_url = canonicalize_url(page.url)
            landmarks = page.evaluate(
                """() => {
                  const texts = [];
                  document.querySelectorAll('h1,h2,nav a,button,[data-testid]').forEach(el => {
                    const t = (el.innerText || el.getAttribute('data-testid') || '').trim();
                    if (t) texts.push(t.slice(0, 80));
                  });
                  return texts.slice(0, 30);
                }"""
            )
            fp = state_fingerprint(final_url, "anonymous", "desktop", landmarks)
            if fp in visited:
                if from_fp:
                    result.transitions.append(
                        {
                            "from_fingerprint": from_fp,
                            "to_fingerprint": fp,
                            "trigger": trigger,
                            "skipped_reason": "",
                            "inputs": {},
                        }
                    )
                continue
            visited.add(fp)

            components = page.evaluate(
                """() => {
                  const items = [];
                  document.querySelectorAll('a,button,input,select,textarea,[role="button"]').forEach(el => {
                    items.push({
                      type: el.tagName.toLowerCase(),
                      name: (el.getAttribute('name') || el.getAttribute('aria-label') || el.innerText || '').trim().slice(0, 120),
                      href: el.getAttribute('href') || '',
                      inputType: el.getAttribute('type') || '',
                      testId: el.getAttribute('data-testid') || ''
                    });
                  });
                  return items.slice(0, 100);
                }"""
            )
            title = page.title()
            screenshot = page.screenshot(full_page=False)
            result.screenshots[fp] = screenshot
            result.states.append(
                {
                    "fingerprint": fp,
                    "url": final_url,
                    "title": title,
                    "auth_state": "anonymous",
                    "role": "public",
                    "viewport": "desktop",
                    "components": components,
                    "messages": [],
                    "confidence": 0.9,
                    "completeness": "partial",
                    "accessibility_snapshot": {"landmarks": landmarks},
                }
            )
            if from_fp:
                result.transitions.append(
                    {
                        "from_fingerprint": from_fp,
                        "to_fingerprint": fp,
                        "trigger": trigger,
                        "skipped_reason": "",
                        "inputs": {},
                    }
                )

            # Enqueue same-origin in-scope links
            hrefs = page.eval_on_selector_all(
                "a[href]",
                "els => els.map(a => a.href).filter(Boolean)",
            )
            for href in hrefs:
                abs_url = urljoin(final_url, href)
                if urlparse(abs_url).scheme not in {"http", "https"}:
                    continue
                try:
                    assert_in_scope(
                        abs_url,
                        allowlist_domains=allowlist_domains,
                        path_prefixes=path_prefixes,
                        allow_trusted_internal=True,
                    )
                except UrlGuardError:
                    result.skipped.append({"url": abs_url, "reason": "out_of_scope"})
                    continue
                cand_fp = state_fingerprint(canonicalize_url(abs_url), "anonymous", "desktop", [])
                if cand_fp in visited:
                    continue
                queue.append((abs_url, depth + 1, fp, f"click_link:{canonicalize_url(abs_url)}"))

        browser.close()
    return result
