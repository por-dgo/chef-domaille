import tempfile
import unittest
from pathlib import Path

from recipe_store import RecipeBundle, RecipeStore


class RecipeStoreTests(unittest.TestCase):
    def test_save_load_and_delete_bundle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = RecipeStore(Path(temp_dir))
            bundle = RecipeBundle(
                recipe_name="alpha",
                recipe_data={
                    "strRecipeDescription": "alpha",
                    "intRecipeNoOfSteps": "2",
                    "intRecipeQty": "24",
                    "intRecipeReworkStep": "1",
                },
                steps=[
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
                    },
                    {
                        "rRecipeStepTime": "35",
                        "rRecipeStepSpeed": "110",
                        "rRecipeStepSpeedRamp": "1",
                        "rRecipeStepPressure": "10",
                        "rRecipeStepPressureRamp": "1",
                        "rRecipeStepFCI": "0",
                        "rRecipeStepLowerSpeedLimit": "10",
                        "rRecipeStepUpperSpeedLimit": "10",
                        "rRecipeStepLowerPressureLimit": "0.5",
                        "rRecipeStepUpperPressureLimit": "0.5",
                        "rRecipeStepFixtureWeight": "0",
                        "intRecipeStepOpCode": "300",
                        "strRecipeStepFilm": "Purple 1um",
                        "strRecipeStepLubricant": "DI Water",
                        "strRecipeStepPad": "70 Duro Violet",
                        "rRecipeStepSpeedRampDn": "1",
                        "rRecipeStepPressureRampDn": "1",
                    },
                ],
            )

            store.save_bundle(bundle)
            self.assertIn("alpha", store.list_recipes())
            loaded = store.load_bundle("alpha")
            self.assertEqual(loaded.recipe_data["intRecipeQty"], "24")
            self.assertEqual(len(loaded.steps), 2)

            store.delete_recipe("alpha")
            self.assertNotIn("alpha", store.list_recipes())


if __name__ == "__main__":
    unittest.main()
