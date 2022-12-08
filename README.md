# LvlLoaderBundleGen
Generates custom bundles from MapEditor save files to use in [CustomLevelLoader](https://github.com/BF3RM/CustomLevelLoader).

## Pre-requisites
- [Python](https://www.python.org/downloads/)
- Rime, a Frostbite editor, with a Windows environment variable for the exe (RimeREPL). You can download the latest version of Rime [here](https://i.nofate.me/36goiuRT0V1fZWd.zip).

## Usage
- Save files generated with MapEditor can be put in the `/in/map_saves` folder in json files (with the `.json` extension). The file names don't matter. 

- If you want to reuse a mapsave for more than just that gamemode, include a `gamemode_map.json` file that takes the original map+gamemode as a key and as the value an array with the supported maps+gamemodes, like so:

```json
{
	"XP1_002/ConquestLarge0": [
		"XP1_002/ConquestSmall0",
		"XP1_002/TeamDeathMatchC0"
	]
}
```

- Run the `run.bat` file. This will generate the following:
	- `/out/sb/`: This folder contains all the custom bundles. This whole folder has to be copied to the root folder of CustomLevelLoader mod, so it should look like `../Server/Admin/Mods/CustomLevelLoader/sb/`
	- `/out/lua/`: copy the contents of this folder to `CustomLevelLoader/ext/Shared/Levels/`
	- `/out/superbundles.json`: Copy the content and paste it in LevelLoader `mod.json` file, inside the `Superbundles field`. Should look like the following:

	![Image](https://user-images.githubusercontent.com/7466799/196763314-8da25ff9-a394-492e-91cf-c45e3b7d1740.png)

Finally, simply run CustomLevelLoader and the modified levels will be loaded automatically.
