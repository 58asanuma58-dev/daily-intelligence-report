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


def load_summary_cache(history_dir: Path, maximum_files: int = 7) -> dict[str, str]:
    """最近の正常な履歴から、AI生成済み要約を記事IDごとに再利用する。"""
    cache: dict[str, str] = {}
    if not history_dir.exists():
        return cache
    for path in sorted(history_dir.glob("*.json"), reverse=True)[:maximum_files]:
        try:
            data = load_json(path)
        except (OSError, json.JSONDecodeError) as error:
            LOGGER.warning("要約キャッシュを読み込めません: %s (%s)", path, error)
            continue
        for article in data.get("articles", []) if isinstance(data, dict) else []:
            article_id = str(article.get("id", ""))
            summary = str(article.get("summary", ""))
            if article_id and summary and article.get("summary_method") == "copilot":
                cache.setdefault(article_id, summary)
    return cache
