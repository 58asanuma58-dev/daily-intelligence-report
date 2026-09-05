from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent


def test_all_yaml_configuration_files_are_readable():
    for name in ("sources", "categories", "interests", "watchlist", "settings"):
        data = yaml.safe_load((ROOT / "config" / f"{name}.yaml").read_text(encoding="utf-8"))
        assert isinstance(data, dict) and data


def test_requested_twelve_sources_are_enabled_and_unique():
    source_config = yaml.safe_load(
        (ROOT / "config" / "sources.yaml").read_text(encoding="utf-8")
    )
    sources = source_config["sources"]
    expected_names = [
        "JMA regular",
        "JMA extra",
        "OpenAI",
        "Google DeepMind",
        "Google AI",
        "ITmedia AI＋",
        "国土交通省プレスリリース",
        "日本銀行",
        "西日本REINS",
        "財務省",
        "e-Gov 意見募集全件",
        "e-Gov 結果公示全件",
    ]

    assert [source["name"] for source in sources] == expected_names
    assert all(source["enabled"] for source in sources)
    assert len({source["url"] for source in sources}) == 12


def test_every_source_has_a_default_category():
    source_config = yaml.safe_load(
        (ROOT / "config" / "sources.yaml").read_text(encoding="utf-8")
    )
    category_config = yaml.safe_load(
        (ROOT / "config" / "categories.yaml").read_text(encoding="utf-8")
    )

    source_names = {source["name"] for source in source_config["sources"]}
    assert source_names == set(category_config["source_defaults"])


def test_workflow_keeps_daily_schedule_and_quality_gate():
    workflow = (ROOT / ".github" / "workflows" / "daily_report.yml").read_text(
        encoding="utf-8"
    )
    assert 'cron: "30 21 * * *"' in workflow
    assert "pytest -q" in workflow
    assert "python src/main.py" in workflow
    assert "actions/upload-artifact@v7" in workflow
