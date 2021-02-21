"""Script to build a lambda compatible package."""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from shutil import copyfile

from .helpers import BUILD_FILE_NAME, PACKAGES_DIR_PATH, get_build_dir


def generate_requirements_txt(build_dir):
    """Generate a requirements.txt inside the build path."""
    print("Generating requirements.txt file.")
    copyfile(Path("./requirements.txt"), build_dir / Path("requirements.txt"))


def pip_install(build_dir):
    """
    Install the packages from the requirements.txt.

    Packages are installed inside a subfolder in the `build_dir`.
    """
    print("Installing application dependencies.")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--target",
            str(build_dir / PACKAGES_DIR_PATH),
            "-r",
            str(build_dir / Path("requirements.txt")),
        ]
    )


def build_package(build_dir):
    """ZIP the dependencies and the application code."""
    file_path = build_dir / BUILD_FILE_NAME
    print("Zipping dependencies' code.")
    subprocess.check_call(
        ["zip", "-qr9", file_path, ".", "-x", "bin/*"], cwd=build_dir / PACKAGES_DIR_PATH
    )
    print("Zipping application's code.")
    subprocess.check_call(
        ["zip", "-qr9", file_path, ".", "-x", ".git/*", "-x", ".venv/*"]
    )


def build():
    """Build the app into a ZIP file to deploy to the Lambda functions."""
    build_dir = get_build_dir(True)

    if build_dir.exists():
        if not build_dir.is_dir():
            raise ValueError("{build_dir} is not a directory")
        elif os.listdir(build_dir):
            raise ValueError("{build_dir} is not empty")

    generate_requirements_txt(build_dir)
    pip_install(build_dir)
    build_package(build_dir)


def run():
    """CLI access to the build function."""
    parser = argparse.ArgumentParser(
        description="Build the app into a ZIP file to deploy to the Lambda functions."
    )
    parser.parse_args()

    build()
