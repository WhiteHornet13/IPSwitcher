#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli.py — Interfaz de linea de comandos de IPSwitcher
=====================================================
Define el parser de argumentos y las funciones de ejecucion en modo CLI
(sin interfaz grafica).

Argumentos soportados
---------------------
``--list``
    Lista los adaptadores de red disponibles y termina.
``--adapter NOMBRE``
    Nombre exacto del adaptador a configurar.
``--profile CLAVE``
    Clave del perfil: ``"Linea X / Maquina Y / Equipo Z"``.
``--gui``
    Abre la interfaz grafica (comportamiento por defecto).
``--lang {es,en}``
    Fuerza el idioma de la interfaz.
``--verbose``
    Activa mensajes de depuracion (nivel DEBUG).
``--version``
    Muestra la version y termina.

Ejemplo de uso
--------------
::

    ipswitcher --list
    ipswitcher --adapter eth0 --profile "Linea 7 / Bobinadora / PLC Perini"
    ipswitcher --lang en --gui
"""

import argparse
import logging
import sys

from .constants import APP_NAME, APP_VERSION
from .i18n import t
from .network import apply_profile, get_network_adapters

logger = logging.getLogger(APP_NAME)


def build_parser() -> argparse.ArgumentParser:
    """
    Construye y devuelve el parser de argumentos de linea de comandos.

    Returns
    -------
    argparse.ArgumentParser
        Parser configurado con todos los argumentos de IPSwitcher.
    """
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description=(
            "Cambia la IP de adaptadores de red a partir de perfiles JSON.\n"
            "Repositorio: https://github.com/WhiteHornet13/IPSwitcher"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  ipswitcher --list\n"
            '  ipswitcher --adapter eth0 --profile "Linea 7 / Bobinadora / PLC Perini"\n'
            "  ipswitcher --gui\n"
            "  ipswitcher --lang en --adapter eth0 --profile \"Linea 9 / Tubera / Simotion\"\n"
        ),
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="Lista los adaptadores de red disponibles y termina.",
    )
    parser.add_argument(
        "--adapter",
        metavar="NOMBRE",
        help="Nombre exacto del adaptador a configurar.",
    )
    parser.add_argument(
        "--profile",
        metavar="CLAVE",
        help='Clave del perfil: "Linea X / Maquina Y / Equipo Z".',
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Abre la interfaz grafica (comportamiento por defecto).",
    )
    parser.add_argument(
        "--lang",
        choices=["es", "en"],
        help="Idioma de la interfaz (es / en). Por defecto se detecta del SO.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Activa mensajes de depuracion (nivel DEBUG).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="{} {}".format(APP_NAME, APP_VERSION),
    )

    return parser


def cli_list(adapters: list[str]) -> None:
    """
    Imprime por consola la lista de adaptadores de red disponibles.

    Parameters
    ----------
    adapters : list[str]
        Lista de nombres de adaptadores devuelta por
        :func:`~src.network.get_network_adapters`.
    """
    print(t("list_header"))
    if not adapters:
        print("  " + t("no_adapters"))
    else:
        for i, adapter in enumerate(adapters, start=1):
            print("  {:2}. {}".format(i, adapter))


def cli_apply(
    adapter: str,
    profile_key: str,
    profiles: dict[str, dict],
) -> None:
    """
    Aplica un perfil de IP desde la linea de comandos.

    Valida que el adaptador exista en el sistema y que la clave del perfil
    este definida en el JSON antes de llamar a :func:`~src.network.apply_profile`.
    Sale con codigo 1 si alguna validacion falla.

    Parameters
    ----------
    adapter : str
        Nombre exacto del adaptador de red.
    profile_key : str
        Clave del perfil en formato ``"Linea X / Maquina Y / Equipo Z"``.
    profiles : dict[str, dict]
        Diccionario plano de perfiles generado por
        :func:`~src.profiles.get_flat_profiles`.
    """
    available = get_network_adapters()
    if adapter not in available:
        logger.error(t("error_adapter", adapter))
        sys.exit(1)

    if profile_key not in profiles:
        logger.error(t("error_profile", profile_key))
        logger.info("Perfiles disponibles: %s", list(profiles.keys()))
        sys.exit(1)

    try:
        apply_profile(adapter, profiles[profile_key])
        print(t("profile_applied", profile_key, adapter))
    except RuntimeError as exc:
        logger.error(t("error_apply", exc))
        sys.exit(1)
