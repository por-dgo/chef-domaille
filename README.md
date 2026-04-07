# Chef Domaille

Simple offline recipe generator for Domaille APM-HDC-5320.

## What It Does

- Creates the default Domaille recipe folder structure if it does not exist
- Creates a default settings file and starter recipe
- Lists available recipes
- Displays recipe details and step files
- Guides creation of new recipes interactively

## Run

```powershell
python .\recipe.py
```

The script can create the default Domaille/Processes/Steps folder structure if it is missing.

## Basic File Structure

```text
Domaille/
	Settings.txt
	Processes/
		default
		<recipe_name>
		Steps/
			default.001
			default.002
			default.003
			<recipe_name>.001
			...
```

Recipe files in Processes define overall recipe metadata (description, step count, quantity).
Step files in Processes/Steps define per-step values like time, pressure, speed, and materials.

## License

MIT. See LICENSE.
