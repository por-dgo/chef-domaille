"""Local Flask API for virtual Domaille recipe machine."""

from __future__ import annotations

import tempfile
from pathlib import Path

from flask import Flask, jsonify, request

from recipe_store import RecipeBundle, RecipeStore
from recipe_validation import PROFILE_5316_5320, validate_bundle


def _bundle_from_json(recipe_name: str, payload: dict) -> RecipeBundle:
    recipe_data = payload.get("recipe_data") or {}
    steps = payload.get("steps") or []
    recipe_data = {k: str(v) for k, v in recipe_data.items()}
    normalized_steps = [{k: str(v) for k, v in step.items()} for step in steps]
    return RecipeBundle(recipe_name=recipe_name, recipe_data=recipe_data, steps=normalized_steps)


def create_app(store_root: Path | None = None) -> Flask:
    app = Flask(__name__)
    store = RecipeStore(store_root or RecipeStore.default_root())
    store.ensure_structure()

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

    @app.get("/api/profiles/current")
    def profile():
        return jsonify(PROFILE_5316_5320)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False)
