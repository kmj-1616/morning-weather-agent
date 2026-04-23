import os
import yaml
from pathlib import Path


class ConfigError(Exception):
    pass


REQUIRED_KEYS = [
    ("api_keys", "kma_service_key"),
    ("api_keys", "airkorea_service_key"),
    ("api_keys", "anthropic_api_key"),
    ("kakao", "client_id"),
    ("kakao", "redirect_uri"),
]


def load_config(path: str = None) -> dict:
    if path is None:
        path = Path(__file__).parent.parent / "config.yaml"
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    _validate(config)
    config["_path"] = str(path)
    return config


def save_config(config: dict, path: str = None) -> None:
    if path is None:
        path = config.get("_path") or str(Path(__file__).parent.parent / "config.yaml")
    data = {k: v for k, v in config.items() if not k.startswith("_")}
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    os.replace(tmp_path, path)


def _validate(config: dict) -> None:
    for section, key in REQUIRED_KEYS:
        if not config.get(section, {}).get(key):
            raise ConfigError(f"config.yaml에 필수 항목이 없습니다: {section}.{key}")
    if not config.get("locations"):
        raise ConfigError("config.yaml에 locations 항목이 없습니다.")
