from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent


def test_all_yaml_configuration_files_are_readable():
    for name in ("sources", "categories", "interests", "watchlist", "settings"):
        data = yaml.safe_load((ROOT / "config" / f"{name}.yaml").read_text(encoding="utf-8"))
        assert isinstance(data, dict) and data


def test_workflow_keeps_daily_schedule_and_quality_gate():
    workflow = (ROOT / ".github" / "workflows" / "daily_report.yml").read_text(
        encoding="utf-8"
    )
    assert 'cron: "30 21 * * *"' in workflow
    assert "pytest -q" in workflow
    assert "python src/main.py" in workflow
    assert "actions/upload-artifact@v7" in workflow
