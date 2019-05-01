import logging
import os

from config import ConfigGenerator, get_configs
from run import get_whitelist, key_from_output, set_of_issues, TestRunner

from slack import send_diff_message, send_full_message


def initialise_logging():
    logging.basicConfig(
        level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s"
    )


def config_handler(event, context):  # pylint: disable=unused-argument
    initialise_logging()
    config_generator = ConfigGenerator(os.environ["CONFIG_BUCKET"])
    config_generator.generate_and_upload()
    return {"statusCode": 200}


def run_handler(event, context):  # pylint: disable=unused-argument
    initialise_logging()
    config_bucket_name = os.environ["CONFIG_BUCKET"]
    output_bucket_name = os.environ["OUTPUT_BUCKET"]
    configs = get_configs(config_bucket_name)
    test_runner = TestRunner(output_bucket_name, *configs.values())
    output = test_runner.run_and_upload(
        accounts=[k.split(".")[0] for k in configs.keys()]  # 123.json -> 123
    )
    whitelist = get_whitelist(config_bucket_name)
    if os.environ.get("DIFF_ONLY"):
        new, fixed = test_runner.diff_previous_s3(output, whitelist)
        send_diff_message(new, fixed, output_bucket_name, key_from_output(output))
    else:
        send_full_message(
            set_of_issues(output, whitelist),
            output_bucket_name,
            key_from_output(output),
        )
    return {"statusCode": 200}
