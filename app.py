"""Local Flask API for virtual Domaille recipe machine."""

from __future__ import annotations

import ctypes
import io
import os
import socket
import tempfile
import threading
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from recipe_store import RecipeBundle, RecipeStore
from recipe_settings import RecipeSettings
from recipe_validation import PROFILE_5316_5320, validate_bundle


def _find_available_port(host: str, start_port: int, max_tries: int = 100) -> int:
    for offset in range(max_tries):
        port = start_port + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if sock.connect_ex((host, port)) != 0:
                return port
    raise RuntimeError(
        f"No available port found between {start_port} and {start_port + max_tries - 1}"
    )


def _bundle_from_json(recipe_name: str, payload: dict) -> RecipeBundle:
    recipe_data = payload.get("recipe_data") or {}
    steps = payload.get("steps") or []
    recipe_data = {k: str(v) for k, v in recipe_data.items()}
    normalized_steps = [{k: str(v) for k, v in step.items()} for step in steps]
    return RecipeBundle(recipe_name=recipe_name, recipe_data=recipe_data, steps=normalized_steps)


def _list_removable_drives() -> list[str]:
    """Return Windows removable drive roots like ['F:\\', 'G:\\']."""
    if os.name != "nt":
        return []

    drives: list[str] = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    get_drive_type = ctypes.windll.kernel32.GetDriveTypeW

    for i in range(26):
        if bitmask & (1 << i):
            drive = f"{chr(65 + i)}:\\"
            # DRIVE_REMOVABLE = 2
            if get_drive_type(drive) == 2:
                drives.append(drive)

    return drives


def create_app(store_root: Path | None = None) -> Flask:
    app = Flask(__name__)
    store = RecipeStore(store_root or RecipeStore.default_root())
    store.ensure_structure()

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True, "store_root": str(store.root), "profile": PROFILE_5316_5320["name"]})

    @app.get("/api/recipes")
    def list_recipes():
        return jsonify({"recipes": store.list_recipes()})

    @app.get("/api/recipes/<recipe_name>")
    def get_recipe(recipe_name: str):
        bundle = store.load_bundle(recipe_name)
        return jsonify({
            "recipe_name": bundle.recipe_name,
            "recipe_data": bundle.recipe_data,
            "steps": bundle.steps,
        })

    @app.put("/api/recipes/<recipe_name>")
    def put_recipe(recipe_name: str):
        payload = request.get_json(force=True)
        bundle = _bundle_from_json(recipe_name, payload)
        result = validate_bundle(bundle)
        if not result.ok:
            return jsonify({"ok": False, "errors": result.errors, "warnings": result.warnings}), 400
        store.save_bundle(bundle)
        return jsonify({"ok": True, "warnings": result.warnings})

    @app.delete("/api/recipes/<recipe_name>")
    def delete_recipe(recipe_name: str):
        store.delete_recipe(recipe_name)
        return jsonify({"ok": True})

    @app.post("/api/transfer/import/thumb")
    def import_thumb():
        payload = request.get_json(force=True)
        source_path = payload["source_path"]
        selected = payload.get("selected_recipes")
        overwrite = bool(payload.get("overwrite", False))
        result = store.import_from_domaille_folder(source_path, selected, overwrite=overwrite)
        return jsonify({"ok": True, "copied": result.copied, "skipped": result.skipped})

    @app.post("/api/transfer/export/thumb")
    def export_thumb():
        payload = request.get_json(force=True)
        destination_path = payload["destination_path"]
        selected = payload.get("selected_recipes") or []
        result = store.export_to_domaille_folder(destination_path, selected)
        return jsonify({"ok": True, "copied": result.copied, "skipped": result.skipped})

    @app.post("/api/transfer/import/zip")
    def import_zip():
        payload = request.get_json(force=True)
        zip_path = payload["zip_path"]
        selected = payload.get("selected_recipes")
        overwrite = bool(payload.get("overwrite", False))
        result = store.import_from_zip(zip_path, selected, overwrite=overwrite)
        return jsonify({"ok": True, "copied": result.copied, "skipped": result.skipped})

    @app.post("/api/transfer/export/zip")
    def export_zip():
        payload = request.get_json(force=True)
        zip_path = payload["zip_path"]
        selected = payload.get("selected_recipes") or []
        result = store.export_to_zip(zip_path, selected)
        return jsonify({"ok": True, "copied": result.copied, "skipped": result.skipped})

    @app.get("/api/system/removable-drives")
    def removable_drives():
        return jsonify({"drives": _list_removable_drives()})

    @app.post("/api/transfer/export/book")
    def export_book():
        payload = request.get_json(force=True)
        selected = payload.get("selected_recipes")
        if not selected:
            selected = store.list_recipes()

        with tempfile.NamedTemporaryFile(suffix=".chef", delete=False) as temp_file:
            temp_path = temp_file.name

        store.export_to_zip(temp_path, selected, include_settings=True)
        data = Path(temp_path).read_bytes()
        try:
            Path(temp_path).unlink()
        except OSError:
            pass

        return send_file(
            io.BytesIO(data),
            as_attachment=True,
            download_name="recipe-book.chef",
            mimetype="application/octet-stream",
        )

    @app.post("/api/transfer/import/book")
    def import_book():
        if "file" not in request.files:
            return jsonify({"ok": False, "error": "No file provided"}), 400

        upload = request.files["file"]
        if not upload.filename:
            return jsonify({"ok": False, "error": "No file selected"}), 400

        with tempfile.NamedTemporaryFile(suffix=".chef", delete=False) as temp_file:
            temp_path = temp_file.name
            upload.save(temp_path)

        try:
            result = store.import_from_zip(temp_path, selected_recipes=None, overwrite=True)
        finally:
            try:
                Path(temp_path).unlink()
            except OSError:
                pass

        return jsonify({"ok": True, "copied": result.copied, "skipped": result.skipped})

    @app.get("/api/profiles/current")
    def profile():
        return jsonify(PROFILE_5316_5320)

    @app.get("/api/settings/consumables")
    def get_consumables():
        settings = RecipeSettings(store.settings_path)
        consumables = settings.get_consumables()
        return jsonify(consumables)

    @app.put("/api/settings/consumables")
    def update_consumables():
        payload = request.get_json(force=True)
        settings = RecipeSettings(store.settings_path)
        # payload should be like: {"Film": [...], "Pad": [...], "Lubricant": [...]}
        settings.set_consumables(payload)
        return jsonify({"ok": True})

    @app.get("/api/settings")
    def get_settings():
        settings = RecipeSettings(store.settings_path)
        all_settings = settings.read_settings()
        return jsonify(all_settings)

    @app.put("/api/settings")
    def update_settings():
        payload = request.get_json(force=True)
        settings = RecipeSettings(store.settings_path)
        settings.write_settings(payload)
        return jsonify({"ok": True})

    return app


if __name__ == "__main__":
    host = "127.0.0.1"
    port = _find_available_port(host, 5000)
    url = f"http://{host}:{port}"
    print(f"Starting Chef Domaille at {url}")
    app = create_app()
    # Open the default browser shortly after server startup begins.
    threading.Timer(0.8, lambda: webbrowser.open(url, new=2)).start()
    app.run(host=host, port=port, debug=False)
