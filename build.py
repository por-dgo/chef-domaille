# build.py — Package Chef Domaille as a single .exe

import os
import shutil
import subprocess
import sys
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")
DIST_DIR = os.path.join(BASE_DIR, "dist")
APP_NAME = "Chef Domaille"
VERSION_FILE = os.path.join(BASE_DIR, "_version.py")


def _get_git_version():
    """Read version from the latest git tag (e.g. v0.1.0 → 0.1.0).

    GitHub releases create tags automatically, so the release tag
    is our single source of version truth.
    """
    try:
        v = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            text=True,
            cwd=BASE_DIR,
        ).strip().lstrip("v")
        return v
    except Exception:
        print("  WARNING: No git tag found. Using 0.0.0.")
        print("           Create a GitHub release to set the version.")
        return "0.0.0"


def run(cmd, **kwargs):
    """Run a command and exit on failure."""
    print(f"  > {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=BASE_DIR, **kwargs)
    if result.returncode != 0:
        print(f"  FAILED (exit code {result.returncode})")
        sys.exit(result.returncode)


def main():
    print("=" * 50)
    print("  Chef Domaille — Build")
    print("=" * 50)

    # ------------------------------------------------------------------
    # 0. Read version from git tag and write _version.py for the bundle
    # ------------------------------------------------------------------
    version = _get_git_version()
    print(f"\n  Version: {version} (from git tag)")
    with open(VERSION_FILE, "w") as f:
        f.write(f'__version__ = "{version}"\n')

    # ------------------------------------------------------------------
    # 1. Ensure build tool is installed
    # ------------------------------------------------------------------
    print("\n[1/3] Installing PyInstaller...")
    run([VENV_PYTHON, "-m", "pip", "install", "--quiet", "pyinstaller"])

    # ------------------------------------------------------------------
    # 2. Clean previous build artifacts
    # ------------------------------------------------------------------
    print("\n[2/3] Cleaning previous build...")
    for d in ["build", "dist"]:
        p = os.path.join(BASE_DIR, d)
        if os.path.isdir(p):
            shutil.rmtree(p)
    spec = os.path.join(BASE_DIR, f"{APP_NAME}.spec")
    if os.path.isfile(spec):
        os.remove(spec)

    # ------------------------------------------------------------------
    # 3. Build single-file exe
    # ------------------------------------------------------------------
    print(f"\n[3/3] Building {APP_NAME}.exe ...")

    pyinstaller_args = [
        VENV_PYTHON, "-m", "PyInstaller",
        "--onefile",
        "--clean",
        "--name", APP_NAME,
        # Runtime hook to fix WMI deadlock on corporate Windows
        "--runtime-hook", "rthook_wmi.py",
        # _version.py is imported dynamically — tell PyInstaller about it
        "--hidden-import", "_version",
        # Bundle the HTML templates and static assets
        "--add-data", "templates;templates",
        "--add-data", "static;static",
        # Bundle favicon for serving
        "--add-data", "favicon.ico;.",
        # Exclude heavy/unused modules to keep size down
        "--exclude-module", "unittest",
        "--exclude-module", "test",
        "--exclude-module", "pydoc",
        "--exclude-module", "doctest",
        "--exclude-module", "xmlrpc",
        "--exclude-module", "pdb",
        "--exclude-module", "lib2to3",
        "--exclude-module", "multiprocessing",
        "--exclude-module", "tkinter",
        # Entry point
        "app.py",
    ]

    # Use favicon if present
    favicon = os.path.join(BASE_DIR, "favicon.ico")
    if os.path.isfile(favicon):
        idx = pyinstaller_args.index("--clean")
        pyinstaller_args.insert(idx + 1, "--icon")
        pyinstaller_args.insert(idx + 2, favicon)

    run(pyinstaller_args)

    # Clean up baked version file (not needed in source tree)
    if os.path.isfile(VERSION_FILE):
        os.remove(VERSION_FILE)

    exe_path = os.path.join(DIST_DIR, f"{APP_NAME}.exe")
    if os.path.isfile(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)

        # Create zip archive for GitHub release upload
        zip_name = f"{APP_NAME}-v{version}.zip"
        zip_path = os.path.join(DIST_DIR, zip_name)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(exe_path, f"{APP_NAME}.exe")
        zip_mb = os.path.getsize(zip_path) / (1024 * 1024)

        print()
        print("=" * 50)
        print(f"  BUILD SUCCESS  (v{version})")
        print(f"  Output: dist\\{APP_NAME}.exe  ({size_mb:.1f} MB)")
        print(f"  Zip:    dist\\{zip_name}  ({zip_mb:.1f} MB)")
        print("=" * 50)
        print()
        print("  Upload the .zip to the GitHub release.")
        print("  Users just extract and double-click to run.")
    else:
        print("\n  BUILD FAILED — exe not found.")
        sys.exit(1)


if __name__ == "__main__":
    main()
