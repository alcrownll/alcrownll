"""
Fetches all repos owned by GITHUB_USER (including private ones, using
PROFILE_PAT), counts how many have each "portfolio-*" topic, builds a
row of shields.io badges (skipping any category with 0 repos), and
writes that row into README.md between the marker comments:

  <!-- PROJECT-BADGES:START -->
  ...badges go here...
  <!-- PROJECT-BADGES:END -->

To add a new project category later, just add a new entry to
CATEGORIES below and start tagging repos with its topic.
"""

import os
import re
import requests

GITHUB_USER = os.environ["GITHUB_USER"]
TOKEN = os.environ["PROFILE_PAT"]
README_PATH = "README.md"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}

# topic -> (badge label as it appears, color, logo)
CATEGORIES = [
    ("portfolio-webapp",     "Web_Apps",        "3B82F6", "react"),
    ("portfolio-ai-rag",     "AI%2FRAG_Systems", "8B5CF6", "openai"),
    ("portfolio-automation", "Automations",      "6D28D9", "n8n"),
    ("portfolio-desktop",    "Desktop_Apps",     "A78BFA", "windows"),
    ("portfolio-mobile",     "Mobile_Apps",      "7C3AED", "android"),
    ("portfolio-games",      "Games",            "5B21B6", "unity"),
]

START_MARKER = "<!-- PROJECT-BADGES:START -->"
END_MARKER = "<!-- PROJECT-BADGES:END -->"


def fetch_all_repos():
    repos = []
    page = 1
    while True:
        resp = requests.get(
            "https://api.github.com/user/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "affiliation": "owner"},
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def fetch_topics(full_name):
    resp = requests.get(
        f"https://api.github.com/repos/{full_name}/topics",
        headers=HEADERS,
    )
    resp.raise_for_status()
    return resp.json().get("names", [])


def count_by_category(repos):
    counts = {topic: 0 for topic, *_ in CATEGORIES}
    for repo in repos:
        topics = fetch_topics(repo["full_name"])
        for topic in counts:
            if topic in topics:
                counts[topic] += 1
    return counts


def build_badge_row(counts):
    badges = []
    for topic, label, color, logo in CATEGORIES:
        count = counts[topic]
        if count < 1:
            continue  # skip categories with no tagged repos yet
        badge_url = (
            f"https://img.shields.io/badge/{label}-{count}-{color}"
            f"?style=for-the-badge&logo={logo}&logoColor=white"
        )
        # Links to a GitHub search filtered to this user's repos
        # carrying this exact topic.
        search_url = (
            f"https://github.com/search?q=user%3A{GITHUB_USER}"
            f"+topic%3A{topic}&type=repositories"
        )
        badges.append(
            f'<a href="{search_url}"><img src="{badge_url}"/></a>'
        )

    if not badges:
        return ""  # nothing tagged yet at all

    return '<div align="center">\n' + "\n".join(badges) + "\n</div>"


def update_readme(badge_block):
    with open(README_PATH, "r") as f:
        content = f.read()

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )
    replacement = f"{START_MARKER}\n{badge_block}\n{END_MARKER}"

    if not pattern.search(content):
        raise RuntimeError(
            "Could not find PROJECT-BADGES markers in README.md. "
            "Make sure both marker comments exist."
        )

    new_content = pattern.sub(replacement, content)

    with open(README_PATH, "w") as f:
        f.write(new_content)


def main():
    repos = fetch_all_repos()
    counts = count_by_category(repos)
    for topic, count in counts.items():
        print(f"{topic}: {count}")

    badge_block = build_badge_row(counts)
    update_readme(badge_block)


if __name__ == "__main__":
    main()
