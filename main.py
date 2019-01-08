#!/usr/bin/python3

import requests
import json
import click
import subprocess
from time import sleep

SECRET_STRINGS = ["api_key", "password"]


def get_repositories(company_name, results_count=500):
    repo_urls = []
    for i in range(results_count // 100):
        r = requests.get(
            "https://api.github.com/search/repositories",
            params={
                "q": "{}".format(company_name),
                "sort": "stars",
                "page": i,
                "per_page": 100,
            },
        )

        if not r.json()["items"]:
            break

        if i >= 9:  # rate-limit protection
            sleep(6)

        for repo in r.json()["items"]:
            repo_urls.append(repo["git_url"])

    return repo_urls


def get_repositories_on_code(company_name, search_term, results_count=1000):
    repo_urls = []
    for i in range(results_count // 100):
        r = requests.get(
            "https://api.github.com/search/code",
            params={
                "q": "{} {}".format(company_name, search_term),
                "sort": "stars",
                "page": i,
                "per_page": 100,
            },
        )

        if not r.json()["items"]:
            break

        sleep(6)

        for repo in r.json()["items"]:
            repo_urls.append(repo["repository"]["git_url"])

    return repo_urls


def trufflehog(repo_url):
    issues = []
    p = subprocess.run(["trufflehog", "--json", repo_url], stdout=subprocess.PIPE)

    for line in p.stdout.decode().split("\n"):
        print(line)
        if not line:
            continue
        
        issue = json.loads(line)

        if issue["reason"] == "High Entropy" and all(
            len(string_found) > 42 for string_found in issue["stringsFound"]
        ):
            continue

        issues.append(issue)

    return issues


@click.command()
@click.option("--company", help="Company name to search for.")
def gib_all_secrets(company):
    repos = set()
    repos.update(get_repositories(company))
    # for search_term in SECRET_STRINGS:
    #     get_repositories_on_code(company, search_term)

    for repo in repos:
        click.echo(trufflehog(repo))


if __name__ == "__main__":
    gib_all_secrets()
