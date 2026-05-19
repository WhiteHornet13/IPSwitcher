#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
privileges.py — Gestion de privilegios de IPSwitcher
=====================================================
Comprueba si la aplicacion se ejecuta con privilegios de administrador y,
si no, intenta relanzarse elevada usando el mecanismo nativo de cada SO:

- Linux  : ``pkexec`` (PolicyKit, compatible con GUI) o ``sudo -E``.
- Windows: ``ShellExecuteW`` con verbo ``'runas'`` (dialogo UAC estandar).

La funcion ``_relaunch_as_admin()`` nunca retorna si el relaunch tiene exito
(reemplaza el proceso actual via ``os.execvp`` en Linux o termina con
``sys.exit(0)`` en Windows). Si el usuario cancela o falla, la aplicacion
continua sin privilegios y mostrara una advertencia en la cabecera de la GUI.
"""

import logging
import os
import platform
import shutil
import sys
from pathlib import Path

from .constants import APP_NAME
from .i18n import t

logger = logging.getLogger(APP_NAME)

_OS = platform.system()


def check_privileges() -> bool:
    """
    Comprueba si la aplicacion se esta ejecutando con privilegios elevados.

    Returns
    -------
    bool
        ``True`` si tiene privilegios de root (Linux) o Administrador (Windows).
        ``False`` en caso contrario o si no se puede determinar.
    """
    if _OS == "Windows":
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    else:
        # Linux / macOS: root tiene UID 0
        return os.geteuid() == 0


def relaunch_as_admin() -> None:
    """
    Relanza el proceso actual con privilegios de administrador/root.

    Linux
    -----
    Intenta ``pkexec --keep-cwd`` primero (entorno de escritorio PolicyKit).
    Si no esta disponible usa ``sudo -E`` para preservar las variables de
    entorno del usuario (DISPLAY, XAUTHORITY).

    Distingue correctamente entre binario compilado con PyInstaller y script
    Python normal para no duplicar la ruta del ejecutable como argumento:

    - **Frozen** (PyInstaller): ``target = [ruta_ejecutable]``
    - **Script**              : ``target = [python, ruta_script]``

    Windows
    -------
    Usa ``ShellExecuteW`` con el verbo ``'runas'`` para mostrar el dialogo
    UAC estandar. Si el usuario acepta, lanza una nueva instancia elevada y
    termina el proceso actual con ``sys.exit(0)``.

    Notes
    -----
    Esta funcion usa ``os.execvp`` en Linux, que *reemplaza* el proceso actual.
    Por tanto nunca retorna si el relaunch tiene exito.
    Si el usuario cancela o el relaunch falla, la funcion retorna normalmente
    y la aplicacion continua sin privilegios.
    """
    logger.debug("sys.executable : %s", sys.executable)
    logger.debug("sys.argv       : %s", sys.argv)
    logger.debug("frozen         : %s", getattr(sys, "frozen", False))

    if _OS == "Linux":
        _relaunch_linux()
    elif _OS == "Windows":
        _relaunch_windows()


# ---------------------------------------------------------------------------
# Implementaciones privadas por SO
# ---------------------------------------------------------------------------

def _relaunch_linux() -> None:
    """Elevacion de privilegios en Linux usando pkexec o sudo."""
    if getattr(sys, "frozen", False):
        target = [str(Path(sys.executable).resolve())]
    else:
        target = [sys.executable, str(Path(sys.argv[0]).resolve())]

    extra_args = sys.argv[1:]

    pkexec = shutil.which("pkexec")
    if pkexec:
        try:
            os.environ.setdefault("DISPLAY", ":0")
            os.execvp(pkexec, [
                pkexec, "--keep-cwd", "env",
                "DISPLAY={}".format(os.environ.get("DISPLAY", ":0")),
                "XAUTHORITY={}".format(os.environ.get("XAUTHORITY", "")),
            ] + target + extra_args)
        except OSError as exc:
            logger.debug("pkexec fallo: %s", exc)

    sudo = shutil.which("sudo")
    if sudo:
        try:
            os.execvp(sudo, [sudo, "-E"] + target + extra_args)
        except OSError as exc:
            logger.debug("sudo fallo: %s", exc)

    logger.warning(
        "No se pudo elevar a root. "
        "La aplicacion continuara sin privilegios."
    )


def _relaunch_windows() -> None:
    """Elevacion de privilegios en Windows usando el dialogo UAC."""
    import ctypes

    exe    = sys.executable if not getattr(sys, "frozen", False) else sys.argv[0]
    params = " ".join('"{}"'.format(a) for a in sys.argv[1:])

    ret = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", exe, params, None, 1
    )
    if ret > 32:
        # Nueva instancia elevada lanzada correctamente; terminar esta
        sys.exit(0)
    else:
        logger.warning(
            "UAC cancelado o error (%s). Continuando sin privilegios.", ret
        )
