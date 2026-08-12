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
python generate.py <mod_name> <mod_version>
```

This will generate a mod in `mods/<mod_name>`, you can copy this to your `Server/Admin/Mods` folder to run it.

You can also directly make it generate the mod in your mods folder by adding the `-o` flag:

```bash
python generate.py <mod_name> <mod_version> -o "<path_to_documents_bf3>/Server/Admin/Mods"`
```

## Per-instance EBX overrides

A save may carry an `ebx` section alongside `header` and `data`:

```json
{
  "header": { ... },
  "data":   [ ... ],
  "ebx":    [ { "objectGuid": "<editor guid>", "name": "...", "partition": { ...serialized EBX... } } ]
}
```

Each entry is the *cloned blueprint* of one instance whose EBX fields were edited in MapEditor.
Editing a field clones that instance's blueprint so the change isolates to it, and the clone only
exists at runtime — so it travels inside the save or it is lost, and the baked level silently falls
back to the stock blueprint.

The generator emits each one as its own partition next to the level partition and repoints **only
that instance's** `ReferenceObjectData` at it. Sibling instances of the same prefab are untouched
and keep resolving the stock blueprint, which is what makes the override per-instance.

Saves with no `ebx` section bake exactly as before.

**Not yet supported:** blueprint-wide overrides (MapEditor's *Apply to Blueprint*). Those arrive
with an empty `objectGuid` and are skipped with a warning. Making them work needs the modified
partition emitted under the **original** partition name so it shadows the stock one — repointing
cannot express it, because the level also contains vanilla `ReferenceObjectData`s that this
generator never emits and therefore cannot repoint.
