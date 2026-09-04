"""取得データ、処理済みデータ、履歴をJSONで安全に保存する。"""

import json
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


LOGGER = logging.getLogger(__name__)


def save_json(path: Path, data: Any) -> None:
    """途中で失敗しても壊れた本番ファイルを残しにくい方法で保存する。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as temporary_file:
        json.dump(data, temporary_file, ensure_ascii=False, indent=2)
        temporary_path = Path(temporary_file.name)
    temporary_path.replace(path)


def load_json(path: Path) -> Any:
    """UTF-8のJSONファイルを読み込む。"""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_previous_history(history_dir: Path, current_date: str) -> dict[str, Any] | None:
    """当日より前で最も新しい、正常に読める履歴を探す。"""
    if not history_dir.exists():
        return None

    candidates = sorted(
        (
            path
            for path in history_dir.glob("*.json")
            if path.stem < current_date
        ),
        reverse=True,
    )
    for path in candidates:
        try:
            data = load_json(path)
            if isinstance(data, dict) and isinstance(data.get("articles"), list):
                return data
            LOGGER.warning("履歴の形式が不正です: %s", path)
        except (OSError, json.JSONDecodeError) as error:
            LOGGER.warning("履歴を読み込めません: %s (%s)", path, error)
    return None


def previous_keywords(history: dict[str, Any] | None) -> set[str]:
    """前回履歴に登場した分類キーワードを小文字で集める。"""
    if not history:
        return set()
    return {
        str(keyword).lower()
        for article in history.get("articles", [])
        for keyword in article.get("keywords", [])
    }
