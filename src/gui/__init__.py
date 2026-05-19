#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
src/gui/__init__.py
===================
Subpaquete de interfaz grafica de IPSwitcher.

Exporta IPSwitcherGUI como simbolo publico del subpaquete para que el
punto de entrada pueda importarla directamente::

    from src.gui import IPSwitcherGUI
"""

from .app import IPSwitcherGUI

__all__ = ["IPSwitcherGUI"]
