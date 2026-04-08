# pip Hangs on Windows — WMI Deadlock Workaround

## Problem

`pip install` hangs indefinitely on corporate Windows machines running **Python 3.13** and **pip 26.x**.

- `pip list`, `pip cache`, and other local-only commands work fine.
- `pip install` (even with `--no-index`, `--dry-run`, or `-vvv`) hangs forever.
- Python's `urllib.request` can reach PyPI — the network is not blocked.

## Root Cause

pip 26 eagerly imports its vendored `truststore` module, which calls:

```
truststore/_api.py  →  platform.system()  →  platform.uname()  →  platform.win32_ver()  →  platform._wmi_query()
```

`platform._wmi_query()` in Python 3.13 uses a COM/WMI call to query Windows version info. On some corporate machines, **WMI is locked, slow, or restricted by Group Policy**, causing the call to deadlock.

pip 25.x didn't trigger this because it loaded `truststore` lazily.

## How We Found It

Used `faulthandler.dump_traceback()` on a watchdog timer to capture the stack trace during the hang:

```python
python -c "
import sys, time, threading, faulthandler

def watchdog():
    time.sleep(15)
    faulthandler.dump_traceback()
    import os; os._exit(1)

threading.Thread(target=watchdog, daemon=True).start()

from pip._internal.cli.main import main
sys.exit(main(['install', 'flask', '--dry-run']))
"
```

Stack trace showed `platform._wmi_query` at line 330 as the blocking call.

## Fix

Create a `sitecustomize.py` in the venv's `site-packages` that monkey-patches the WMI call with `sys.getwindowsversion()` (a direct kernel call — no WMI):

**File**: `.venv/Lib/site-packages/sitecustomize.py`

```python
import sys

if sys.platform == "win32":
    import platform

    def _wmi_query_bypass(*args, **kwargs):
        ver = sys.getwindowsversion()
        return (
            f"{ver.major}.{ver.minor}.{ver.build}",
            ver.product_type,
            f"{ver.major}.{ver.minor}.{ver.build}",
            ver.service_pack_major,
            ver.service_pack_minor,
        )

    platform._wmi_query = _wmi_query_bypass
```

This runs before any Python code in the venv, including pip.

## Important Notes

- **Not checked into git** — `sitecustomize.py` lives inside `.venv/` which is gitignored. You need to recreate it after making a new venv.
- **Per-venv fix** — apply to each venv on affected machines.
- **Affects all `platform` calls** — `platform.system()`, `platform.uname()`, `platform.win32_ver()` will all use the patched path. The returned data is functionally equivalent.
- **Upstream issue**: This is a Python 3.13 regression with WMI on restricted Windows environments. May be fixed in a future Python patch.

## Creating a venv on Affected Machines

`ensurepip` can also fail during `python -m venv` (separate issue). Workaround:

```powershell
# Create venv without pip
python -m venv .venv --without-pip

# Activate
.\.venv\Scripts\Activate.ps1

# Create sitecustomize.py FIRST (paste the content above into the file)
# Then bootstrap pip
python -m ensurepip --upgrade

# Now pip works
pip install -r requirements.txt
```

## Quick Diagnostic

If you suspect WMI is hanging, test with:

```powershell
python -c "import platform; print(platform.system())"
```

If that hangs, you have the WMI issue. Apply the fix above.
