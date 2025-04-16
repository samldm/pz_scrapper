import yaml
import requests
import re
from time import sleep
from typing import List, Dict
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Exporter for mods and maps from a Steam collection.")
    parser.add_argument('--config', default='config.yml', help="Path to the configuration file")
    parser.add_argument('--collection', default='default', help="Collection configuration name (key in config.yml)")
    parser.add_argument('--output', default='output.txt', help="Output file name")
    return parser.parse_args()

def load_config(config_file: str = 'config.yml') -> dict:
    """Loads the YAML configuration file."""
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            if config is None:
                raise ValueError("Empty or invalid config file.")
            return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    except yaml.YAMLError as e:
        raise Exception(f"YAML parsing error: {e}")
    except Exception as e:
        raise Exception(f"Unknown error loading config: {e}")

def get_collection_mod_ids(collection_id: str) -> List[str]:
    """Retrieves the mod IDs from a Steam Workshop collection."""
    try:
        url = "https://api.steampowered.com/ISteamRemoteStorage/GetCollectionDetails/v1/"
        payload = {
            'collectioncount': 1,
            'publishedfileids[0]': collection_id
        }

        response = requests.post(url, data=payload)
        response.raise_for_status()

        data = response.json()
        children = data['response']['collectiondetails'][0].get('children', [])
        return [child['publishedfileid'] for child in children if child.get('filetype') == 0]
    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP request error while retrieving mods: {e}")
    except KeyError:
        raise Exception("The API response does not contain the expected data.")
    except Exception as e:
        raise Exception(f"Unknown error retrieving mod IDs: {e}")

def select_user_choice(items: List[str], item_type: str) -> List[str]:
    """Allows the user to choose one or more items from a list."""
    if not items:
        print(f"No {item_type} found.")
        return []

    print(f"\nSelect the {item_type}s you want to add (separate indices with commas):")
    for idx, item in enumerate(items):
        print(f"{idx + 1}. {item}")

    selected = input(f"\nSelect one or more {item_type}s (e.g., 1,2 or 'all' to select all): ").strip()

    if selected.lower() == 'all':
        return items

    try:
        indices = [int(i.strip()) - 1 for i in selected.split(',')]
        return [items[i] for i in indices if 0 <= i < len(items)]
    except ValueError:
        print("\nInvalid input. Please enter valid indices.")
        return select_user_choice(items, item_type)

def remove_duplicates(items: List[str]) -> List[str]:
    """Removes duplicates while preserving the order of appearance."""
    seen = set()
    return [x for x in items if not (x in seen or seen.add(x))]

def get_mod_info(file: dict) -> Dict[str, List[str]]:
    """Extracts mod and map information from a Workshop file description."""
    try:
        description = file.get('description', '')

        mod_ids = re.findall(r'Mod ID:\s*(.+)', description, re.IGNORECASE)
        map_ids = re.findall(r'Map Folder:\s*(.+)', description, re.IGNORECASE)

        mod_ids = remove_duplicates([mod_id.strip().replace('\r', '').replace('\n', '').replace('[/hr]', '') for mod_id in mod_ids])
        map_ids = remove_duplicates([map_id.strip().replace('\r', '').replace('\n', '').replace('[/hr]', '') for map_id in map_ids])

        if len(mod_ids) > 1:
            print("-----")
            print(f"\nMultiple Mod IDs found for {file.get('title')}, please make a choice.")
            print(f"Mod link: https://steamcommunity.com/sharedfiles/filedetails/?id={file.get('publishedfileid')}")
            mod_ids = select_user_choice(mod_ids, "Mod ID")

        if len(map_ids) > 1:
            print("-----")
            print(f"\nMultiple Map Folders found for {file.get('title')}, please make a choice.")
            print(f"Mod link: https://steamcommunity.com/sharedfiles/filedetails/?id={file.get('publishedfileid')}")
            map_ids = select_user_choice(map_ids, "Map Folder")

        return {
            'title': file.get('title'),
            'workshop_id': file['publishedfileid'],
            'mod_ids': mod_ids,
            'map_ids': map_ids
        }
    except Exception as e:
        raise Exception(f"Error extracting mod information: {e}")

def get_mods_data(mod_ids: List[str], batch_size: int = 100, delay: float = 0.5) -> List[dict]:
    """Fetches mod data in batches from the Steam API."""
    try:
        url = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
        all_mods = []

        for i in range(0, len(mod_ids), batch_size):
            batch = mod_ids[i:i + batch_size]
            payload = {'itemcount': len(batch)}
            for idx, mod_id in enumerate(batch):
                payload[f'publishedfileids[{idx}]'] = mod_id

            response = requests.post(url, data=payload)
            response.raise_for_status()
            data = response.json()

            for file in data['response']['publishedfiledetails']:
                all_mods.append(get_mod_info(file))

            sleep(delay)

        return all_mods
    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP request error while retrieving mods: {e}")
    except Exception as e:
        raise Exception(f"Unknown error retrieving mod data: {e}")

def export_to_file(workshop_ids: List[str], mod_ids: List[str], maps: List[str], filename: str = 'output.txt') -> None:
    """Exports data to a text file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"WorkshopItems={';'.join(workshop_ids)}\n")
            f.write(f"Mods={';'.join(mod_ids)}\n")
            f.write(f"Map={';'.join(maps)}\n")
        print(f"\n✅ File '{filename}' successfully generated.")
    except Exception as e:
        raise Exception(f"Error exporting to file: {e}")

def ask_yes_no(question: str, default: str = "yes") -> bool:
    """
    Asks the user a yes/no question.
    """
    valid = {"yes": True, "y": True, "no": False, "n": False}

    prompt = {
        None: " [y/n] ",
        "yes": " [Y/n] ",
        "no": " [y/N] "
    }[default]

    while True:
        choice = input(question + prompt).strip().lower()
        if choice == '' and default:
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please answer 'yes' or 'no' (or 'y' / 'n').")

if __name__ == '__main__':
    try:
        args = parse_args()
        config = load_config(args.config)

        collection_id = str(config['collections'][args.collection])

        mods = get_collection_mod_ids(collection_id)
        mods_data = get_mods_data(mods)

        workshop_ids: List[str] = []
        mod_ids: List[str] = []
        maps: List[str] = []

        for mod in mods_data:
            workshop_ids.append(mod['workshop_id'])
            mod_ids.extend(mod['mod_ids'])
            maps.extend(mod['map_ids'])

        if ask_yes_no("Do you want to add 'Muldraugh, KY' to the Map Folders? (vanilla map)"):
            maps.append("Muldraugh, KY")

        export_to_file(workshop_ids, mod_ids, maps, args.output)

    except Exception as e:
        print(f"Error: {e}")
