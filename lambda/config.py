import json
import logging
from typing import Any, Callable, Dict, List

import boto3

from json_dumper import dumps
from s3_bucket_inspector import get_s3_bucket_list, get_s3_random_files

log = logging.getLogger(__name__)


class ConfigGenerator:
    def __init__(self, bucket_name: str):
        self._bucket_name = bucket_name

    def upload_config(self, output: Dict[str, Any]) -> None:
        """Upload the config to the config bucket with account ID as the key"""
        account = boto3.client("sts").get_caller_identity().get("Account")
        output_key = f"{account}.json"
        log.info("Uploading to s3://%s/%s", self._bucket_name, output_key)
        boto3.client("s3").put_object(
            Body=dumps(output),
            Bucket=self._bucket_name,
            Key=output_key,
            ACL="bucket-owner-read",
        )

    def generate_and_upload(self) -> None:
        self.upload_config(generate())


def generate() -> Dict[str, Any]:
    config_generators: List[Callable[..., Any]] = [
        get_s3_bucket_list,
        get_s3_random_files,
    ]
    output = {
        generator.__name__[4:]: generator(s3_client=boto3.client("s3"))
        for generator in config_generators
    }
    return output


def get_configs(config_bucket_name: str) -> Dict[str, Dict[str, Any]]:
    """Fetch configs for all accounts."""
    s3 = boto3.client("s3")
    config_keys = [
        config_obj["Key"]
        for config_obj in s3.list_objects_v2(Bucket=config_bucket_name)["Contents"]
        if config_obj["Key"] != "whitelist.json"
    ]
    return {
        key: json.load(s3.get_object(Bucket=config_bucket_name, Key=key)["Body"])
        for key in config_keys
    }
