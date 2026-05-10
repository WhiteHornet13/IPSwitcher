# -*- coding: utf-8 -*-
"""
setup_xp.py — cx_Freeze setup para IPSwitcherXP (Windows XP, Python 2.7)
=========================================================================
Genera un ejecutable portable en dist/windowsXP/IPSwitcherXP/

Uso:
    python setup_xp.py build        → Compilar en dist/windowsXP/IPSwitcherXP/
    python setup_xp.py install      → Instalar en el sistema (no recomendado)

Requisitos:
    Python 2.7.18 (última versión de Python 2.7)
    cx_Freeze 5.1.1  (última versión compatible con Python 2.7)

        pip install cx_Freeze==5.1.1
"""

from __future__ import print_function

import os
import sys

try:
    from cx_Freeze import setup, Executable
except ImportError:
    print("ERROR: cx_Freeze no instalado.")
    print("  pip install cx_Freeze==5.1.1")
    sys.exit(1)

# Directorio raiz del proyecto
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Paquetes que cx_Freeze debe incluir explícitamente
# (con Python 2.7 la detección automática es menos confiable)
# ---------------------------------------------------------------------------
PACKAGES = [
    "os",
    "sys",
    "io",
    "json",
    "locale",
    "logging",
    "optparse",
    "platform",
    "subprocess",
    "threading",
    "ctypes",
    "Tkinter",
    "ttk",
    "tkMessageBox",
    "tkColorChooser",
    "tkCommonDialog",
    "tkFileDialog",
    "tkFont",
    "tkSimpleDialog",
]

# Módulos que no son necesarios y agrandan el ejecutable
EXCLUDES = [
    "email",
    "html",
    "http",
    "urllib",
    "urllib2",
    "xml",
    "xmlrpclib",
    "unittest",
    "pydoc",
    "doctest",
    "difflib",
    "inspect",
    "pdb",
    "profile",
    "cProfile",
    "distutils",
    "setuptools",
    "pkg_resources",
    "numpy",
    "scipy",
    "matplotlib",
    "PIL",
]

# Archivos de datos que se copian junto al ejecutable
INCLUDE_FILES = [
    # (origen, destino_en_el_paquete)
    (os.path.join(HERE, "ips.json"), "ips.json"),
]

# ---------------------------------------------------------------------------
# Opciones de compilación
# ---------------------------------------------------------------------------
BUILD_OPTIONS = {
    "packages"       : PACKAGES,
    "excludes"       : EXCLUDES,
    "include_files"  : INCLUDE_FILES,
    "optimize"       : 2,           # .pyo optimizado
    "build_exe"      : os.path.join(HERE, "dist", "windowsXP", "IPSwitcherXP"),
    "include_msvcr"  : True,        # incluir DLLs de runtime de Visual C++
    "silent"         : False,
}

# ---------------------------------------------------------------------------
# Ejecutable
# ---------------------------------------------------------------------------
# base="Win32GUI" elimina la ventana de consola negra.
# Cambiar a base="Console" para mostrarla (útil en depuración).
EXECUTABLES = [
    Executable(
        script          = os.path.join(HERE, "src", "ipswitcherXP.py"),
        base            = "Win32GUI",
        targetName      = "IPSwitcherXP.exe",
        shortcutName    = "IPSwitcherXP",
        shortcutDir     = "ProgramMenuFolder",
        copyright       = "IPSwitcher Project 2024",
    ),
]

# ---------------------------------------------------------------------------
# Metadatos del paquete
# ---------------------------------------------------------------------------
setup(
    name        = "IPSwitcherXP",
    version     = "1.0.0",
    author      = "IPSwitcher Project",
    description = "Cambia la IPv4 de adaptadores de red (Windows XP)",
    url         = "https://github.com/WhiteHornet13/IPSwitcher",
    options     = {"build_exe": BUILD_OPTIONS},
    executables = EXECUTABLES,
)
