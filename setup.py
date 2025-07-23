from pathlib import Path

from poetry.factory import Factory
from setuptools import (
    find_packages,
    setup,
)


def get_metadata():
    poetry = Factory().create_poetry(Path.cwd())
    package = poetry.package

    return {
        "name": package.name,
        "version": str(package.version),
        "python_requires": package.python_versions,
        "install_requires": [dep.to_pep_508_string() for dep in package.requires],
    }


metadata = get_metadata()

setup(
    name=metadata["name"],
    version=metadata["version"],
    python_requires=metadata["python_requires"],
    install_requires=metadata["install_requires"],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "portfinder=portfinder.cli:run",
        ],
    },
)
