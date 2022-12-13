# LevelLoaderGen

Generates a level loader mod from MapEditor save files.

## Pre-requisites

-   [Python](https://www.python.org/downloads/)

## Usage

Save files generated with MapEditor can be put in the `/in/map_saves` folder in json files (with the `.json` extension). The file names don't matter.

If you want to reuse a mapsave for more than just that gamemode, include a `gamemode_map.json` file that takes the original map+gamemode as a key and as the value an array with the supported maps+gamemodes, like so:

```json
{
	"XP1_002/ConquestLarge0": [
		"XP1_002/ConquestSmall0",
		"XP1_002/TeamDeathMatchC0"
	]
}
```

### Generating the mod

Generating the mod is fairly simple, just run:

```bash
python main.py <mod_name> <mod_version>
```

This will generate a mod in `mods/<mod_name>`, you can copy this to your `Server/Admin/Mods` folder to run it.

You can also directly make it generate the mod in your mods folder by adding the `-o` flag:

```bash
python generate.py <mod_name> <mod_version> -o "<path_to_documents_bf3>/Server/Admin/Mods"`
```
