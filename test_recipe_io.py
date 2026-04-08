import tempfile
import unittest
from pathlib import Path

from recipe_io import get_step_path, read_recipe, read_step, write_recipe, write_step


class RecipeIoTests(unittest.TestCase):
    def test_step_path_is_zero_padded(self):
        path = get_step_path("Domaille", "alpha", 7)
        self.assertTrue(str(path).endswith(str(Path("Domaille/Processes/Steps/alpha.007"))))

    def test_recipe_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = str(Path(temp_dir) / "Domaille")
            recipe_name = "sample"
            recipe_data = {
                "strRecipeDescription": "sample",
                "intRecipeNoOfSteps": 2,
                "intRecipeQty": 24,
                "intRecipeReworkStep": 1,
            }
            step1 = {
                "rRecipeStepTime": 25,
                "rRecipeStepPressure": 12,
            }
            step2 = {
                "rRecipeStepTime": 30,
                "rRecipeStepPressure": 10,
            }

            write_recipe(root, recipe_name, recipe_data)
            write_step(root, recipe_name, 1, step1)
            write_step(root, recipe_name, 2, step2)

            loaded_recipe = read_recipe(root, recipe_name)
            loaded_step1 = read_step(root, recipe_name, 1)
            loaded_step2 = read_step(root, recipe_name, 2)

            self.assertEqual(loaded_recipe["strRecipeDescription"], "sample")
            self.assertEqual(loaded_recipe["intRecipeNoOfSteps"], "2")
            self.assertEqual(loaded_recipe["intRecipeQty"], "24")
            self.assertEqual(loaded_step1["rRecipeStepTime"], "25")
            self.assertEqual(loaded_step2["rRecipeStepPressure"], "10")


if __name__ == "__main__":
    unittest.main()
