#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
constants.py — Constantes globales de IPSwitcher
=================================================
Centraliza metadatos de la aplicación, resolución de rutas y flags de
subproceso dependientes de plataforma.

Todos los demás módulos deben importar desde aquí en lugar de redefinir
estas constantes localmente.
"""

import platform
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Metadatos de la aplicación
# ---------------------------------------------------------------------------

APP_NAME    = "IPSwitcher"
APP_VERSION = "1.3.6"
APP_REPO    = "https://github.com/WhiteHornet13/IPSwitcher"

# ---------------------------------------------------------------------------
# Resolución de la ruta base
#
# PyInstaller compila la aplicación en un ejecutable autónomo (frozen).
# En ese modo, sys.executable apunta al binario y _BASE_DIR es su carpeta.
# En modo script normal (desarrollo), la raíz del proyecto está dos niveles
# por encima de este archivo: src/constants.py -> src/ -> raiz/
# ---------------------------------------------------------------------------

if getattr(sys, "frozen", False):
    _BASE_DIR: Path = Path(sys.executable).parent
else:
    _BASE_DIR = Path(__file__).resolve().parent.parent   # raiz del proyecto

PROFILES_FILE: Path = _BASE_DIR / "ips.json"

# ---------------------------------------------------------------------------
# Flag de creacion de proceso sin ventana de consola (solo Windows)
#
# CREATE_NO_WINDOW evita que cada llamada a netsh, PowerShell, ipconfig, etc.
# abra una ventana de consola negra visible para el usuario.
# En Linux el diccionario queda vacio y subprocess lo ignora.
# ---------------------------------------------------------------------------

_POPEN_FLAGS: dict = (
    {"creationflags": subprocess.CREATE_NO_WINDOW}
    if platform.system() == "Windows"
    else {}
)
