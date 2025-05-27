import os
import yaml

def load_config(path="config.yaml"):
    project_root = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(project_root, path)
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
