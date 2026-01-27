"""
Install all requirements: root + all plugin requirements.
Usage: python install_requirements.py

This script has NO external dependencies — safe to run before pip install.
"""

import subprocess
import sys
from pathlib import Path


PLUGINS_DIR = Path(__file__).parent / "plugins"


def collect_plugin_requirements() -> list[str]:
    """Scan plugins/ for requirements.txt files and collect all lines."""
    all_reqs = []
    if not PLUGINS_DIR.is_dir():
        return all_reqs

    for plugin_dir in PLUGINS_DIR.iterdir():
        if not plugin_dir.is_dir():
            continue
        req_file = plugin_dir / "requirements.txt"
        if req_file.exists():
            lines = req_file.read_text(encoding="utf-8").splitlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    all_reqs.append(line)
    return all_reqs


def main():
    # 1. Install root requirements
    print("Installing root requirements...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    )

    # 2. Install plugin requirements
    plugin_reqs = collect_plugin_requirements()
    if plugin_reqs:
        print(f"\nInstalling plugin requirements: {plugin_reqs}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + plugin_reqs
        )
    else:
        print("\nNo plugin requirements found.")

    print("\nAll done.")


if __name__ == "__main__":
    main()
