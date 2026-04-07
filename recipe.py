''' Offline Recipe Generator for Domaille APM-HDC-5320

(c) 2024 under MIT License for not-for-profit use with attribution.
    Developed at the Fiber Optics Laboratory at Teledyne DGO, 2024.
'''

import os

def CreateDefaultFiles(default="default"):
  ''' Create Default Directory Structure and Files for Polisher Recipes '''
  print("Creating default directory structure...", end=" ")
  try:
    os.makedirs('Domaille/Processes/Steps')
  except Exception as e:
    print('FAILED: ', e)
    raise e
  else: print('done.')
  print("Creating default settings file...", end=" ")
  try:
    with open('Domaille/Settings.txt', 'x') as f:
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
    with open(f'Domaille/Processes/{default}', 'w') as f:
      f.write("strRecipeDescription := default recipe\n")
      f.write("intRecipeNoOfSteps := 3\n")
      f.write("intRecipeQty := 30\n")
      f.write("intRecipeReworkStep := 1\n")

    with open(f'Domaille/Processes/Steps/{default}.001', 'w') as f:
      f.write("rRecipeStepTime := 25\n")
      f.write("rRecipeStepSpeed := 110\n")
      f.write("rRecipeStepSpeedRamp := 1\n")
      f.write("rRecipeStepPressure := 15\n")
      f.write("rRecipeStepPressureRamp := 1\n")
      f.write("rRecipeStepFCI := 5\n")
      f.write("rRecipeStepLowerSpeedLimit := 10\n")
      f.write("rRecipeStepUpperSpeedLimit := 10\n")
      f.write("rRecipeStepLowerPressureLimit := 0.5\n")
      f.write("rRecipeStepUpperPressureLimit := 0.5\n")
      f.write("rRecipeStepFixtureWeight := 0\n")
      f.write("intRecipeStepOpCode := 300\n")
      f.write("strRecipeStepFilm := Brown 5um\n")
      f.write("strRecipeStepLubricant := DI Water\n")
      f.write("strRecipeStepPad := 70 Duro Violet\n")
      f.write("strRecipeStepDescription1 := Rough Polish\n")
      f.write("strRecipeStepDescription2 := Geometry\n")
      f.write("rRecipeStepSpeedRampDn := 1\n")
      f.write("rRecipeStepPressureRampDn := 1\n")

    with open(f'Domaille/Processes/Steps/{default}.002', 'w') as f:
      f.write("rRecipeStepTime := 35\n")
      f.write("rRecipeStepSpeed := 110\n")
      f.write("rRecipeStepSpeedRamp := 1\n")
      f.write("rRecipeStepPressure := 12\n")
      f.write("rRecipeStepPressureRamp := 1\n")
      f.write("rRecipeStepFCI := 5\n")
      f.write("rRecipeStepLowerSpeedLimit := 10\n")
      f.write("rRecipeStepUpperSpeedLimit := 10\n")
      f.write("rRecipeStepLowerPressureLimit := 0.5\n")
      f.write("rRecipeStepUpperPressureLimit := 0.5\n")
      f.write("rRecipeStepFixtureWeight := 0\n")
      f.write("intRecipeStepOpCode := 300\n")
      f.write("strRecipeStepFilm := Purple 1um\n")
      f.write("strRecipeStepLubricant := DI Water\n")
      f.write("strRecipeStepPad := 70 Duro Violet\n")
      f.write("strRecipeStepDescription1 := Medium Polish\n")
      f.write("rRecipeStepSpeedRampDn := 1\n")
      f.write("rRecipeStepPressureRampDn := 1\n")


    with open(f'Domaille/Processes/Steps/{default}.003', 'w') as f:
      f.write("rRecipeStepTime := 35\n")
      f.write("rRecipeStepSpeed := 110\n")
      f.write("rRecipeStepSpeedRamp := 1\n")
      f.write("rRecipeStepPressure := 12\n")
      f.write("rRecipeStepPressureRamp := 1\n")
      f.write("rRecipeStepFCI := 3\n")
      f.write("rRecipeStepLowerSpeedLimit := 10\n")
      f.write("rRecipeStepUpperSpeedLimit := 10\n")
      f.write("rRecipeStepLowerPressureLimit := 0.5\n")
      f.write("rRecipeStepUpperPressureLimit := 0.5\n")
      f.write("rRecipeStepFixtureWeight := 0\n")
      f.write("intRecipeStepOpCode := 300\n")
      f.write("strRecipeStepFilm := Clear FOS-22\n")
      f.write("strRecipeStepLubricant := DI Water\n")
      f.write("strRecipeStepPad := 70 Duro Violet\n")
      f.write("strRecipeStepDescription1 := Final Polish\n")
      f.write("rRecipeStepSpeedRampDn := 1\n")
      f.write("rRecipeStepPressureRampDn := 1\n")


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
    recipeList = os.listdir("Domaille/Processes/")
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
    with open(f'Domaille/Processes/{recipeName}', 'r') as f:
      recipe=f.readlines()
  except Exception as e:
    print('ERROR', e)
    return

  cwd = os.getcwd()
  print(f'{cwd}\\Domaille\\Processes\\{recipeName}')
  for line in recipe:
    print(line, end="")
    # get the number of steps from the recipe as we go through it:
    if line.startswith("intRecipeNoOfSteps"):
      recipeNoOfSteps = int(line.strip()[-1:]) # this will bug if >=10 steps!

  # Get each step of the recipe:  
  print()
  for step in range(1, recipeNoOfSteps+1):
    print(f"STEP #{step}:")
    try:
      with open(f'Domaille/Processes/Steps/default.00{step}', 'r') as f:
        print(f.read())
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
  if os.path.exists(f"Domaille/Processes/{recipeName}"):
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
    with open(f'Domaille/Processes/{recipeName}', 'w') as f:
      f.write(f"strRecipeDescription := {recipeName}\n")
      f.write(f"intRecipeNoOfSteps := {steps}\n")
      f.write(f"intRecipeQty := {qty}\n")
      f.write(f"intRecipeReworkStep := 1\n")
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
      with open(f'Domaille/Processes/Steps/{recipeName}.00{step}', 'w') as f:
        f.write(f"rRecipeStepTime := {time}\n")
        f.write("rRecipeStepSpeed := 110\n")
        f.write("rRecipeStepSpeedRamp := 1\n")
        f.write(f"rRecipeStepPressure := {pressure}\n")
        f.write("rRecipeStepPressureRamp := 1\n")
        f.write("rRecipeStepFCI := 5\n")
        f.write("rRecipeStepSpeedRampDn := 1\n")
        f.write("rRecipeStepPressureRampDn := 1\n")
    except Exception as e:
      print(f"ERROR while writing recipe step {step} to file: {e}.")
      raise e
    
  print(f"Recipe {recipeName} generated with {steps} steps.")
  print(f"You may copy Domaille folder from {os.getcwd()} to flash drive.")
       

def main():
  print()
  print("Offline Recipe Generator for Domaille APM-HDC-5320\n")
  # check for file structure
  if os.path.isdir('Domaille/Processes/Steps'):
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
