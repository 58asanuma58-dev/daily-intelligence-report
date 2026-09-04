"""複数のPhaseで共有する、ログと設定読み込みの小さな機能。"""

import logging
from pathlib import Path
import sys
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    """YAMLを辞書として読み込み、空や異常な形式を検出する。"""
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise ValueError(f"YAMLの最上位は辞書形式にしてください: {path}")
    return data


def setup_logging(log_path: Path) -> logging.Logger:
    """ターミナルと日付別ファイルの両方へログを出す。"""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s", datefmt="%H:%M:%S"
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger
