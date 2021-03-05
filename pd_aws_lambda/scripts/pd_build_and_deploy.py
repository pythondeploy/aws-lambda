"""Shortcut to pd_build and pd_deploy."""

import argparse

from .pd_build import build
from .pd_deploy import _deploy_args, deploy


def run():
    """CLI access to the build and deploy functions."""
    parser = argparse.ArgumentParser(
        description="Shortcut to run pd_build and pd_deploy commands."
    )
    _deploy_args(parser)
    args = parser.parse_args()

    build()
    deploy(**vars(args))
