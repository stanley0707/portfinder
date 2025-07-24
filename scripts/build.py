import platform
import shutil
import subprocess
from pathlib import Path


def build():
    dist_dir = Path("dist")
    if dist_dir.exists():
        for item in dist_dir.glob("*"):
            if item.is_file():
                item.unlink()
            else:
                shutil.rmtree(item)

    cmd = [
        "python",
        "-m",
        "nuitka",
        "--onefile",
        "--output-dir=dist",
        "--output-filename=portfinder",
        "--include-package=portfinder",
        "--remove-output",
        "--assume-yes-for-downloads",
        "--disable-console" if platform.system() == "Windows" else "",
    ]

    if platform.system() == "Darwin":
        cmd.extend(
            [
                "--macos-disable-console",
            ]
        )

    cmd.append("portfinder/cli.py")

    subprocess.run([arg for arg in cmd if arg], check=True)


if __name__ == "__main__":
    build()
    print("Build complete! Binary is in dist/")
