"""Командная строка saltcav: запуск расчёта, проверка конфигурации и веб-сервер.

Команды:
  saltcav run config.yaml [--out result.csv]   Запуск симуляции выщелачивания
  saltcav web [--port 8080]                   Запуск веб-визуализатора
  saltcav check config.yaml                   Проверка валидности YAML-конфигурации
  saltcav version                             Версия программы
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from saltcav import __version__
from saltcav.core.lab_config import LabConfig, load_lab_config


def _cmd_check(args: argparse.Namespace) -> int:
    path = Path(args.config)
    if not path.exists():
        print(f"Ошибка: файл конфигурации не найден: {path}", file=sys.stderr)
        return 1
    try:
        cfg = load_lab_config(path)
        print(f"Конфигурация '{cfg.name}' успешно проверена:")
        print(f"  Установка:      {cfg.setup}")
        print(f"  Модель:         {cfg.model} (конвекция: {cfg.natural_convection})")
        print(f"  Длина / диаметр:{cfg.length_mm} мм / {cfg.diameter_mm} мм")
        print(f"  Число ступеней: {len(cfg.stages)}")
        print(f"  Сетка:          {cfg.n_cells} ячеек вдоль оси, {cfg.n_theta} секторов")
        return 0
    except Exception as e:
        print(f"Ошибка валидации конфигурации:\n{e}", file=sys.stderr)
        return 1


def _cmd_run(args: argparse.Namespace) -> int:
    path = Path(args.config)
    if not path.exists():
        print(f"Ошибка: файл конфигурации не найден: {path}", file=sys.stderr)
        return 1

    try:
        cfg = load_lab_config(path)
    except Exception as e:
        print(f"Ошибка загрузки конфигурации: {e}", file=sys.stderr)
        return 1

    print(f"Запуск симуляции: {cfg.name} (модель: {cfg.model}, установка: {cfg.setup})")
    t0 = time.time()

    if cfg.model == "axisym":
        from saltcav.leaching.axisym import simulate_lab
        res = simulate_lab(cfg)
        final_vol_cm3 = res.volume[-1] * 1e6
        max_r_mm = res.radius[-1].max() * 1e3
        dissolved_g = res.dissolved[-1] * 1e3
        c_out_g_l = res.outlet_concentration[-1]
    else:
        from saltcav.leaching.section import simulate_section
        res = simulate_section(cfg)
        final_vol_cm3 = res.volume[-1] * 1e6
        max_r_mm = res.radius[-1].max() * 1e3
        dissolved_g = res.dissolved[-1] * 1e3
        c_out_g_l = res.outlet_concentration[-1]

    elapsed = time.time() - t0
    print(f"\n--- Результаты расчёта (время вычисления: {elapsed:.2f} с) ---")
    print(f"  Шагов по времени:        {len(res.times)}")
    print(f"  Итоговый объём:          {final_vol_cm3:.2f} см³")
    print(f"  Максимальный радиус:     {max_r_mm:.2f} мм")
    print(f"  Растворено соли:         {dissolved_g:.2f} г")
    print(f"  Концентрация на выходе:  {c_out_g_l:.2f} г/л (C_s = {res.c_sat:.2f} г/л)")

    if args.out:
        out_path = Path(args.out)
        import csv
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["time_s", "volume_cm3", "outlet_c_g_l", "dissolved_g"])
            for t, v, c, m in zip(res.times, res.volume, res.outlet_concentration, res.dissolved):
                writer.writerow([round(t, 2), round(v * 1e6, 3), round(c, 2), round(m * 1e3, 2)])
        print(f"Результаты сохранены в: {out_path}")

    return 0


def _cmd_web(args: argparse.Namespace) -> int:
    from saltcav.web.server import launch_server
    launch_server(host=args.host, port=args.port)
    return 0


def _cmd_version(args: argparse.Namespace) -> int:
    print(f"saltcav-lab {__version__}")
    return 0


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="saltcav",
        description="saltcav-lab: моделирование выщелачивания соляного канала и веб-визуализатор",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run
    p_run = sub.add_parser("run", help="Запустить симуляцию по YAML-конфигурации")
    p_run.add_argument("config", help="Путь к YAML-файлу конфигурации")
    p_run.add_argument("--out", help="Путь для сохранения результатов (CSV)")
    p_run.set_defaults(func=_cmd_run)

    # check
    p_check = sub.add_parser("check", help="Проверить валидность YAML-конфигурации")
    p_check.add_argument("config", help="Путь к YAML-файлу")
    p_check.set_defaults(func=_cmd_check)

    # web
    p_web = sub.add_parser("web", help="Запустить веб-интерфейс визуализации")
    p_web.add_argument("--port", type=int, default=8080, help="Порт сервера (по умолчанию: 8080)")
    p_web.add_argument("--host", default="127.0.0.1", help="Хост сервера (по умолчанию: 127.0.0.1)")
    p_web.set_defaults(func=_cmd_web)

    # version
    p_ver = sub.add_parser("version", help="Версия пакета")
    p_ver.set_defaults(func=_cmd_version)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
