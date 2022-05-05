# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime
from string import Template

import httpx

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
}


tpl = Template(
    """# Awesome Stars

![Total](https://img.shields.io/badge/Total-$total-green) ![Updated](https://img.shields.io/badge/Updated-$updated-blue)

## Table of Contents

$toc
$contents
"""
)


def get_all_stars():
    """
    Get all stars from GitHub API
    """
    # https://docs.github.com/cn/rest/activity/starring
    # url = "https://api.github.com/user/starred"
    url = f"https://api.github.com/users/{os.getenv('USERNAME')}/starred"
    params = {"per_page": 100}

    res = httpx.get(url, params=params, headers=HEADERS)
    print(f"Total pages: {res.links['last']['url']}\n", file=sys.stderr)

    stars = []
    while "next" in res.links.keys():
        url = res.links["next"]["url"]
        print(
            f"> Getting: {url}, X-RateLimit-Used: {res.headers['X-RateLimit-Used']}",
            file=sys.stderr,
        )
        res = httpx.get(url, params=params, headers=HEADERS)
        stars.extend(res.json())

    return stars


def get_repos_by_language(stars):
    """
    Group repos by language
    """
    repos_by_language = {}
    for s in stars:
        language = s["language"] or "Others"
        description = s["description"]
        description = description.replace("\n", "").strip() if description else ""

        if language not in repos_by_language:
            repos_by_language[language] = []

        repos_by_language[language].append(
            [
                s["full_name"],
                s["html_url"],
                s["stargazers_count"],
                description,
            ]
        )

    repos_by_language = dict(
        sorted(repos_by_language.items(), key=lambda item: item[0])
    )
    return repos_by_language


def make_md(repos_by_language):
    """
    Make markdown
    """
    toc = ""
    for language in repos_by_language.keys():
        toc += f"- [{language}](#{'-'.join(language.lower().split())})\n"

    contents = ""
    for language, repos in repos_by_language.items():
        contents += f"## {language}\n\n"
        for repo in repos:
            contents += "- [{}]({}) - `★{}` {}\n".format(*repo)
        contents += "\n"

    md = tpl.substitute(
        total=len(stars),
        updated=datetime.now().strftime("%Y--%m--%d"),
        toc=toc,
        contents=contents,
    ).strip()

    return md


if __name__ == "__main__":
    stars = get_all_stars()
    repos_by_language = get_repos_by_language(stars)
    md = make_md(repos_by_language)
    print(md)
