# Antigravity MounRiver Setup

This folder contains MounRiver SDK files and project templates for CH572 and CH592 chips.

## Flashing Note
- **Automatic flashing (`make` or `make flash`)**: 
  - Uses `minichlink` (local tool).
  - **IMPORTANT**: This requires the device to use the **WinUSB** driver. If you have the default WCH driver installed (installed by MounRiver), this will fail with an error.
- **WCHISPTool GUI (`make openisp`)**:
  - If `make flash` fails due to driver issues, it will automatically launch the official WCHISPTool GUI.
  - **Auto-Flash Setup**: In the GUI, configure your chip settings once and click **"Save UI Config"**. Save the file as `isp_config.ini` in your project folder (e.g., inside `templates/ch592`). 
  - On subsequent runs, `make` will detect this file and use it to automatically flash the device via the WCHISPTool CLI, without opening the GUI.

## Structure
- `sdk/`: Contains the SDK files (Startup, Linker, StdPeriphDriver) for CH572 and CH592.
  - These were copied from the original `mounriver` folder.
- `templates/`: Contains basic project templates.
  - `ch572/`: Template for CH572.
  - `ch592/`: Template for CH592.

## How to use
1. Copy one of the template folders to a new location (or work directly in it).
2. Edit `src/Main.c`.
3. Run `make` to build and automatically attempt to flash.
   - Requires `riscv-none-embed-gcc` (compilation) and `minichlink` (flashing) in your PATH.
   - The flashing process will retry up to 10 times (1-second interval) to allow time for the device to be detected.
   - Generates `obj/firmware.hex` and `obj/firmware.bin`.
4. Run `make flash` to explicitly flash (also uses the retry mechanism).

## Notes
- The Makefiles are set up to reference the `../../sdk` directory. If you move the project template outside of this folder depth, you will need to update the paths in the Makefile.
