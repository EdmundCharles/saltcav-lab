"""saltcav-lab: Моделирование выщелачивания соляного канала и полуканала в блоке NaCl."""

__version__ = "2.0.0"

from saltcav.core.lab_config import LabConfig, LabStage, load_lab_config
from saltcav.leaching.axisym import LabResult, simulate_lab
from saltcav.leaching.section import SectionResult, simulate_section

__all__ = [
    "LabConfig",
    "LabStage",
    "load_lab_config",
    "simulate_section",
    "simulate_lab",
    "SectionResult",
    "LabResult",
]
