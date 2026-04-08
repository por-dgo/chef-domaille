import unittest

from recipe_store import RecipeBundle
from recipe_validation import validate_bundle


class RecipeValidationTests(unittest.TestCase):
    def test_valid_bundle(self):
        bundle = RecipeBundle(
            recipe_name="alpha",
            recipe_data={
                "strRecipeDescription": "alpha",
                "intRecipeNoOfSteps": "1",
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
                    "rRecipeStepFCI": "5",
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
        )
        result = validate_bundle(bundle)
        self.assertTrue(result.ok)

    def test_invalid_pressure_fails(self):
        bundle = RecipeBundle(
            recipe_name="alpha",
            recipe_data={
                "strRecipeDescription": "alpha",
                "intRecipeNoOfSteps": "1",
                "intRecipeQty": "24",
                "intRecipeReworkStep": "1",
            },
            steps=[
                {
                    "rRecipeStepTime": "25",
                    "rRecipeStepSpeed": "110",
                    "rRecipeStepSpeedRamp": "1",
                    "rRecipeStepPressure": "20",
                    "rRecipeStepPressureRamp": "1",
                    "rRecipeStepFCI": "5",
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
        )
        result = validate_bundle(bundle)
        self.assertFalse(result.ok)
        self.assertTrue(any("rRecipeStepPressure" in e for e in result.errors))


if __name__ == "__main__":
    unittest.main()
