"""Script to delpoy the application to Lambda functions through PythonDeploy."""
import argparse
import json
import os
import time
import urllib.request
from pathlib import Path
from time import sleep

from boto3 import Session

from .exceptions import CloudFormationTransofrmationFailed
from .helpers import (
    BUILD_FILE_NAME,
    PD_API_URL,
    ctx,
    get_aws_account_information,
    get_build_dir,
)


def upload_to_s3(aws_account, build_file, s3_path):
    """
    Upload a local file to a S3 bucket using the provided access data.

    `aws_account` is a dictionary with access information from the
    PythonDeploy API.
    """
    print("Uploading file to S3")
    bucket = (
        Session(
            aws_access_key_id=aws_account["credentials"]["aws_access_key_id"],
            aws_secret_access_key=aws_account["credentials"]["aws_secret_access_key"],
            aws_session_token=aws_account["credentials"]["aws_session_token"],
            region_name=aws_account["credentials"]["region_name"],
        )
        .resource("s3")
        .Bucket(aws_account["private_bucket"])
    )

    bucket.upload_file(build_file, s3_path)

    s3_url = f"s3://{aws_account['private_bucket']}/{s3_path}"
    print(f"Successfully uploaded '{build_file}' to '{s3_url}'")


def lambda_update(app_id, api_key, s3_path):
    """Push the uploaded code to the Lambda functions using PythonDeploy."""
    print("Deploying code to Lambda functions")

    jsondata = json.dumps({"action": "lambda_deploy", "s3_path": s3_path})
    jsondataasbytes = jsondata.encode("utf-8")

    req = urllib.request.Request(PD_API_URL.format(app_id=app_id))
    req.add_header("Content-Length", len(jsondataasbytes))
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("Authorization", f"Bearer {api_key}")
    urllib.request.urlopen(req, jsondataasbytes, context=ctx)


def exponential():
    """Exponentially increasing generator, with a max value of 10."""
    n = 0
    limit = 10
    while True:
        exp = 0.5 * 2 ** n
        if exp > 10:
            yield 10

        yield limit
        n += 1


def cloud_formation_wait(aws_account):
    """
    Wait until the CloudFormation stack finishes applying changes.

    The Stack might not be ready to accept new changes, but the new code
    has been deployed to the functions.

    If the changes fail to be applied, an exception is raised.
    - pd_aws_lambda.exceptions.CloudFormationTransofrmationFailed
    """
    for sleep_time in exponential():
        print("Waiting for CloudFormation changes")
        stack_status = (
            Session(
                aws_access_key_id=aws_account["credentials"]["aws_access_key_id"],
                aws_secret_access_key=aws_account["credentials"][
                    "aws_secret_access_key"
                ],
                aws_session_token=aws_account["credentials"]["aws_session_token"],
                region_name=aws_account["credentials"]["region_name"],
            )
            .client("cloudformation")
            .describe_stacks(StackName=aws_account["stack_name"], NextToken="string")[
                "Stacks"
            ][0]["StackStatus"]
        )

        if stack_status != "UPDATE_IN_PROGRESS":
            break

        sleep(sleep_time)

    if stack_status not in [
        "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS",
        "UPDATE_COMPLETE",
    ]:
        raise CloudFormationTransofrmationFailed(stack_status)


def deploy(app_id, api_key, s3_path, wait, **kwargs):
    """Upload the build ZIP file to the application's S3 bucket."""
    s3_path = s3_path.lstrip("/")

    build_dir = get_build_dir()
    build_file = str(Path(build_dir) / BUILD_FILE_NAME)

    if not app_id:
        raise ValueError("Missing App ID.")

    if not api_key:
        raise ValueError("Missing Api Key.")

    aws_account = get_aws_account_information(app_id, api_key)

    upload_to_s3(aws_account, build_file, s3_path)
    lambda_update(app_id, api_key, s3_path)
    if wait:
        cloud_formation_wait(aws_account)


def _deploy_args(parser):
    """Add arguments required to run deploy()."""
    parser.add_argument(
        "--s3-path",
        help=("s3 path to upload the ZIP to. Default: 'python_deploy/{timestamp}.zip'"),
        default="python_deploy/{timestamp}.zip".format(timestamp=int(time.time())),
    )
    parser.add_argument(
        "--app-id",
        help="PythonDeploy application id. Default: environment variable PD_APP_ID",
        required=False,
        default=os.environ.get("PD_APP_ID"),
    )
    parser.add_argument(
        "--api-key",
        help="PythonDeploy api key. Default: environment variable PD_API_KEY",
        required=False,
        default=os.environ.get("PD_API_KEY"),
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help=(
            "Seconds to wait for AWS changes to be applied. By default this"
            " command exits as soon as AWS received the changes. If `--wait`"
            " is given, then the command finishes when the changes either are"
            " applied successfully, or fail to be applied."
        ),
    )


def run():
    """CLI access to the deploy function."""
    parser = argparse.ArgumentParser(
        description=(
            "Deploy the built ZIP file to the AWS lambda functions. The ZIP file is"
            " uploaded to the private S3 bucket. Any changes to your application"
            " pending to be deployed will also be applied with the new code."
        )
    )
    _deploy_args(parser)
    args = parser.parse_args()

    deploy(**vars(args))
