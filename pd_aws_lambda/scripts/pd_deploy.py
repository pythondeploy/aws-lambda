"""Script to delpoy the application to Lambda functions through PythonDeploy."""
import argparse
import json
import os
import time
import urllib.request
from pathlib import Path

from boto3 import Session

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


def deploy(app_id, api_key, s3_path):
    """Upload the build ZIP file to the application's S3 bucket."""
    build_dir = get_build_dir()
    build_file = str(Path(build_dir) / BUILD_FILE_NAME)

    if not app_id:
        raise ValueError("Missing App ID.")

    if not api_key:
        raise ValueError("Missing Api Key.")

    aws_account = get_aws_account_information(app_id, api_key)

    upload_to_s3(aws_account, build_file, s3_path)
    lambda_update(app_id, api_key, s3_path)


def _deploy_args(parser):
    """Add arguments required to run deploy()."""
    parser.add_argument(
        "--s3-path",
        help=("s3 path to upload the ZIP to. Default: 'python_deploy/{timestamp}.zip'"),
        default="python_deploy/{timestamp}.zip".format(timestamp=int(time.time())),
    )
    parser.add_argument(
        "--app-id",
        help="PythonDeploy application id. Default: environment variable PD_APP_ID ",
        required=False,
        default=os.environ.get("PD_APP_ID"),
    )
    parser.add_argument(
        "--api-key",
        help="PythonDeploy api key. Default: environment variable PD_API_KEY ",
        required=False,
        default=os.environ.get("PD_API_KEY"),
    )


def run():
    """CLI access to the deploy function."""
    parser = argparse.ArgumentParser(
        description=(
            "Deploy the built ZIP file to the AWS lambda functions. The ZIP file is"
            " uploaded to the private S3 bucket."
        )
    )
    _deploy_args(parser)

    args = parser.parse_args()
    s3_path = args.s3_path.lstrip("/")
    app_id = args.app_id
    api_key = args.api_key

    deploy(app_id, api_key, s3_path)
