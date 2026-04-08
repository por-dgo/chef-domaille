import tempfile
import unittest
from pathlib import Path

from app import create_app
from recipe_store import RecipeBundle, RecipeStore


class AppTests(unittest.TestCase):
    def test_home_page_and_health(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app = create_app(Path(temp_dir))
            client = app.test_client()

            home = client.get("/")
            self.assertEqual(home.status_code, 200)
            self.assertIn(b"Chef Domaille", home.data)

            health = client.get("/api/health")
            self.assertEqual(health.status_code, 200)
            self.assertTrue(health.get_json()["ok"])

    def test_put_and_get_recipe(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app = create_app(Path(temp_dir))
            client = app.test_client()

            payload = {
                "recipe_data": {
                    "strRecipeDescription": "alpha",
                    "intRecipeNoOfSteps": "1",
                    "intRecipeQty": "24",
                    "intRecipeReworkStep": "1",
                },
                "steps": [
                    {
                        "rRecipeStepTime": "25",
                        "rRecipeStepSpeed": "110",
                        "rRecipeStepSpeedRamp": "1",
                        "rRecipeStepPressure": "12",
                        "rRecipeStepPressureRamp": "1",
                        "rRecipeStepFCI": "0",
                        "rRecipeStepLowerSpeedLimit": "10",
                        "rRecipeStepUpperSpeedLimit": "10",
                        "rRecipeStepLowerPressureLimit": "0.5",
                        "rRecipeStepUpperPressureLimit": "0.5",
                        "rRecipeStepFixtureWeight": "0",
                        "intRecipeStepOpCode": "300",
                        "strRecipeStepFilm": "Brown 5um",
                        "strRecipeStepLubricant": "DI Water",
                        "strRecipeStepPad": "70 Duro Violet",
                        "rRecipeStepSpeedRampDn": "1",
                        "rRecipeStepPressureRampDn": "1",
                    }
                ],
            }

            put_res = client.put("/api/recipes/alpha", json=payload)
            self.assertEqual(put_res.status_code, 200)

            get_res = client.get("/api/recipes/alpha")
            self.assertEqual(get_res.status_code, 200)
            data = get_res.get_json()
            self.assertEqual(data["recipe_data"]["intRecipeQty"], "24")


if __name__ == "__main__":
    unittest.main()
