import json
import logging
from datetime import datetime, timedelta
from typing import Any, cast, Dict, Generator, NewType, Optional, Set, Tuple

import boto3
from botocore.exceptions import ClientError
from botocore.vendored import requests

from json_dumper import dumps
from s3_bucket_inspector import (
    PubliclyDeletableBuckets,
    PubliclyListableBuckets,
    PubliclyReadableFiles,
    PubliclyUploadableBuckets,
)

log = logging.getLogger(__name__)
Output = NewType("Output", Dict[str, Any])
Whitelist = NewType("Whitelist", Set[Tuple[str, str]])


class TestRunner:
    """Takes per-account config files and runs tests against the buckets."""

    test_classes = (
        PubliclyListableBuckets,
        PubliclyReadableFiles,
        PubliclyUploadableBuckets,
        PubliclyDeletableBuckets,
    )

    def __init__(self, output_bucket_name: str, *configs: Any):
        self._bucket_name = output_bucket_name
        self._tests = [cls(**config) for cls in self.test_classes for config in configs]

    def _get_issues(self) -> Generator[Dict, None, None]:
        for test in self._tests:
            log.info("Running test: %s", type(test).__name__)
            for issue in test.find_issues():
                log.info("Found %s with resource '%s'", issue.issue, issue.resource)
                yield {"test": type(test).__name__, **issue.to_json()}

    def run(self, **extra: Any) -> Output:
        """Run the tests and return output."""
        start = datetime.utcnow()
        failures = list(self._get_issues())
        end = datetime.utcnow()
        output = {
            "start_time": start,
            "end_time": end,
            "tests": [test.__name__ for test in self.test_classes],
            "issues": failures,
            "external_ip": get_external_ip(),
            **extra,
        }
        return cast(Output, output)

    def run_and_upload(self, **extra: Any) -> Output:
        """Run the tests and upload output."""
        output = self.run(**extra)
        output_key = key_from_output(output)
        log.info("Uploading to s3://%s/%s", self._bucket_name, output_key)
        boto3.client("s3").put_object(
            Body=dumps(output), Bucket=self._bucket_name, Key=output_key
        )
        return output

    def _previous_output_s3(
        self, ignore_key: str = "", hours_in_past_to_search: int = 200
    ) -> Optional[Output]:
        s3 = boto3.client("s3")
        previous_outputs = s3.list_objects_v2(
            Bucket=self._bucket_name,
            StartAfter=(  # Really just want to make sure we retrieve the last run
                datetime.utcnow() - timedelta(hours=hours_in_past_to_search)
            ).isoformat(),
        )["Contents"]
        # Compare to previous outputs
        if previous_outputs and previous_outputs[-1]["Key"] == ignore_key:
            # Consistency of LIST after PUT is eventual so can't be guaranteed
            previous_outputs = previous_outputs[:-1]
        if previous_outputs:
            previous_key = previous_outputs[-1]["Key"]
            log.warning("Comparing to s3://%s/%s", self._bucket_name, previous_key)
            return json.load(
                s3.get_object(Bucket=self._bucket_name, Key=previous_key)["Body"]
            )
        return None

    def diff_previous_s3(
        self,
        latest_output: Output,
        whitelist: Optional[Whitelist] = None,
        hours_in_past_to_search: int = 200,
    ) -> Tuple[Set[Tuple[str, str]], Set[Tuple[str, str]]]:
        """Return the new issues and the fixed issues compared to the previous run."""
        latest_output_key = key_from_output(latest_output)
        previous_output = self._previous_output_s3(
            ignore_key=latest_output_key,
            hours_in_past_to_search=hours_in_past_to_search,
        )
        if previous_output:
            return diff_previous(latest_output, previous_output, whitelist)
        return set(), set()


def diff_previous(
    latest_output: Output,
    previous_output: Output,
    whitelist: Optional[Whitelist] = None,
) -> Tuple[Set[Tuple[str, str]], Set[Tuple[str, str]]]:
    """Return the new issues and the fixed issues compared to the previous output."""
    current_issues = set_of_issues(latest_output)
    previous_issues = set_of_issues(previous_output)
    if whitelist:
        current_issues -= whitelist
        previous_issues -= whitelist
    new_issues = current_issues - previous_issues
    resolved_issues = previous_issues - current_issues
    if new_issues:
        log.error("%d new issues: %s", len(new_issues), new_issues)
    if resolved_issues:
        log.info("%d issues resolved: %s", len(resolved_issues), resolved_issues)
    return new_issues, resolved_issues


def get_whitelist(config_bucket_name: str) -> Optional[Whitelist]:
    """Fetch whitelist.json, parse it and return it if it exists."""
    try:
        whitelist_dict = json.load(
            boto3.client("s3").get_object(
                Bucket=config_bucket_name, Key="whitelist.json"
            )["Body"]
        )
        return cast(
            Whitelist,
            {
                (issue, bucket_name)
                for issue, buckets in whitelist_dict.items()
                for bucket_name in buckets
            },
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return None
        raise


def set_of_issues(output: Output) -> Set[Tuple[str, str]]:
    """Processes run output JSON and returns a set of issue tuples to compare with previous runs."""
    return set((issue["issue"], issue["resource"]) for issue in output["issues"])


def key_from_output(output: Output) -> str:
    return f"{output['end_time'].isoformat()}.json"


def get_external_ip() -> str:
    return requests.get("http://checkip.amazonaws.com").text.rstrip()
