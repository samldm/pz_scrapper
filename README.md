# PZ_SCRAPPER

A Python script to export mod and map information from a Steam Workshop collection for configuring Project Zomboid server mods.

### Features:
- Retrieves all mods from a Workshop collection.
- Automatically extracts Mod IDs and Map Folders from the file descriptions.
- Allows the user to manually select the correct IDs in case of ambiguity.
- Generates an output file containing Workshop IDs, Mod IDs, and Map Folders.

**Make sure to set your collection ID in the config.yml file. No Steam API key is required.**

### Usage:

**By default, running the script with no parameters will scrape the default collection. You can specify additional collections in the config.yml file if needed.**

For more informations about parameters, run:
```
python main.py --help
```
