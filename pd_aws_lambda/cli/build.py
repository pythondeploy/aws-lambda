"""CLI command to build a Docker image."""
import json
from pathlib import Path
from typing import Any, Dict, Optional

import docker
import typer


def build_context_path_callback(value: Path) -> Path:
    """Ensure that the build_context_path is a directory."""
    if not value.is_dir():
        raise typer.BadParameter("Must to be an existing directory.")

    return value


def dockerfile_callback(value: Path) -> Path:
    """Ensure that the Dockerfile exists."""
    if not value.is_file():
        raise typer.BadParameter("Must to be an existing file.")

    return value


def json_args_callback(value: str) -> Optional[Dict[Any, Any]]:
    """Decode the json string for additional arguments."""
    if value is None:
        return

    try:
        extra_args = json.loads(value)
    except json.decoder.JSONDecodeError:
        raise typer.BadParameter("Invalid json string.")

    if not isinstance(extra_args, dict):
        raise typer.BadParameter("Must be an json object -> python dictionary.")

    return extra_args


def build_command(
    image_tag: str = typer.Argument(
        ...,
        help="Local docker image tag to be deployed",
    ),
    build_context_path: Path = typer.Argument(
        Path(),
        help="Path to the the root of the build context",
        callback=build_context_path_callback,
    ),
    dockerfile: Path = typer.Argument(
        Path("Dockerfile"),
        help="Path to the Dockerfile.",
        callback=dockerfile_callback,
    ),
    json_args: str = typer.Option(
        None,
        help=(
            "Json encoded string with extra arguments to pass to the"
            " Docker build call."
        ),
        callback=json_args_callback,
    ),
) -> None:
    """
    Build a Docker image using the Python Docker SDK.

    Use when you do not have the Docker client installed. It is specially
    useful for simple builds, but by passing --json-args, complex builds
    can be created.

    Check the official Python Docker SDK for the full list of arguments
    that can be passed via --json-args.

    https://docker-py.readthedocs.io/en/stable/api.html#module-docker.api.build
    """
    extra_args: Dict[Any, Any] = json_args or {}

    try:
        dockerfile = dockerfile.resolve().relative_to(build_context_path.resolve())
    except ValueError:
        raise typer.BadParameter("Dockerfile must exist in the context path.")

    docker_client = docker.from_env()

    extra_args.pop("tag", None)
    extra_args.pop("tag", None)
    extra_args.pop("path", None)
    extra_args.pop("dockerfile", None)
    extra_args.pop("decode", None)

    print(str(build_context_path.absolute()))
    build_output = docker_client.api.build(
        tag=image_tag,
        path=str(build_context_path.resolve()),
        dockerfile=str(dockerfile),
        decode=True,
        **extra_args
    )
    for output in build_output:
        stream = output.get("stream", None)
        message = output.get("message", None)
        if (stream or message) is not None:
            typer.echo(stream or message)
