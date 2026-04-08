''' Offline Recipe Generator for Domaille APM-HDC-5320

(c) 2024 under MIT License for not-for-profit use with attribution.
    Developed at the Fiber Optics Laboratory at Teledyne DGO, 2024.
'''

import os

from recipe_io import read_recipe, read_step, serialize_kv_lines, write_recipe, write_step


DOMAILLE_ROOT = "Domaille"


def _default_step_data(time, pressure, fci, film, description1, description2=""):
  data = {
    "rRecipeStepTime": time,
    "rRecipeStepSpeed": 110,
    "rRecipeStepSpeedRamp": 1,
    "rRecipeStepPressure": pressure,
    "rRecipeStepPressureRamp": 1,
    "rRecipeStepFCI": fci,
    "rRecipeStepLowerSpeedLimit": 10,
    "rRecipeStepUpperSpeedLimit": 10,
    "rRecipeStepLowerPressureLimit": 0.5,
    "rRecipeStepUpperPressureLimit": 0.5,
    "rRecipeStepFixtureWeight": 0,
    "intRecipeStepOpCode": 300,
    "strRecipeStepFilm": film,
    "strRecipeStepLubricant": "DI Water",
    "strRecipeStepPad": "70 Duro Violet",
    "strRecipeStepDescription1": description1,
  }
  if description2:
    data["strRecipeStepDescription2"] = description2
  data["rRecipeStepSpeedRampDn"] = 1
  data["rRecipeStepPressureRampDn"] = 1
  return data

def CreateDefaultFiles(default="default"):
  ''' Create Default Directory Structure and Files for Polisher Recipes '''
  print("Creating default directory structure...", end=" ")
  try:
    os.makedirs(f'{DOMAILLE_ROOT}/Processes/Steps')
  except Exception as e:
    print('FAILED: ', e)
    raise e
  else: print('done.')
  print("Creating default settings file...", end=" ")
  try:
    with open(f'{DOMAILLE_ROOT}/Settings.txt', 'x') as f:
      f.write('Max Quantity,72\n')
      f.write('Film,<None>,Brown 5um,Purple 1um,Clear FOS-22\n')
      f.write('Pad,<None>,60 Duro Blue,65 Duro Dark Blue,70 Duro Violet,')
      f.write('75 Duro Brown,80 Duro Green,85 Duro Gray,90 Duro Black\n')
      f.write('Lubricant,<None>,DI Water\n')
  except Exception as e:
    print('FAILED: ', e)
    raise e
  else: print('done.')
  print("Creating default 3-step recipe...", end=" ")
  try:
    recipe_data = {
      "strRecipeDescription": "default recipe",
      "intRecipeNoOfSteps": 3,
      "intRecipeQty": 30,
      "intRecipeReworkStep": 1,
    }
    write_recipe(DOMAILLE_ROOT, default, recipe_data)

    write_step(
      DOMAILLE_ROOT,
      default,
      1,
      _default_step_data(25, 15, 5, "Brown 5um", "Rough Polish", "Geometry"),
    )
    write_step(
      DOMAILLE_ROOT,
      default,
      2,
      _default_step_data(35, 12, 5, "Purple 1um", "Medium Polish"),
    )
    write_step(
      DOMAILLE_ROOT,
      default,
      3,
      _default_step_data(35, 12, 3, "Clear FOS-22", "Final Polish"),
    )


  except Exception as e:
    print('FAILED: ', e)
    raise e
  else: print('done.')
   

def Menu():
  print()
  print("(L)ist Recipes")
  print("(V)iew a Recipe")
  print("(N)ew Recipe")   
  print("(Q)uit program and exit")


def ListRecipes():
# get a list of recipes from Domaille/Processes/
  try:
    recipeList = os.listdir(f"{DOMAILLE_ROOT}/Processes/")
    recipeList.remove('Steps')
  except Exception as e:
    raise e
  s = "" if len(recipeList) == 1 else "s"
  print(f"{len(recipeList)} recipe{s} found:")
  for index,recipe in enumerate(recipeList):
    print(f"  ({index+1}) {recipe}")
  return recipeList


def ViewRecipe():
  recipeList = ListRecipes()
  print("Which recipe would you like to view? (#)")
  try:
    recipeNum = int(input(" >> "))-1
    recipeName = recipeList[recipeNum]
  except Exception as e:
    print("Recipe not found.")
    print(e)
    return

  # Get the main recipe process:
  try:
    recipe_data = read_recipe(DOMAILLE_ROOT, recipeName)
  except Exception as e:
    print('ERROR', e)
    return

  cwd = os.getcwd()
  print(f'{cwd}\\{DOMAILLE_ROOT}\\Processes\\{recipeName}')
  for line in serialize_kv_lines(recipe_data):
    print(line, end="")

  try:
    recipeNoOfSteps = int(recipe_data["intRecipeNoOfSteps"])
  except Exception as e:
    print(f"ERROR: Invalid step count in recipe file: {e}")
    return

  # Get each step of the recipe:  
  print()
  for step in range(1, recipeNoOfSteps+1):
    print(f"STEP #{step}:")
    try:
      step_data = read_step(DOMAILLE_ROOT, recipeName, step)
      print("".join(serialize_kv_lines(step_data)))
    except Exception as e:
      print(f"ERROR: Could not find file for Step #{step}")
      print(e)
      return


def NewRecipe():
  print("Creating new recipe...")
  recipeName = input("new recipe name: >> ")
  if not recipeName:
    print("Invalid recipe name.")
    return
  if os.path.exists(f"{DOMAILLE_ROOT}/Processes/{recipeName}"):
    print("Recipe name already exists. Recipe creation cancelled")
    return

  steps = input(f"How many steps in recipe {recipeName}? (default: 3) >> ")
  try:
    if steps == "": steps = 3
    else: steps = int(steps)
    if steps < 1 or steps > 9: raise ValueError
  except Exception as e: 
    print(f"ERROR: {e}")
    print("Invalid number of steps. Range is 1-9. Recipe creation cancelled.")
    return

  qty = input("what is the recipe max number of contacts? (default: 30) >> ")
  try:
    if qty == "": qty = 30
    else: qty = int(qty)
    if qty < 2 or qty > 72: raise ValueError
  except Exception as e: 
    print(f"ERROR: {e}")
    print("Invalid qty of contacts. Range is 2-72. Recipe creation cancelled.")
    return

  # generate the base recipe file:
  try:
    write_recipe(
      DOMAILLE_ROOT,
      recipeName,
      {
        "strRecipeDescription": recipeName,
        "intRecipeNoOfSteps": steps,
        "intRecipeQty": qty,
        "intRecipeReworkStep": 1,
      },
    )
  except Exception as e:
    print("ERROR", e)
    return
  
  # get parameters from user and generate step files:
  for step in range(1, steps+1):
    print(f"Step {step} of {steps}:")
    time = 0
    while time < 10 or time > 300:
      print(f"  How many seconds should step #{step} run?")
      time = input(" >> ")   
      # validate input:
      try:
        time = int(time)
        if time < 10 or time > 300: 
          raise ValueError
      except Exception as e:
        print(f"ERROR: {e}. Value should be between 10 and 300.")
        time = 0
    pressure = -1
    while pressure < 0 or pressure > 16:
      print(f"  How much total pressure should step #{step} apply for {qty} contacts? (in lbs)")
      pressure = input(" >> ")
      # validate input for pressure:
      try:
        pressure = float(pressure)
        if pressure < 0 or pressure > 16:
          raise ValueError
      except Exception as e:
        print(f"ERROR: {e} Value should be between 0 and 16.")
        pressure = -1
        continue
      print(f"{pressure} lbs of pressure for {qty} contacts is {pressure/qty} lbs per contact.")
      confirm = input("Is this correct? Y/N >> ")
      if confirm.upper() == "Y": 
        break
      else:
        pressure = -1
        continue

    # time and pressure are now set. Build the recipe and write to file:
    try:
      write_step(
        DOMAILLE_ROOT,
        recipeName,
        step,
        {
          "rRecipeStepTime": time,
          "rRecipeStepSpeed": 110,
          "rRecipeStepSpeedRamp": 1,
          "rRecipeStepPressure": pressure,
          "rRecipeStepPressureRamp": 1,
          "rRecipeStepFCI": 5,
          "rRecipeStepSpeedRampDn": 1,
          "rRecipeStepPressureRampDn": 1,
        },
      )
    except Exception as e:
      print(f"ERROR while writing recipe step {step} to file: {e}.")
      raise e
    
  print(f"Recipe {recipeName} generated with {steps} steps.")
  print(f"You may copy Domaille folder from {os.getcwd()} to flash drive.")
       

def main():
  print()
  print("Offline Recipe Generator for Domaille APM-HDC-5320\n")
  # check for file structure
  if os.path.isdir(f'{DOMAILLE_ROOT}/Processes/Steps'):
    print('Domaille path found in current working directory:')
    print(os.getcwd())
  else:
    print('Domaille path not found in current working directory...')
    print(os.getcwd())
    print("generate recipe file structure?", end =" ")
    option = input("(Y/N) > ")
    if option.upper() == "Y":
      CreateDefaultFiles()
    else:
      print("No working directory. Exiting.")
      return
  option = ""
  while option.upper() != "Q":
    Menu()
    option = input(" >> ")
    if option.upper() == "L": ListRecipes()
    if option.upper() == "V": ViewRecipe()
    if option.upper() == "N": NewRecipe()


if __name__=="__main__":
  main()
  input("  press Enter to exit program...\n")
