import os
import sys
import json
import yaml
import tempfile

# Ensure the root and 'app' directory are on PYTHONPATH so that modules like 'my_tools'
# (located at app/my_tools.py) can be imported when this loader runs as a standalone
# script.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
APP_DIR = os.path.join(ROOT_DIR, "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from app import db_utils

# Path to the YAML file shipped with the repo
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "crew_config.yaml")


def _yaml_entities_to_db_entities(yaml_data):
    """Ensure the YAML data is a list of {id, entity_type, data} dicts.
    The exporter already writes that exact schema.  If users hand-edit the file and
    turn it into a dict keyed by entity_type, we convert it back to the list shape."""
    if isinstance(yaml_data, list):
        return yaml_data

    # If the YAML root is a mapping, flatten it into a list
    flat = []
    for entity_type, items in yaml_data.items():
        if not isinstance(items, list):
            continue
        for item in items:
            # Older hand-written examples may omit the entity_type field
            etype = item.get("entity_type", entity_type)
            entity_id = item.get("id")
            data = item.get("data", {})
            if entity_id is None:
                # Skip items without an explicit id – Studio will regenerate ids later
                continue
            flat.append({"id": entity_id, "entity_type": etype, "data": data})
    return flat


def load_config_to_db(config_path: str | None = None):
    """Import entities from a YAML file into the sqlite/Postgres DB.

    If the DB already has an entity with the same id, the YAML version wins
    (just like db_utils.import_from_json does)."""
    path = config_path or CONFIG_FILE
    if not os.path.exists(path):
        # Nothing to load – this is not an error if the user hasn't created the file yet.
        print(f"Config loader: '{path}' not found – skipping YAML import.")
        return

    try:
        with open(path, "r", encoding="utf-8") as fp:
            yaml_data = yaml.safe_load(fp) or []
    except Exception as e:
        print(f"Config loader: failed to parse YAML – {e}")
        return

    entities = _yaml_entities_to_db_entities(yaml_data)
    if not entities:
        print("Config loader: no entities found in YAML – nothing to import.")
        return

    # db_utils.import_from_json expects a file path; create a temp file.
    try:
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tmp:
            json.dump(entities, tmp)
            tmp_path = tmp.name
        db_utils.import_from_json(tmp_path)
        print(f"Config loader: imported {len(entities)} entities from YAML into DB.")
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def export_db_to_yaml(out_path: str | None = None):
    """Dump current DB entities to a YAML file so it can be version-controlled."""
    path = out_path or CONFIG_FILE
    # Write to a temporary JSON first, then convert to YAML for human readability.
    try:
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tmp:
            tmp_json_path = tmp.name
        db_utils.export_to_json(tmp_json_path)
        with open(tmp_json_path, "r", encoding="utf-8") as fp:
            entities = json.load(fp)
    finally:
        try:
            os.remove(tmp_json_path)
        except Exception:
            pass

    # Now dump to YAML
    with open(path, "w", encoding="utf-8") as fp:
        yaml.dump(entities, fp, sort_keys=False)
    print(f"Config loader: exported {len(entities)} entities to '{path}'.")


if __name__ == "__main__":
    load_config_to_db() 