#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
profiles.py — Gestion de perfiles de IP
========================================
Carga el archivo JSON de perfiles y lo convierte en un diccionario
plano listo para usar tanto en la GUI como en la CLI.

Esquema JSON esperado
---------------------
::

    {
      "IPs": {
        "lineas": [
          {
            "nombre": "Linea 1",
            "maquinas": [
              {
                "nombre": "Maquina 1",
                "equipos": [
                  {
                    "nombre"    : "Equipo 1",
                    "IP-PC"     : "192.168.1.10",
                    "Mascara"   : "255.255.255.0",
                    "IP-Destino": "192.168.1.254"
                  }
                ]
              }
            ]
          }
        ]
      }
    }

El diccionario plano resultante usa claves con formato:
``"Linea 1 / Maquina 1 / Equipo 1"``
"""

import json
import logging
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from .constants import APP_NAME, PROFILES_FILE
from .i18n import t

logger = logging.getLogger(APP_NAME)


def load_profiles(path: Path = PROFILES_FILE) -> dict:
    """
    Carga y valida el archivo JSON de perfiles de IP.

    Si el archivo no existe o tiene formato invalido muestra un dialogo de
    error (si hay entorno grafico disponible), registra el error en el log
    y termina la aplicacion con codigo de salida 1.

    Parameters
    ----------
    path : Path, optional
        Ruta al archivo JSON. Por defecto usa ``PROFILES_FILE`` de constants.

    Returns
    -------
    dict
        Contenido completo del JSON tal como lo parsea ``json.load()``.

    Raises
    ------
    SystemExit
        Si el archivo no existe o no es JSON valido.
    """
    if not path.exists():
        msg = t("error_load", str(path))
        logger.error(msg)
        _show_error(msg)
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, IOError) as exc:
        msg = t("error_load", exc)
        logger.error(msg)
        _show_error(msg)
        sys.exit(1)

    return data


def get_flat_profiles(data: dict) -> dict[str, dict]:
    """
    Aplana la jerarquia Linea / Maquina / Equipo en un diccionario plano.

    La clave resultante tiene el formato::

        "Linea X / Maquina Y / Equipo Z"

    El campo ``IP-Destino`` del JSON se almacena como ``destino`` con caracter
    informativo exclusivamente; no se usa como gateway al aplicar la
    configuracion (el gateway siempre queda vacio para evitar rutas erroneas).

    Parameters
    ----------
    data : dict
        Diccionario cargado desde el JSON mediante :func:`load_profiles`.

    Returns
    -------
    dict[str, dict]
        Diccionario plano ``{ "Linea X / Maquina Y / Equipo Z": perfil }``.
        Cada perfil es un dict con claves ``ip``, ``mask``, ``destino`` y
        ``gateway`` (siempre cadena vacia).

    Examples
    --------
    >>> data = load_profiles()
    >>> profiles = get_flat_profiles(data)
    >>> profiles["Linea 7 / Bobinadora / PLC Perini"]
    {'ip': '192.168.214.246', 'mask': '255.255.255.0', 'destino': '0.0.0.0', 'gateway': ''}
    """
    flat: dict[str, dict] = {}

    for linea in data.get("IPs", {}).get("lineas", []):
        for maquina in linea.get("maquinas", []):
            for equipo in maquina.get("equipos", []):
                key = "{} / {} / {}".format(
                    linea["nombre"],
                    maquina["nombre"],
                    equipo["nombre"],
                )
                flat[key] = {
                    "ip"     : equipo.get("IP-PC", ""),
                    "mask"   : equipo.get("Mascara", ""),
                    # IP-Destino es solo informativo; no se aplica como gateway
                    "destino": equipo.get("IP-Destino", ""),
                    "gateway": "",   # siempre en blanco
                }

    return flat


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------

def _show_error(message: str) -> None:
    """
    Muestra un dialogo de error de Tkinter si hay entorno grafico disponible.

    Falla silenciosamente si no hay display (ej. ejecucion en servidor).

    Parameters
    ----------
    message : str
        Texto del error a mostrar.
    """
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(APP_NAME, message)
        root.destroy()
    except Exception:
        pass
