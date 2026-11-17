#!/usr/bin/env python3
"""Быстрый запуск веб-визуализатора saltcav-lab."""

import sys
from pathlib import Path

# Добавляем src/ в PYTHONPATH при прямом запуске скрипта
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from saltcav.web.server import launch_server

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    launch_server(port=port)
