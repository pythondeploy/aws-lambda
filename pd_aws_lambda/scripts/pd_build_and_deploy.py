"""Shortcut to pd_build and pd_deploy."""

import argparse

from .pd_build import build
from .pd_deploy import _deploy_args, deploy


def run():
    """CLI access to the build and deploy functions."""
    parser = argparse.ArgumentParser(
        description="Build and deploy the application code to AWS Lambda functions."
    )
    _deploy_args(parser)

    args = parser.parse_args()

    s3_path = args.s3_path.lstrip("/")
    app_id = args.app_id
    api_key = args.api_key

    build()
    deploy(app_id, api_key, s3_path)
