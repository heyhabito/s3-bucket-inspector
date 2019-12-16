import os
import sys

import logging
import random
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, Generator, List, Optional

from botocore.client import BaseClient
import requests

from issues import Issue

CWD = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(CWD, "lib"))

log = logging.getLogger(__name__)


def bucket_root(bucket_name: str) -> str:
    if "." not in bucket_name:
        return f"https://{bucket_name}.s3.amazonaws.com"
    return f"https://s3-{bucket_region(bucket_name)}.amazonaws.com/{bucket_name}"


@lru_cache(maxsize=None)  # Don't actually care about it being LRU
def bucket_region(bucket_name: str) -> str:
    """Find the region of an S3 bucket.

    If your bucket name contains a dot then certificate validation will fail
    on https://b.u.c.k.e.t.s3.amazonaws.com since the wildcard certificate AWS
    returns (CN=*.s3.amazonaws.com) does not match multi-level subdomains.
    Instead of just setting verify=False, let's find the correct region.
    """
    head = requests.head(f"https://s3.amazonaws.com/{bucket_name}")
    region = head.headers.get("x-amz-bucket-region")
    assert (
        head.status_code == 301 and region
    ), f"Cannot find region for bucket {bucket_name}"
    return region


class PubliclyListableBucketIssue(Issue):
    @property
    def help(self) -> Optional[str]:
        return (
            "The list of keys stored within an S3 bucket should not be public, "
            f"but {bucket_root(self.resource)} lists the keys publicly."
        )


class PubliclyListableBuckets:
    """Raises an issue on any S3 bucket where the keys are publicly listable."""

    def __init__(self, s3_bucket_list: List[str], **_: Any) -> None:
        self._bucket_list = s3_bucket_list

    def find_issues(self) -> Generator[Issue, None, None]:
        for bucket_name in self._bucket_list:
            if bucket_publicly_listable(bucket_name):
                yield PubliclyListableBucketIssue(bucket_name)


def bucket_publicly_listable(bucket_name: str) -> bool:
    response = requests.get(f"{bucket_root(bucket_name)}/?max-keys=0")
    if response.status_code == 200:
        assert response.content.endswith(
            b"</ListBucketResult>"
        ), f"Unexpected ListBucketResult for {bucket_name}"
        return True
    assert (
        response.status_code == 403
    ), f"Unexpected status code {response.status_code} for bucket {bucket_name}"
    return False


class PubliclyUploadableBucketIssue(Issue):
    @property
    def help(self) -> Optional[str]:
        return (
            "An S3 bucket should not allow file uploads from the Internet, "
            f"but {self.resource} allows uploads."
        )


class PubliclyUploadableBuckets:
    """Raises an issue on any S3 bucket where public uploads are allowed"""

    def __init__(self, s3_bucket_list: List[str], **_: Any) -> None:
        self._bucket_list = s3_bucket_list

    def find_issues(self) -> Generator[Issue, None, None]:
        for bucket_name in self._bucket_list:
            if bucket_publicly_uploadable(bucket_name):
                yield PubliclyUploadableBucketIssue(bucket_name)


def bucket_publicly_uploadable(bucket_name: str) -> bool:
    test_key = "s3_bucket_inspector.upload.test"
    content: bytes = datetime.utcnow().isoformat().encode()
    response = requests.put(
        f"{bucket_root(bucket_name)}/{test_key}", files={"file": content}
    )
    return response.status_code == 200


class PubliclyDeletableBucketIssue(Issue):
    @property
    def help(self) -> Optional[str]:
        return (
            "An S3 bucket should not allow everyone to delete files, "
            f"but {self.resource} allows deletions."
        )


class PubliclyDeletableBuckets:
    """Raises an issue on any S3 bucket where public deletions are allowed."""

    def __init__(self, s3_bucket_list: List[str], **_: Any) -> None:
        self._bucket_list = s3_bucket_list

    def find_issues(self) -> Generator[Issue, None, None]:
        for bucket_name in self._bucket_list:
            if bucket_publicly_deletable(bucket_name):
                yield PubliclyDeletableBucketIssue(bucket_name)


def bucket_publicly_deletable(bucket_name: str) -> bool:
    test_key = "s3_bucket_inspector.delete.test"
    response = requests.delete(f"{bucket_root(bucket_name)}/{test_key}")
    return response.status_code == 204


class PubliclyReadableFileIssue(Issue):
    def __init__(self, bucket_name: str, key: str):
        self.key = key
        super().__init__(bucket_name)

    def to_json(self) -> Dict[str, Optional[str]]:
        return {"key": self.key, **super().to_json()}

    @property
    def help(self) -> Optional[str]:
        return (
            "The files stored within this S3 bucket should not be public, "
            f"but {bucket_root(self.resource)}/{self.key} was readable."
        )


class PubliclyReadableFiles:
    """Raises an issue on any S3 bucket with publicly readable files."""

    def __init__(self, s3_random_files: Dict[str, List[str]], **_: Any) -> None:
        self._keys_by_bucket = s3_random_files

    def find_issues(self) -> Generator[Issue, None, None]:
        for bucket_name, keys in self._keys_by_bucket.items():
            for key in keys:
                if file_publicly_readable(bucket_name, key):
                    yield PubliclyReadableFileIssue(bucket_name, key)
                    break  # Try next bucket


def file_publicly_readable(bucket_name: str, key: str) -> bool:
    response = requests.head(f"{bucket_root(bucket_name)}/{key}")
    return response.status_code != 403


def get_s3_bucket_list(s3_client: BaseClient, **_: Any) -> List[str]:
    """Use AWS key to list all our buckets."""
    return [bucket["Name"] for bucket in s3_client.list_buckets()["Buckets"]]


def keys_in_bucket(s3_client: BaseClient, bucket_name: str, max_keys: int) -> List[str]:
    log.debug("Getting %d keys from bucket '%s'", max_keys, bucket_name)
    result = s3_client.list_objects_v2(
        Bucket=bucket_name,
        MaxKeys=max_keys,  # Fetches the first max_keys files, sorted alphabetically by key
    )
    if result["KeyCount"] == 0:
        return []
    return [obj["Key"] for obj in result["Contents"]]


def get_s3_random_files(
    s3_client: BaseClient,
    keys_to_return: int = 10,
    keys_to_request: int = 100,
    **_: Any,
) -> Dict[str, List[str]]:
    """Use AWS key to list random files from our buckets."""
    files = {
        bucket_name: keys_in_bucket(s3_client, bucket_name, keys_to_request)
        for bucket_name in get_s3_bucket_list(s3_client)
    }
    return {
        bucket_name: random.sample(keys, min(keys_to_return, len(keys)))
        for bucket_name, keys in files.items()
        if len(keys)
    }
