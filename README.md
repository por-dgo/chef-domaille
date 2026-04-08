# 🍳 Chef Domaille

Recipe manager for the Domaille APM-HDC-5316 and APM-HDC-5320 fiber optic polishing machines.

Chef Domaille lets you create, edit, and organize polishing recipes on your PC, then export them to a USB drive for the machine — no more editing recipes one field at a time on the machine's touchscreen.

## Getting Started

1. Download `Chef Domaille-v*.zip` from the [latest release](https://github.com/por-dgo/chef-domaille/releases/latest)
2. Extract the zip anywhere on your PC
3. Double-click **Chef Domaille.exe**
4. Your browser opens automatically to the recipe editor

A small console window will appear — this is the server powering the editor. **Leave it open** while you work. Close it when you're done.

## What You Can Do

### Create and Edit Recipes

- Set the recipe name, description, and contact quantity
- Add up to 9 polishing steps per recipe
- Configure each step: time, pressure, speed, ramp rates
- Assign consumables (film, pad, lubricant) and notes per step
- Reorder or remove steps with drag handles

### Manage Consumable Options

Expand the **Machine Settings** panel to customize the dropdown lists for Film, Pad, and Lubricant. These are the options that appear when editing a step. Add or remove entries to match what's stocked at your workstation.

### Import and Export

- **Export to USB** — Select recipes and write them to a thumb drive in the format the machine expects (`Domaille/Processes/` and `Domaille/Processes/Steps/`)
- **Import from USB** — Pull recipes from a thumb drive into your local library
- **Recipe Book (.chef)** — Export a portable bundle of recipes to share with colleagues, or import one they've shared with you

### Validation

Recipes are validated against the 5316/5320 machine profile before saving. The editor will flag values that are out of range (e.g., pressure above 16 lbs, speed beyond machine limits) so you catch problems before they reach the machine.

## Where Recipes Are Stored

Recipes live in your Windows AppData folder:

```
%APPDATA%\Chef Domaille\Domaille\
├── Settings.txt
└── Processes/
    ├── <recipe_name>
    └── Steps/
        ├── <recipe_name>.001
        ├── <recipe_name>.002
        └── ...
```

This is separate from the machine's USB folder structure. Use **Export** to copy recipes to a thumb drive.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Browser didn't open | Check the console window for the URL (e.g., `http://127.0.0.1:5000`) and open it manually |
| Port already in use | Chef Domaille automatically tries the next available port. Check the console for the actual URL |
| Recipes missing after reinstall | Your recipes are safe in `%APPDATA%\Chef Domaille` — they persist across updates |

## Documentation

- [APM-HDC-5320 Polishing Machine User Manual](docs/APM-HDC-5320-Polishing-Machine-User-Manual.pdf) — operator manual for the 5320
- [APM-HDC-5400 Polishing Machine User Manual](docs/APM-HDC-5400-Polishing-Machine-User-Manual.pdf) — operator manual for the 5400 (supplementary reference)
- [Recipe File Format](docs/recipe-format-contract.md) — detailed breakdown of the files Chef Domaille reads and writes to USB

Additional developer notes are in the [`docs/`](docs/) folder.

## License

MIT. See [LICENSE](LICENSE).
