#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
__main__.py — Punto de entrada de IPSwitcher
=============================================
Orquesta el flujo de arranque de la aplicacion:

1. Parsea los argumentos de linea de comandos.
2. Configura idioma y nivel de logging.
3. Carga los perfiles desde ``ips.json``.
4. Segun los argumentos, ejecuta uno de los tres modos:

   - ``--list``              : imprime adaptadores y termina.
   - ``--adapter + --profile``: aplica un perfil por CLI y termina.
   - *(por defecto)*          : abre la interfaz grafica (GUI).

En modo GUI, si la aplicacion no tiene privilegios intenta relanzarse
con permisos de administrador antes de construir la ventana.

Uso como modulo
---------------
::

    python -m src          # desde la raiz del proyecto (desarrollo)

Uso compilado (PyInstaller)
---------------------------
::

    sudo ./IPSwitcher              # Linux
    IPSwitcher.exe                 # Windows (UAC se dispara automaticamente)
"""

import logging
import sys
import tkinter as tk

from .cli import build_parser, cli_apply, cli_list
from .constants import APP_NAME
from .i18n import set_language
from .network import get_network_adapters
from .privileges import check_privileges, relaunch_as_admin
from .profiles import get_flat_profiles, load_profiles


def _setup_logging(verbose: bool = False) -> None:
    """
    Configura el sistema de logging de la aplicacion.

    Parameters
    ----------
    verbose : bool
        Si es ``True`` activa el nivel DEBUG; si no, usa INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> None:
    """
    Funcion principal de IPSwitcher.

    Parseado de argumentos, configuracion de idioma/logging, carga de
    perfiles y despacho al modo correspondiente (list, apply, gui).
    """
    parser = build_parser()
    args   = parser.parse_args()

    # 1. Idioma: argumento CLI tiene prioridad sobre autodeteccion del SO
    if args.lang:
        set_language(args.lang)

    # 2. Logging
    _setup_logging(verbose=args.verbose)
    logger = logging.getLogger(APP_NAME)

    # 3. Carga de perfiles
    raw_data = load_profiles()
    profiles = get_flat_profiles(raw_data)

    # ── Modo --list ────────────────────────────────────────────────────────
    if args.list:
        cli_list(get_network_adapters())
        sys.exit(0)

    # ── Modo CLI: --adapter + --profile ────────────────────────────────────
    if args.adapter and args.profile:
        if not check_privileges():
            logger.error("Se requieren privilegios de administrador.")
            sys.exit(1)
        cli_apply(args.adapter, args.profile, profiles)
        sys.exit(0)

    # ── Modo GUI (por defecto o con --gui) ─────────────────────────────────
    # Intentar elevar privilegios si no los tiene; si el usuario cancela
    # la aplicacion continua sin ellos y muestra la advertencia en cabecera.
    if not check_privileges():
        relaunch_as_admin()

    root = tk.Tk()

    # Importacion diferida para no requerir Tkinter en modo CLI puro
    from .gui import IPSwitcherGUI  # noqa: PLC0415

    IPSwitcherGUI(root, profiles)
    root.mainloop()


if __name__ == "__main__":
    main()
