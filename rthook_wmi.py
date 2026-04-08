# PyInstaller runtime hook: patch platform._wmi_query to avoid deadlock.
# Python 3.13 on corporate Windows can hang in _wmi_query() due to
# restricted WMI access. This runs before app code loads.
import sys

if sys.platform == "win32":
    import platform

    def _wmi_query_bypass(table, *keys):
        if table == "OS":
            ver = sys.getwindowsversion()
            data = {
                "Version": f"{ver.major}.{ver.minor}.{ver.build}",
                "ProductType": ver.product_type,
                "Caption": f"Microsoft Windows {ver.major}.{ver.minor}.{ver.build}",
                "ServicePackMajorVersion": ver.service_pack_major,
                "ServicePackMinorVersion": ver.service_pack_minor,
            }
        elif table == "CPU":
            import struct
            data = {
                "Manufacturer": "GenuineIntel",
                "Caption": f"{struct.calcsize('P') * 8}-bit processor",
            }
        else:
            data = {k: "" for k in keys}
        return tuple(data.get(k, "") for k in keys)

    if hasattr(platform, "_wmi_query"):
        platform._wmi_query = _wmi_query_bypass
