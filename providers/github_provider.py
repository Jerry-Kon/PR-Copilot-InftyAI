import requests
from retry import retry
from typing import Dict

from utils.util import parse_content
from utils.envs import GITHUB_TOKEN


def convert_to_diff_url(url: str = None):
    if str is None:
        return ""
    url = url.replace("github.com", "patch-diff.githubusercontent.com/raw")
    url += ".diff"
    return url


def convert_to_pull_pr_url(url: str = None) -> str:
    if url is None:
        return ""
    url = url.replace("github.com", "api.github.com/repos")
    url = url.replace("pull", "pulls")
    return url


def convert_to_pull_commit_url(url: str = None) -> str:
    url = convert_to_pull_pr_url(url)
    url += "/commits"
    return url


def split_line_break(content: str = None) -> str:
    if content is None:
        return ""
    return content.split("\n\n")[0]


# TODO: Use github library if more convenient?
@retry(
    tries=3,
    delay=2,
    backoff=2,
    jitter=(1, 3),
)
def get_pr_info(url: str) -> Dict[str, str]:
    """
    Args:
        url: The pr link.

    Return:
        A dict contains keys as below:
            title (str):
            description (str):
            commit_messages (array[string]):
            git_diffs (str):
    """

    res = {}
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + str(GITHUB_TOKEN),
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # request to get pull request info.
    pr_resp = requests.get(
        url=convert_to_pull_pr_url(url),
        headers=headers,
    )
    if pr_resp.status_code != 200:
        raise Exception(
            "request pull-request error, status code %s", pr_resp.status_code
        )
    pr_content = pr_resp.json()
    res["title"] = pr_content["title"]
    res["description"] = parse_content(pr_content["body"])

    # request to get commits info.
    commit_resp = requests.get(
        url=convert_to_pull_commit_url(url),
        headers=headers,
    )
    if commit_resp.status_code != 200:
        raise Exception(
            "request commits error, status code %s", commit_resp.status_code
        )

    commit_content = commit_resp.json()

    commit_messages = []
    for content in commit_content:
        commit_messages.append(split_line_break(content["commit"]["message"]))
    res["commit_messages"] = ", ".join(commit_messages)

    # request to get diffs.
    diff_resp = requests.get(
        url=convert_to_diff_url(url),
        headers=headers,
    )
    if diff_resp.status_code != 200:
        raise Exception("request PR diff error, status code %s", diff_resp.status_code)
    res["pr_diffs"] = diff_resp.text

    return res
