# LvlLoaderBundleGen
Generates custom bundles from MapEditor save files to use in [CustomLevelLoader](https://github.com/BF3RM/CustomLevelLoader).

## Pre-requisites
- [Python](https://www.python.org/downloads/)
- Rime, a Frostbite editor, with a Windows environment variable for the exe (RimeREPL). You can download the latest version of Rime [here](https://i.nofate.me/36goiuRT0V1fZWd.zip).


## Usage
Save files generated with MapEditor can be put in the `/in/` folder in json files (with the `.json` extension). The file names don't matter. Run the `run.bat` file. This will generate two folders:
- `/sb/`: contains all the custom bundles. This whole folder has to be copied to the root folder of CustomLevelLoader mod, so it should look like `../Server/Admin/Mods/CustomLevelLoader/sb/`
- `/out/lua/`: it contains folders for each map with some Lua files inside. These folders have to be copied to `CustomLevelLoader/ext/Shared/Levels/`

Next, open CustomLevelLoader `mod.json` file and add the names of the superbundles. You can see their names in the Rime console output. Should look like the following:

![imagen](https://user-images.githubusercontent.com/7466799/196763314-8da25ff9-a394-492e-91cf-c45e3b7d1740.png)

Finally, simply run CustomLevelLoader and the modified levels will be loaded automatically.
