#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
styles.py — Estilos ttk de IPSwitcher
======================================
Define la paleta de colores y configura todos los estilos de widgets ttk
usados en la interfaz grafica.

La paleta sigue un tema oscuro con acento en cian electrico (#00d4ff) y
violeta (#7c3aed) sobre fondo azul noche (#1a1d2e).

Uso tipico
----------
::

    import tkinter as tk
    from src.gui.styles import COLORS, configure_styles

    root = tk.Tk()
    configure_styles(root)
    # A partir de aqui los estilos "App.*", "Panel.*", "Apply.*" estan listos
"""

import tkinter as tk
from tkinter import ttk

# ---------------------------------------------------------------------------
# Paleta de colores
# ---------------------------------------------------------------------------

COLORS: dict[str, str] = {
    "bg"       : "#1a1d2e",   # fondo principal (azul noche)
    "panel"    : "#252840",   # fondo de paneles y comboboxes
    "accent"   : "#00d4ff",   # cian electrico (boton primario, titulos)
    "accent2"  : "#7c3aed",   # violeta (hover, DHCP, seleccion)
    "text"     : "#e2e8f0",   # texto principal
    "text_dim" : "#64748b",   # texto secundario / etiquetas
    "success"  : "#22c55e",   # verde: operacion correcta
    "error"    : "#ef4444",   # rojo: error
    "warning"  : "#f59e0b",   # naranja: advertencia
    "border"   : "#334155",   # borde sutil
}


def configure_styles(root: tk.Tk) -> None:
    """
    Configura todos los estilos ttk y opciones globales de Tkinter.

    Debe llamarse una sola vez tras crear la ventana raiz y antes de
    construir cualquier widget.

    Parameters
    ----------
    root : tk.Tk
        Ventana raiz de la aplicacion.
    """
    style = ttk.Style(root)
    style.theme_use("clam")
    c = COLORS

    # ── Marcos ──────────────────────────────────────────────────────────
    style.configure("App.TFrame",   background=c["bg"])
    style.configure("Panel.TFrame", background=c["panel"])

    # ── Etiquetas ────────────────────────────────────────────────────────
    style.configure(
        "App.TLabel",
        background=c["bg"],
        foreground=c["text"],
        font=("DejaVu Sans Mono", 10),
    )
    style.configure(
        "Title.TLabel",
        background=c["bg"],
        foreground=c["accent"],
        font=("DejaVu Sans Mono", 16, "bold"),
    )
    style.configure(
        "Dim.TLabel",
        background=c["panel"],
        foreground=c["text_dim"],
        font=("DejaVu Sans Mono", 9),
    )
    style.configure(
        "Info.TLabel",
        background=c["panel"],
        foreground=c["accent"],
        font=("DejaVu Sans Mono", 10, "bold"),
    )

    # ── ComboBox ─────────────────────────────────────────────────────────
    style.configure(
        "App.TCombobox",
        fieldbackground=c["panel"],
        background=c["accent"],
        foreground=c["text"],
        selectbackground=c["accent2"],
        selectforeground=c["text"],
        insertcolor=c["text"],
        font=("DejaVu Sans Mono", 10),
    )
    style.map(
        "App.TCombobox",
        fieldbackground=[("readonly", c["panel"]), ("disabled", c["bg"])],
        foreground=[("readonly", c["text"]),        ("disabled", c["text_dim"])],
        selectbackground=[("readonly", c["accent2"])],
        selectforeground=[("readonly", c["text"])],
        background=[("readonly", c["accent"]),      ("active", c["accent2"])],
    )

    # Lista interna del ComboBox (Listbox subyacente de Tk)
    root.option_add("*TCombobox*Listbox.background",       c["panel"])
    root.option_add("*TCombobox*Listbox.foreground",       c["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", c["accent2"])
    root.option_add("*TCombobox*Listbox.selectForeground", c["text"])
    root.option_add("*TCombobox*Listbox.font", ("DejaVu Sans", 10))

    # ── Boton principal (Aplicar) ────────────────────────────────────────
    style.configure(
        "Apply.TButton",
        background=c["accent"],
        foreground=c["bg"],
        font=("DejaVu Sans Mono", 11, "bold"),
        padding=(20, 8),
        relief="flat",
    )
    style.map(
        "Apply.TButton",
        background=[("active", c["accent2"]), ("pressed", c["accent2"])],
        foreground=[("active", c["text"]),    ("pressed", c["text"])],
    )
