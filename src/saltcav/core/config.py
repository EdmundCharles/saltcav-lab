"""Конфигурация saltcav: прямое перенаправление на lab_config."""

from saltcav.core.lab_config import LabConfig, LabStage, _Strict, load_lab_config

__all__ = ["LabConfig", "LabStage", "_Strict", "load_lab_config"]
