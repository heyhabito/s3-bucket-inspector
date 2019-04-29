import os
import json
from base64 import b64decode
from typing import Any, Dict, List, NamedTuple, Set, Tuple

import boto3
from botocore.vendored import requests


class IssueGroup(NamedTuple):
    color: str
    title: str
    issues: Set[Tuple[str, str]]


def build_message(
    issue_groups: List[IssueGroup], output_bucket_name: str, output_key: str
) -> Dict[str, Any]:
    link = f"https://{output_bucket_name}.s3.amazonaws.com/{output_key}"
    message_body = {
        "attachments": [
            {
                "color": color,
                "title": title,
                "title_link": link,
                "text": "\n".join(f"{resource}: {issue}" for issue, resource in issues),
            }
            for color, title, issues in issue_groups
        ]
    }

    return message_body


def send_diff_message(
    new_issues: Set[Tuple[str, str]],
    fixed_issues: Set[Tuple[str, str]],
    output_bucket_name: str,
    output_key: str,
) -> None:
    """Send slack message listing new and fixed issues if there are any."""
    issue_groups = []
    if new_issues:
        issue_groups.append(
            IssueGroup(
                "danger", f"{len(new_issues)} new bucket security issues", new_issues
            )
        )
    if fixed_issues:
        issue_groups.append(
            IssueGroup(
                "good",
                f"{len(fixed_issues)} bucket security issues fixed",
                fixed_issues,
            )
        )
    if issue_groups:
        message = build_message(issue_groups, output_bucket_name, output_key)
        send(message)


def send_full_message(
    issues: Set[Tuple[str, str]], output_bucket_name: str, output_key: str
) -> None:
    """Send slack message listing all issues if there are any."""
    if issues:
        message = build_message(
            [IssueGroup("danger", f"{len(issues)} bucket security issues", issues)],
            output_bucket_name,
            output_key,
        )
        send(message)


def send(message: Dict[str, Any]) -> None:
    if "ENCRYPTED_HOOK_URL" in os.environ:
        hook = (
            boto3.client("kms")
            .decrypt(CiphertextBlob=b64decode(os.environ["ENCRYPTED_HOOK_URL"]))[
                "Plaintext"
            ]
            .decode("utf-8")
        )
    elif "HOOK_URL" in os.environ:
        hook = os.environ["HOOK_URL"]
    else:
        return
    requests.post(hook, data=json.dumps(message)).raise_for_status()
