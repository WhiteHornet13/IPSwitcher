#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py — Ventana principal de IPSwitcher
=========================================
Define la clase :class:`IPSwitcherGUI` que construye y gestiona la interfaz
grafica completa de la aplicacion.

Estructura visual
-----------------
::

    ┌──────────────────────────────────────────────────────┐
    │ ◈  IPSwitcher  v1.2.4   IP Actual: x.x.x.x  ● admin │
    ├──────────────────────────────────────────────────────┤
    │ Adaptador de red: [eth0              ▼]  [⟳ Actualizar]│
    │ Perfil de IP:     [Linea 7 / ...     ▼]              │
    │ Nueva IP          Mascara            IP Destino       │
    │ 192.168.214.246   255.255.255.0      0.0.0.0          │
    ├──────────────────────────────────────────────────────┤
    │ [▶  Aplicar                                       ]  │
    │ [⇄ DHCP adaptador]  [⇄ DHCP todos]                   │
    ├──────────────────────────────────────────────────────┤
    │ LOG                                                  │
    │ Adaptadores detectados: 3                            │
    └──────────────────────────────────────────────────────┘

Usa hilos daemon para todas las operaciones de red, evitando que la GUI
quede bloqueada mientras se aplican cambios.
"""

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from ..constants import APP_NAME, APP_VERSION, _BASE_DIR
from ..i18n import t
from ..network import (
    apply_profile,
    get_adapter_hardware,
    get_all_adapter_hardware,
    get_current_ip,
    get_network_adapters,
    set_dhcp,
)
from ..privileges import check_privileges
from .styles import COLORS, configure_styles


class IPSwitcherGUI:
    """
    Ventana principal de la aplicacion IPSwitcher.

    Parameters
    ----------
    root : tk.Tk
        Instancia raiz de Tkinter.
    profiles : dict[str, dict]
        Diccionario plano de perfiles generado por
        :func:`~src.profiles.get_flat_profiles`.
    """

    def __init__(self, root: tk.Tk, profiles: dict[str, dict]) -> None:
        self.root     = root
        self.profiles = profiles
        self.adapters : list[str] = []

        # Mapa etiqueta_display -> nombre_real_del_SO
        # (el display puede incluir descripcion de hardware)
        self._adapter_map: dict[str, str] = {}

        configure_styles(root)
        self._setup_window()
        self._build_ui()
        self._refresh_adapters()

    # =========================================================================
    # Configuracion de la ventana
    # =========================================================================

    def _setup_window(self) -> None:
        """Configura propiedades basicas de la ventana principal."""
        self.root.title(t("title"))
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["bg"])

        w, h = 800, 640
        sx   = self.root.winfo_screenwidth()
        sy   = self.root.winfo_screenheight()
        x    = (sx - w) // 2
        y    = (sy - h) // 2
        self.root.geometry("{}x{}+{}+{}".format(w, h, x, y))

        # Icono de la aplicacion (.ico en Windows, .png en Linux)
        try:
            ico = _BASE_DIR / "assets" / "ipswitcher.ico"
            png = _BASE_DIR / "assets" / "ipswitcher.png"
            if ico.exists():
                self.root.iconbitmap(str(ico))
            elif png.exists():
                img = tk.PhotoImage(file=str(png))
                self.root.iconphoto(True, img)
        except Exception:
            pass

    # =========================================================================
    # Construccion de la UI
    # =========================================================================

    def _build_ui(self) -> None:
        """Construye y dispone todos los widgets de la interfaz."""
        c = COLORS

        # ── Cabecera ──────────────────────────────────────────────────────
        header = ttk.Frame(self.root, style="App.TFrame")
        header.pack(fill="x", padx=18, pady=(18, 4))

        ttk.Label(
            header,
            text="◈  " + APP_NAME,
            style="Title.TLabel",
        ).pack(side="left")

        ttk.Label(
            header,
            text="v{}".format(APP_VERSION),
            style="App.TLabel",
        ).pack(side="left", padx=(6, 0), pady=(6, 0))

        # Indicador de privilegios
        priv_ok  = check_privileges()
        priv_txt = "● admin" if priv_ok else "● sin privilegios"
        priv_clr = c["success"] if priv_ok else c["error"]
        tk.Label(
            header,
            text=priv_txt,
            bg=c["bg"],
            fg=priv_clr,
            font=("DejaVu Sans Mono", 8),
        ).pack(side="right")

        # Label de IP actual (se actualiza al cambiar adaptador o aplicar perfil)
        self._lbl_current_ip = tk.Label(
            header,
            text="IP Actual: \u2014",
            bg=c["bg"],
            fg=c["accent"],
            font=("DejaVu Sans Mono", 9, "bold"),
        )
        self._lbl_current_ip.pack(side="left", padx=(24, 0))

        # Separador horizontal
        tk.Frame(self.root, bg=c["accent"], height=1).pack(
            fill="x", padx=18, pady=(4, 10)
        )

        # ── Panel de seleccion ────────────────────────────────────────────
        sel_frame = ttk.Frame(self.root, style="Panel.TFrame")
        sel_frame.pack(fill="x", padx=18, pady=4, ipady=10)

        # Fila: seleccion de adaptador + boton Actualizar
        row1 = ttk.Frame(sel_frame, style="Panel.TFrame")
        row1.pack(fill="x", padx=12, pady=(8, 4))

        tk.Label(
            row1, text=t("select_adapter"),
            bg=c["panel"], fg=c["text_dim"],
            font=("DejaVu Sans Mono", 9),
        ).pack(side="left")

        self._adapter_var = tk.StringVar()
        self._cb_adapter  = ttk.Combobox(
            row1,
            textvariable=self._adapter_var,
            state="readonly",
            width=58,
            style="App.TCombobox",
        )
        self._cb_adapter.pack(side="left", padx=(8, 0))
        self._cb_adapter.bind("<<ComboboxSelected>>", self._on_adapter_change)

        tk.Button(
            row1,
            text="\u27f3 " + t("btn_refresh"),
            bg=c["accent"], fg=c["bg"],
            activebackground=c["accent2"], activeforeground=c["text"],
            font=("DejaVu Sans Mono", 9, "bold"),
            relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
            command=self._refresh_adapters,
        ).pack(side="left", padx=(8, 0))

        # Fila: seleccion de perfil
        row2 = ttk.Frame(sel_frame, style="Panel.TFrame")
        row2.pack(fill="x", padx=12, pady=4)

        tk.Label(
            row2, text=t("select_profile"),
            bg=c["panel"], fg=c["text_dim"],
            font=("DejaVu Sans Mono", 9),
        ).pack(side="left")

        self._profile_var = tk.StringVar()
        self._cb_profile  = ttk.Combobox(
            row2,
            textvariable=self._profile_var,
            values=sorted(self.profiles.keys()),
            state="readonly",
            width=46,
            style="App.TCombobox",
        )
        self._cb_profile.pack(side="left", padx=(8, 0))
        self._cb_profile.bind("<<ComboboxSelected>>", self._on_profile_change)

        # ── Panel de detalle del perfil seleccionado ──────────────────────
        detail = ttk.Frame(self.root, style="Panel.TFrame")
        detail.pack(fill="x", padx=18, pady=4, ipady=8)

        self._lbl_ip   = self._add_detail_col(detail, t("new_ip"))
        self._lbl_mask = self._add_detail_col(detail, t("mask"))
        self._lbl_gw   = self._add_detail_col(detail, t("destino"))

        # ── Boton Aplicar ─────────────────────────────────────────────────
        ttk.Button(
            self.root,
            text="\u25b6  " + t("btn_apply"),
            style="Apply.TButton",
            command=self._apply,
        ).pack(fill="x", padx=18, pady=(10, 4))

        # ── Botones DHCP ──────────────────────────────────────────────────
        dhcp_row = ttk.Frame(self.root, style="App.TFrame")
        dhcp_row.pack(fill="x", padx=18, pady=(0, 4))

        for text, cmd in [
            ("\u21c4 " + t("btn_dhcp_one"), self._dhcp_selected),
            ("\u21c4 " + t("btn_dhcp_all"), self._dhcp_all),
        ]:
            tk.Button(
                dhcp_row,
                text=text,
                bg=c["accent2"], fg=c["text"],
                activebackground=c["accent"], activeforeground=c["bg"],
                font=("DejaVu Sans Mono", 9, "bold"),
                relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
                command=cmd,
            ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        # ── Area de log ───────────────────────────────────────────────────
        log_frame = ttk.Frame(self.root, style="App.TFrame")
        log_frame.pack(fill="both", expand=True, padx=18, pady=(4, 16))

        tk.Label(
            log_frame, text="LOG",
            bg=c["bg"], fg=c["text_dim"],
            font=("DejaVu Sans Mono", 8),
        ).pack(anchor="w")

        self._log_box = tk.Text(
            log_frame,
            bg=c["panel"], fg=c["text"],
            font=("DejaVu Sans Mono", 9),
            relief="flat", height=8, state="disabled",
            bd=0, wrap="word",
        )
        self._log_box.pack(fill="both", expand=True)

        # Tags de color para las entradas del log
        self._log_box.tag_configure("ok",      foreground=c["success"])
        self._log_box.tag_configure("err",     foreground=c["error"])
        self._log_box.tag_configure("info",    foreground=c["accent"])
        self._log_box.tag_configure("warning", foreground=c["warning"])

    def _add_detail_col(self, parent: ttk.Frame, label_text: str) -> tk.Label:
        """
        Crea una columna de detalle (etiqueta + valor) en el panel de perfil.

        Parameters
        ----------
        parent : ttk.Frame
            Frame contenedor.
        label_text : str
            Texto de la etiqueta descriptiva.

        Returns
        -------
        tk.Label
            Label del valor (para actualizar posteriormente).
        """
        c = COLORS
        col = ttk.Frame(parent, style="Panel.TFrame")
        col.pack(side="left", expand=True, fill="x", padx=12)

        tk.Label(
            col, text=label_text,
            bg=c["panel"], fg=c["text_dim"],
            font=("DejaVu Sans Mono", 8),
        ).pack(anchor="w")

        lbl = tk.Label(
            col, text="\u2014",
            bg=c["panel"], fg=c["accent"],
            font=("DejaVu Sans Mono", 11, "bold"),
        )
        lbl.pack(anchor="w")
        return lbl

    # =========================================================================
    # Callbacks y logica
    # =========================================================================

    def _refresh_adapters(self) -> None:
        """
        Actualiza la lista de adaptadores con nombre real + hardware detectado.

        Realiza una unica consulta de hardware para todos los adaptadores
        (en Windows evita lanzar un proceso PowerShell por cada interfaz).
        Mantiene el mapa interno ``_adapter_map`` etiqueta->nombre_real.
        """
        raw      = get_network_adapters()
        hw_cache = get_all_adapter_hardware()

        self._adapter_map = {}
        labels: list[str] = []

        for name in raw:
            hw    = get_adapter_hardware(name, _cache=hw_cache)
            label = "{:<12} {}".format(name, hw).rstrip() if hw else name
            self._adapter_map[label] = name
            labels.append(label)

        self.adapters = raw
        self._cb_adapter.configure(values=labels)

        if labels:
            self._cb_adapter.current(0)
            self._update_current_ip(raw[0])

        self._log("info", "Adaptadores detectados: {}".format(len(raw)))

    def _update_current_ip(self, adapter: str) -> None:
        """
        Consulta y muestra la IP actualmente asignada al adaptador indicado.

        Parameters
        ----------
        adapter : str
            Nombre real del adaptador (sin la etiqueta de hardware).
        """
        ip = get_current_ip(adapter)
        self._lbl_current_ip.configure(
            text="IP Actual: {}".format(ip) if ip else "IP Actual: \u2014"
        )

    def _on_adapter_change(self, _event=None) -> None:
        """Actualiza la IP actual en pantalla al cambiar el adaptador."""
        label   = self._adapter_var.get()
        adapter = self._adapter_map.get(label, label)
        self._update_current_ip(adapter)
        self._log("info", "Adaptador: {}".format(adapter))

    def _on_profile_change(self, _event=None) -> None:
        """Actualiza los labels de detalle al cambiar el perfil seleccionado."""
        key = self._profile_var.get()
        if key and key in self.profiles:
            p = self.profiles[key]
            self._lbl_ip.configure(text=p["ip"])
            self._lbl_mask.configure(text=p["mask"])
            self._lbl_gw.configure(text=p["destino"])

    def _apply(self) -> None:
        """Valida la seleccion y aplica el perfil en un hilo daemon."""
        label       = self._adapter_var.get().strip()
        adapter     = self._adapter_map.get(label, label)
        profile_key = self._profile_var.get().strip()

        if not adapter:
            self._log("err", t("error_adapter", "(vacio)"))
            return
        if not profile_key:
            self._log("err", t("error_profile", "(vacio)"))
            return

        profile = self.profiles[profile_key]
        if not messagebox.askyesno(
            t("confirm_title"),
            t("confirm_msg", profile["ip"], adapter),
            parent=self.root,
        ):
            return

        threading.Thread(
            target=self._apply_thread,
            args=(adapter, profile_key, profile),
            daemon=True,
        ).start()

    def _apply_thread(
        self, adapter: str, profile_key: str, profile: dict
    ) -> None:
        """
        Hilo que aplica el perfil y actualiza el log al terminar.

        Refresca la IP mostrada en cabecera con un pequeno retardo para dar
        tiempo al SO a asignar la nueva direccion.
        """
        self._log("info", t("log_applying", profile_key, adapter))
        try:
            apply_profile(adapter, profile)
            self._log("ok", t("success"))
            # Retardo de 800 ms para que el SO complete la asignacion
            self.root.after(800, self._update_current_ip, adapter)
        except RuntimeError as exc:
            self._log("err", t("error_apply", exc))

    def _dhcp_selected(self) -> None:
        """Pasa el adaptador actualmente seleccionado a DHCP."""
        label   = self._adapter_var.get().strip()
        adapter = self._adapter_map.get(label, label)
        if not adapter:
            self._log("err", t("error_adapter", "(vacio)"))
            return
        if not messagebox.askyesno(
            t("confirm_title"),
            t("confirm_dhcp_one", adapter),
            parent=self.root,
        ):
            return
        threading.Thread(
            target=self._dhcp_thread,
            args=([adapter],),
            daemon=True,
        ).start()

    def _dhcp_all(self) -> None:
        """Pasa TODOS los adaptadores detectados a DHCP."""
        if not self.adapters:
            self._log("warning", t("no_adapters"))
            return
        if not messagebox.askyesno(
            t("confirm_title"),
            t("confirm_dhcp_all"),
            parent=self.root,
        ):
            return
        threading.Thread(
            target=self._dhcp_thread,
            args=(list(self.adapters),),
            daemon=True,
        ).start()

    def _dhcp_thread(self, adapters: list[str]) -> None:
        """
        Hilo que aplica DHCP sobre la lista de adaptadores recibida.

        Actualiza el log por cada adaptador y refresca la IP actual al final.
        """
        for adapter in adapters:
            self._log("info", "DHCP \u2192 {}".format(adapter))
            try:
                set_dhcp(adapter)
                self._log("ok", "DHCP aplicado en {}.".format(adapter))
            except RuntimeError as exc:
                self._log("err", t("error_apply", exc))

        label   = self._adapter_var.get()
        current = self._adapter_map.get(label, label)
        self.root.after(1500, self._update_current_ip, current)

    # =========================================================================
    # Utilidades de la GUI
    # =========================================================================

    def _log(self, tag: str, message: str) -> None:
        """
        Aniade un mensaje al widget de log con el color del tag indicado.

        Esta funcion es segura para llamarla desde hilos secundarios porque
        solo modifica el widget (que es thread-safe en Tkinter para inserciones
        simples).

        Parameters
        ----------
        tag : str
            Color de la linea: ``'ok'``, ``'err'``, ``'info'``, ``'warning'``.
        message : str
            Texto a insertar en el log.
        """
        self._log_box.configure(state="normal")
        self._log_box.insert("end", message + "\n", tag)
        self._log_box.see("end")
        self._log_box.configure(state="disabled")
