"""Конфигурация лабораторной установки: канал в блоке NaCl, режим насоса, глубина.

Строгая схема: неизвестные поля отвергаются, значения валидируются по физическим диапазонам.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Strict(BaseModel):
    """Базовая модель со строгой валидацией: запрещены лишние поля, объект неизменяем."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class LabStage(_Strict):
    """Ступень режима насоса."""

    duration_h: Annotated[float, Field(gt=0, description="Длительность ступени, ч")]
    flow_ml_min: Annotated[float, Field(gt=0, description="Расход насоса, мл/мин")]
    inlet_saturation: Annotated[
        float, Field(ge=0, le=1, description="Насыщение на входе, доля C_s; 0 — дистиллят")
    ] = 0.0


class LabConfig(_Strict):
    """Параметры установки. Всё, что можно поменять в опыте, задаётся здесь."""

    name: Annotated[str, Field(description="Название опыта")] = "lab-channel"
    setup: Annotated[
        Literal["channel", "window"],
        Field(description="channel — канал в целом блоке; window — полуканал у вертикального "
                          "окна из оргстекла (половина каверны, видна через стекло)"),
    ] = "channel"
    length_mm: Annotated[float, Field(gt=0, description="Длина канала (блока вдоль оси), мм")]
    diameter_mm: Annotated[float, Field(gt=0, description="Начальный диаметр канала, мм")]
    max_radius_mm: Annotated[
        float | None,
        Field(gt=0, description="От оси канала до ближайшей грани блока, мм; расчёт "
                                "останавливается, когда канал до неё дорастёт"),
    ] = None
    temperature_c: Annotated[
        float, Field(ge=0, le=100, description="Температура, °C (при заданном геотермическом "
                                               "градиенте — температура на поверхности)"),
    ] = 20.0
    salt_density_kg_m3: Annotated[float, Field(gt=0, description="Плотность соли блока, кг/м³")] = (
        2160.0
    )
    depth_m: Annotated[
        float, Field(ge=0, le=2800, description="Глубина установки от поверхности, м: вода "
                                                "подаётся насосом с поверхности по одной трубке, "
                                                "рассол поднимается на поверхность по другой "
                                                "(0 — установка на поверхности)"),
    ] = 0.0
    tube_diameter_mm: Annotated[
        float, Field(gt=0, description="Внутренний диаметр подающей и отводящей трубок, мм "
                                       "(при глубине > 0)"),
    ] = 4.0
    geothermal_gradient_c_per_100m: Annotated[
        float | None,
        Field(ge=0, description="Геотермический градиент, °C на 100 м: температура блока и "
                                "рассола на глубине = температура на поверхности + "
                                "градиент·глубина. Не задан — температура одна и та же"),
    ] = None
    rock_density_kg_m3: Annotated[
        float, Field(gt=0, description="Средняя плотность пород над установкой, кг/м³ "
                                       "(горное давление — для оценки ползучести соли)"),
    ] = 2300.0
    model: Annotated[
        Literal["section", "axisym"],
        Field(description="section — сечение r(θ, x) с конвекцией и расслоением; "
                          "axisym — простая модель с круглым сечением r(x)"),
    ] = "section"
    natural_convection: Annotated[
        bool, Field(description="Учитывать свободную конвекцию и расслоение рассола")
    ] = True
    sh_mult: Annotated[
        float, Field(gt=0, description="Калибровочный множитель массоотдачи (по опытам)")
    ] = 1.0
    roof_mult: Annotated[
        float, Field(ge=0, description="Множитель массоотдачи свободной конвекции у потолка")
    ] = 1.0
    wall_mult: Annotated[
        float, Field(ge=0, description="Множитель массоотдачи свободной конвекции у боковых стенок")
    ] = 1.0
    ri_crit: Annotated[
        float, Field(gt=0, description="Gr/Re², выше которого рассол в сечении расслаивается")
    ] = 1.0
    k_surface_m_s: Annotated[
        float | None,
        Field(gt=0, description="Константа скорости реакции на поверхности соли, м/с: поток "
                                "j = (C_s − c)/(1/k_массоотдачи + 1/k_реакции). Не задана — "
                                "растворение ограничено массоотдачей (транспортный контроль)"),
    ] = None
    salt_conductivity_w_mk: Annotated[
        float, Field(gt=0, description="Теплопроводность соли блока, Вт/(м·К), для оценки "
                                       "охлаждения стенки теплотой растворения"),
    ] = 6.0
    n_cells: Annotated[int, Field(ge=4, description="Число ячеек вдоль оси")] = 100
    n_theta: Annotated[int, Field(ge=4, description="Секторов по углу на половину сечения")] = 18
    output_every_min: Annotated[float, Field(gt=0, description="Шаг записи, мин")] = 10.0
    cfl: Annotated[float, Field(gt=0, le=1, description="Запас по условию Куранта")] = 0.5
    stages: Annotated[list[LabStage], Field(min_length=1, description="Режим насоса")]

    @model_validator(mode="after")
    def _check_model(self) -> LabConfig:
        if self.model == "axisym" and (self.setup == "window" or self.natural_convection):
            raise ValueError("model: axisym — только setup: channel и natural_convection: false")
        if self.model == "axisym" and self.depth_m > 0:
            raise ValueError("model: axisym — только для установки на поверхности (depth_m: 0)")
        if self.temperature_at_depth > 100:
            raise ValueError("температура на глубине выше 100 °C — вне таблиц свойств рассола")
        return self

    @property
    def temperature_at_depth(self) -> float:
        """Температура блока и рассола на глубине установки, °C."""
        grad = self.geothermal_gradient_c_per_100m or 0.0
        return self.temperature_c + grad * self.depth_m / 100.0


def load_lab_config(path: str | Path) -> LabConfig:
    with open(path, encoding="utf-8") as f:
        return LabConfig.model_validate(yaml.safe_load(f))
