"""Entrypoint to the Python Deploy CLI."""
import importlib

if not importlib.util.find_spec("boto3") or not importlib.util.find_spec("docker"):
    raise Exception("Missing extra dependencies. install with `--extras deploy`")

import typer

from .deploy import deploy_command
from .run import run_command

app = typer.Typer()
app.command("deploy")(deploy_command)
app.command("run")(run_command)
