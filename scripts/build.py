import platform
import shutil
import subprocess
from pathlib import Path


def build():
    dist_dir = Path("dist")
    shutil.rmtree(dist_dir, ignore_errors=True)

    cmd = [
        "python",
        "-m",
        "nuitka",
        "--standalone",
        "--output-dir=dist",
        "--output-filename=portfinder",
        "--lto=yes",
        "--python-flag=no_site",
        "--assume-yes-for-downloads",
        "--include-package=portfinder",
        "--include-package=uvloop" if platform.system() != "Windows" else "",
        "--include-package=structlog",
        "--remove-output",
        "portfinder/cli.py",
    ]

    print(f"[+] Building for {platform.system()}...")
    subprocess.run([arg for arg in cmd if arg], check=True)

    binary = dist_dir / "portfinder.dist" / "portfinder"
    if binary.exists():
        print(f"[+] Success! Binary: {binary}")
        print(f"[+] Test speed: time {binary} --help")
    else:
        raise RuntimeError("Build failed: binary not found")


if __name__ == "__main__":
    build()
