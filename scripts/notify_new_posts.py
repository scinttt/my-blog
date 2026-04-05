#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


DEFAULT_FEED_URL = "https://www.creaturelove7.com/index.xml"
DEFAULT_POLL_ATTEMPTS = 30
DEFAULT_POLL_INTERVAL_SECONDS = 20


def parse_front_matter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("+++\n"):
        raise ValueError(f"{path} is missing TOML front matter")

    _, remainder = text.split("+++\n", 1)
    front_matter, _separator, _body = remainder.partition("\n+++")
    if not _separator:
        raise ValueError(f"{path} has an unclosed TOML front matter block")

    return tomllib.loads(front_matter)


def list_candidate_posts(paths: list[str]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []

    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            continue
        if path.suffix != ".md" or not path.name.endswith(".en.md"):
            continue
        if path.name in {"search.en.md", "_index.en.md"}:
            continue

        front_matter = parse_front_matter(path)
        if bool(front_matter.get("draft", False)):
            continue

        title = str(front_matter.get("title", "")).strip()
        if not title:
            raise ValueError(f"{path} is missing title in front matter")

        candidates.append({"path": raw_path, "title": title})

    return candidates


def fetch_feed(feed_url: str) -> str:
    request = urllib.request.Request(
        feed_url,
        headers={"Accept": "application/rss+xml, application/xml, text/xml"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")


def parse_feed_links(feed_xml: str) -> dict[str, str]:
    root = ET.fromstring(feed_xml)
    links_by_title: dict[str, str] = {}

    for item in root.findall("./channel/item"):
        title = item.findtext("title", default="").strip()
        link = item.findtext("link", default="").strip()
        if title and link:
            links_by_title[title] = link

    return links_by_title


def resolve_post_links(candidates: list[dict[str, str]], feed_url: str) -> dict[str, str]:
    poll_attempts = int(os.environ.get("NOTIFY_POLL_ATTEMPTS", DEFAULT_POLL_ATTEMPTS))
    poll_interval = int(
        os.environ.get("NOTIFY_POLL_INTERVAL_SECONDS", DEFAULT_POLL_INTERVAL_SECONDS)
    )
    missing_titles = {candidate["title"] for candidate in candidates}

    for attempt in range(1, poll_attempts + 1):
        links_by_title = parse_feed_links(fetch_feed(feed_url))
        resolved = {
            candidate["path"]: links_by_title[candidate["title"]]
            for candidate in candidates
            if candidate["title"] in links_by_title
        }
        missing_titles = {
            candidate["title"]
            for candidate in candidates
            if candidate["path"] not in resolved
        }
        if not missing_titles:
            return resolved

        if attempt < poll_attempts:
            print(
                f"Feed not ready yet. Attempt {attempt}/{poll_attempts}. "
                f"Waiting for: {', '.join(sorted(missing_titles))}",
                file=sys.stderr,
            )
            time.sleep(poll_interval)

    raise RuntimeError(
        "Timed out waiting for posts to appear in feed: "
        + ", ".join(sorted(missing_titles))
    )


def send_post(send_api_url: str, token: str, post_url: str) -> dict[str, object]:
    payload = json.dumps({"postUrl": post_url}).encode("utf-8")
    request = urllib.request.Request(
        send_api_url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Send API request failed for {post_url}: {error.code} {body}"
        ) from error

    try:
        return json.loads(body)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Send API returned invalid JSON for {post_url}: {body}") from error


def main() -> int:
    candidates = list_candidate_posts(sys.argv[1:])
    if not candidates:
        print("No eligible English posts changed. Exiting.")
        return 0

    feed_url = os.environ.get("BLOG_FEED_URL") or DEFAULT_FEED_URL
    send_api_url = os.environ.get("EMAIL_SEND_API_URL", "").strip()
    dry_run = os.environ.get("DRY_RUN") == "1"
    token = os.environ.get("EMAIL_SEND_API_TOKEN", "")

    resolved = resolve_post_links(candidates, feed_url)

    print("Resolved post URLs:")
    for path, post_url in resolved.items():
        print(f"- {path} -> {post_url}")

    if dry_run:
        print("Dry run enabled. Skipping send API calls.")
        return 0

    if not send_api_url:
        raise RuntimeError("EMAIL_SEND_API_URL is required unless DRY_RUN=1")

    if not token:
        raise RuntimeError("EMAIL_SEND_API_TOKEN is required unless DRY_RUN=1")

    for path, post_url in resolved.items():
        result = send_post(send_api_url, token, post_url)
        print(f"Triggered send for {path}: {json.dumps(result, ensure_ascii=True)}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:  # pragma: no cover
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
