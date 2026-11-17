"""Тесты интерфейса командной строки saltcav."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from saltcav.cli import main

ROOT = Path(__file__).resolve().parents[1]
CFG_CHANNEL = ROOT / "configs" / "channel.yaml"


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["version"]) == 0
    out = capsys.readouterr().out
    assert "saltcav-lab" in out


def test_cli_check_success(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", str(CFG_CHANNEL)]) == 0
    out = capsys.readouterr().out
    assert "успешно проверена" in out


def test_cli_check_not_found(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", "non_existent.yaml"]) == 1
    err = capsys.readouterr().err
    assert "не найден" in err


def test_cli_run_and_save_csv(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out_csv = tmp_path / "result.csv"
    code = main(["run", str(CFG_CHANNEL), "--out", str(out_csv)])
    assert code == 0
    captured = capsys.readouterr().out
    assert "Результаты расчёта" in captured
    assert "Итоговый объём" in captured
    assert out_csv.exists()
    content = out_csv.read_text(encoding="utf-8")
    assert "time_s,volume_cm3,outlet_c_g_l,dissolved_g" in content
