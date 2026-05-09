"""GitHub search — find repositories relevant to corpus gaps."""

from __future__ import annotations

import os

import httpx

GITHUB_API = "https://api.github.com"
DEFAULT_MAX_RESULTS = 20


class GitHubSearcher:
    """Search GitHub for repositories matching gap-derived queries."""

    def __init__(self, token: str | None = None):
        self._token = token or os.environ.get("GITHUB_TOKEN", "")
        self._headers = {"Accept": "application/vnd.github+json"}
        if self._token:
            self._headers["Authorization"] = f"Bearer {self._token}"

    def search_repos(
        self,
        queries: list[str],
        languages: list[str] | None = None,
        min_stars: int = 0,
        max_results: int = DEFAULT_MAX_RESULTS,
    ) -> list[dict]:
        """Search GitHub repos using multiple queries, deduplicate results."""
        seen = set()
        results = []

        for query in queries:
            q = query
            if languages:
                lang_filter = " ".join(f"language:{lang}" for lang in languages)
                q = f"{query} {lang_filter}"
            if min_stars > 0:
                q += f" stars:>={min_stars}"

            try:
                resp = httpx.get(
                    f"{GITHUB_API}/search/repositories",
                    params={"q": q, "sort": "stars", "per_page": min(max_results, 30)},
                    headers=self._headers,
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()

                for item in data.get("items", []):
                    full_name = item["full_name"]
                    if full_name in seen:
                        continue
                    seen.add(full_name)

                    results.append({
                        "github_url": item["html_url"],
                        "full_name": full_name,
                        "owner": item["owner"]["login"],
                        "repo_name": item["name"],
                        "description": item.get("description") or "",
                        "primary_language": item.get("language") or "",
                        "stars": item.get("stargazers_count", 0),
                        "last_updated": item.get("updated_at", ""),
                        "license": (item.get("license") or {}).get("spdx_id", ""),
                        "clone_url": item["clone_url"],
                        "topics": item.get("topics", []),
                        "has_wiki": item.get("has_wiki", False),
                    })

                    if len(results) >= max_results:
                        return results

            except httpx.HTTPError:
                continue

        return results
