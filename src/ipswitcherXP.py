#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IPSwitcher XP - Network IP Address Switcher (Windows XP Edition)
=================================================================
Version compatible con Windows XP usando Python 2.7.
Basada en la misma logica que ipswitcher.py pero adaptada a las
limitaciones y APIs disponibles en Python 2.7.

Version   : 1.0.0
Plataforma: Windows XP, Vista, 7 (Python 2.7)
Repositorio: https://github.com/WhiteHornet13/IPSwitcher

NOTA: Este archivo usa sintaxis Python 2.7:
  - print como sentencia (no funcion)
  - Strings sin prefijo u"" para Unicode
  - Excepciones con 'except Tipo, e:' en lugar de 'except Tipo as e:'
  - No se usan anotaciones de tipo
  - io.open para leer UTF-8 de forma segura
"""

from __future__ import print_function, unicode_literals

import os
import sys
import json
import locale
import logging
import optparse
import platform
import subprocess
import threading

# Tkinter en Python 2.7 se llama Tkinter (mayuscula)
try:
    import Tkinter as tk
    import ttk
    import tkMessageBox as messagebox
except ImportError:
    tk = None
    ttk = None
    messagebox = None

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
APP_NAME    = "IPSwitcher"
APP_VERSION = "1.0.0"

# Ruta al JSON de perfiles: junto al ejecutable/script
if getattr(sys, "frozen", False):
    # cx_Freeze pone el ejecutable en la carpeta raiz
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )

PROFILES_FILE = os.path.join(_BASE_DIR, "ips.json")

# ---------------------------------------------------------------------------
# Traducciones (i18n) - subset necesario para XP
# ---------------------------------------------------------------------------
STRINGS = {
    "es": {
        "title"          : "IPSwitcher - Cambio de IP",
        "select_adapter" : "Adaptador de red:",
        "select_profile" : "Perfil de IP:",
        "btn_apply"      : "Aplicar",
        "btn_refresh"    : "Actualizar",
        "success"        : "IP aplicada correctamente.",
        "error_root"     : "Requiere privilegios de administrador.",
        "error_load"     : "No se pudo cargar perfiles: {}",
        "error_adapter"  : "Adaptador no encontrado: {}",
        "error_profile"  : "Perfil no encontrado: {}",
        "error_apply"    : "Error al aplicar: {}",
        "no_adapters"    : "No se detectaron adaptadores.",
        "list_header"    : "Adaptadores de red disponibles:",
        "profile_applied": "Perfil '{}' aplicado en '{}'.",
        "new_ip"         : "Nueva IP",
        "mask"           : "Mascara",
        "gateway"        : "Puerta de enlace",
        "confirm_title"  : "Confirmar",
        "confirm_msg"    : "Aplicar IP {} al adaptador {}?",
    },
    "en": {
        "title"          : "IPSwitcher - IP Changer",
        "select_adapter" : "Network adapter:",
        "select_profile" : "IP profile:",
        "btn_apply"      : "Apply",
        "btn_refresh"    : "Refresh",
        "success"        : "IP applied successfully.",
        "error_root"     : "Administrator privileges required.",
        "error_load"     : "Could not load profiles: {}",
        "error_adapter"  : "Adapter not found: {}",
        "error_profile"  : "Profile not found: {}",
        "error_apply"    : "Error applying config: {}",
        "no_adapters"    : "No network adapters detected.",
        "list_header"    : "Available network adapters:",
        "profile_applied": "Profile '{}' applied to '{}'.",
        "new_ip"         : "New IP",
        "mask"           : "Subnet mask",
        "gateway"        : "Gateway",
        "confirm_title"  : "Confirm",
        "confirm_msg"    : "Apply IP {} to adapter {}?",
    },
}


def detect_language():
    """Detecta el idioma del sistema. Devuelve 'es' o 'en'."""
    try:
        lang = locale.getdefaultlocale()[0]
        if lang and lang.lower().startswith("es"):
            return "es"
    except Exception:
        pass
    return "en"


LANG = detect_language()


def t(key, *args):
    """
    Traduce una clave al idioma activo.

    Parametros
    ----------
    key  : clave del diccionario
    args : argumentos para .format()
    """
    text = STRINGS.get(LANG, STRINGS["en"]).get(key, key)
    if args:
        # Python 2.7 format() basico con posicionales
        for i, arg in enumerate(args):
            text = text.replace("{}", str(arg), 1)
    return text


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(APP_NAME)


# ---------------------------------------------------------------------------
# Carga de perfiles
# ---------------------------------------------------------------------------
def load_profiles(path=None):
    """
    Carga el archivo JSON de perfiles de IP.

    Parametros
    ----------
    path : ruta al archivo (str). Si es None usa PROFILES_FILE.

    Retorna
    -------
    dict con los datos del JSON.
    """
    if path is None:
        path = PROFILES_FILE

    if not os.path.exists(path):
        logger.error(t("error_load", path))
        sys.exit(1)

    try:
        # io.open para manejar UTF-8 en Python 2.7
        import io
        with io.open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (ValueError, IOError) as exc:
        logger.error(t("error_load", str(exc)))
        sys.exit(1)

    return data


def get_flat_profiles(data):
    """
    Aplana la estructura jerarquica del JSON.

    Retorna
    -------
    dict { "Linea X / Maquina Y / Equipo Z": {ip, mask, gateway} }
    """
    flat = {}
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
                    "gateway": equipo.get("IP-Destino", ""),
                }
    return flat


# ---------------------------------------------------------------------------
# Adaptadores de red (Windows XP - netsh)
# ---------------------------------------------------------------------------
def get_network_adapters():
    """
    Lista los adaptadores de red usando netsh (Windows XP compatible).

    Retorna
    -------
    Lista de nombres de adaptadores.
    """
    adapters = []
    try:
        proc = subprocess.Popen(
            ["netsh", "interface", "show", "interface"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, _ = proc.communicate()

        # En Python 2.7 stdout es bytes; decodificar con cp850 (consola XP)
        try:
            output = stdout.decode("cp850")
        except Exception:
            output = stdout.decode("latin-1")

        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[0] not in ("Admin", "---", "Estado"):
                adapters.append(" ".join(parts[3:]))

    except Exception as exc:
        logger.warning("No se pudo listar adaptadores: %s", exc)

    return sorted(adapters)


# ---------------------------------------------------------------------------
# Aplicar configuracion de red (Windows)
# ---------------------------------------------------------------------------
def apply_profile(adapter, profile):
    """
    Aplica una configuracion IP fija usando netsh (Windows).

    Parametros
    ----------
    adapter : nombre del adaptador
    profile : dict con 'ip', 'mask', 'gateway'
    """
    ip      = profile["ip"]
    mask    = profile["mask"]
    gateway = profile["gateway"]

    logger.info("Aplicando %s/%s vía %s en '%s'", ip, mask, gateway, adapter)

    cmd = [
        "netsh", "interface", "ip", "set", "address",
        "name={}".format(adapter),
        "source=static",
        "address={}".format(ip),
        "mask={}".format(mask),
        "gateway={}".format(gateway),
        "gwmetric=1",
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = proc.communicate()

    if proc.returncode != 0:
        err_msg = stderr.decode("latin-1").strip() or stdout.decode("latin-1").strip()
        raise RuntimeError(err_msg)

    logger.info("Configuracion aplicada correctamente.")


# ---------------------------------------------------------------------------
# Verificacion de privilegios
# ---------------------------------------------------------------------------
def check_privileges():
    """
    Comprueba si se ejecuta como administrador en Windows.

    Retorna
    -------
    True si es administrador, False en caso contrario.
    """
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


# ---------------------------------------------------------------------------
# GUI con Tkinter (Python 2.7)
# ---------------------------------------------------------------------------
class IPSwitcherGUI(object):
    """Ventana principal de IPSwitcher (version Python 2.7 / XP)."""

    # Colores - paleta mas sencilla compatible con Windows XP
    BG      = "#1e2235"
    PANEL   = "#252840"
    ACCENT  = "#00cfff"
    TEXT    = "#dce8f0"
    TEXT_D  = "#607080"
    SUCCESS = "#22c55e"
    ERROR   = "#ef4444"

    def __init__(self, root, profiles):
        """
        Inicializa la ventana principal.

        Parametros
        ----------
        root     : instancia Tk
        profiles : dict plano de perfiles
        """
        self.root     = root
        self.profiles = profiles
        self.adapters = []

        self._setup_window()
        self._build_ui()
        self._refresh_adapters()

    def _setup_window(self):
        """Configura la ventana principal."""
        self.root.title(t("title"))
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG)

        w, h = 560, 420
        sx   = self.root.winfo_screenwidth()
        sy   = self.root.winfo_screenheight()
        x    = (sx - w) // 2
        y    = (sy - h) // 2
        self.root.geometry("{}x{}+{}+{}".format(w, h, x, y))

    def _label(self, parent, text, fg=None, font=None, bg=None):
        """Helper para crear etiquetas con estilos comunes."""
        return tk.Label(
            parent,
            text=text,
            bg=bg or self.BG,
            fg=fg or self.TEXT,
            font=font or ("Courier New", 9),
        )

    def _build_ui(self):
        """Construye la interfaz."""
        # Titulo
        tk.Label(
            self.root,
            text="  IPSwitcher  v{}".format(APP_VERSION),
            bg=self.BG,
            fg=self.ACCENT,
            font=("Courier New", 14, "bold"),
        ).pack(pady=(14, 2), anchor="w", padx=16)

        tk.Frame(self.root, bg=self.ACCENT, height=1).pack(fill="x", padx=16)

        # Panel de seleccion
        panel = tk.Frame(self.root, bg=self.PANEL, bd=0)
        panel.pack(fill="x", padx=16, pady=8, ipady=6)

        # Adaptador
        tk.Label(panel, text=t("select_adapter"),
                 bg=self.PANEL, fg=self.TEXT_D,
                 font=("Courier New", 9)).grid(
            row=0, column=0, padx=10, pady=4, sticky="w"
        )

        self.adapter_var = tk.StringVar()
        self.cb_adapter  = ttk.Combobox(
            panel,
            textvariable=self.adapter_var,
            state="readonly",
            width=28,
        )
        self.cb_adapter.grid(row=0, column=1, padx=4, pady=4, sticky="w")
        self.cb_adapter.bind("<<ComboboxSelected>>", self._on_adapter_change)

        tk.Button(
            panel, text=t("btn_refresh"),
            bg=self.PANEL, fg=self.TEXT,
            font=("Courier New", 8),
            relief="flat", bd=1,
            command=self._refresh_adapters,
        ).grid(row=0, column=2, padx=6, pady=4)

        # Perfil
        tk.Label(panel, text=t("select_profile"),
                 bg=self.PANEL, fg=self.TEXT_D,
                 font=("Courier New", 9)).grid(
            row=1, column=0, padx=10, pady=4, sticky="w"
        )

        self.profile_var = tk.StringVar()
        self.cb_profile  = ttk.Combobox(
            panel,
            textvariable=self.profile_var,
            values=sorted(self.profiles.keys()),
            state="readonly",
            width=34,
        )
        self.cb_profile.grid(row=1, column=1, columnspan=2,
                             padx=4, pady=4, sticky="w")
        self.cb_profile.bind("<<ComboboxSelected>>", self._on_profile_change)

        # Detalle
        detail = tk.Frame(self.root, bg=self.PANEL, bd=0)
        detail.pack(fill="x", padx=16, pady=4, ipady=4)

        for col_idx, (lbl_text, attr) in enumerate([
            (t("new_ip"),  "lbl_ip"),
            (t("mask"),    "lbl_mask"),
            (t("gateway"), "lbl_gw"),
        ]):
            frm = tk.Frame(detail, bg=self.PANEL)
            frm.grid(row=0, column=col_idx, padx=12, sticky="w")

            tk.Label(frm, text=lbl_text,
                     bg=self.PANEL, fg=self.TEXT_D,
                     font=("Courier New", 8)).pack(anchor="w")
            lbl = tk.Label(frm, text="—",
                           bg=self.PANEL, fg=self.ACCENT,
                           font=("Courier New", 11, "bold"))
            lbl.pack(anchor="w")
            setattr(self, attr, lbl)

        # Boton aplicar
        tk.Button(
            self.root,
            text="▶  " + t("btn_apply"),
            bg=self.ACCENT, fg=self.BG,
            font=("Courier New", 11, "bold"),
            relief="flat",
            command=self._apply,
        ).pack(fill="x", padx=16, pady=(8, 4), ipady=6)

        # Log
        tk.Label(self.root, text="LOG",
                 bg=self.BG, fg=self.TEXT_D,
                 font=("Courier New", 8)).pack(anchor="w", padx=16)

        self.log_box = tk.Text(
            self.root,
            bg=self.PANEL, fg=self.TEXT,
            font=("Courier New", 9),
            relief="flat", height=7,
            state="disabled",
        )
        self.log_box.pack(fill="both", expand=True, padx=16, pady=(2, 14))
        self.log_box.tag_config("ok",  foreground=self.SUCCESS)
        self.log_box.tag_config("err", foreground=self.ERROR)
        self.log_box.tag_config("inf", foreground=self.ACCENT)

    def _refresh_adapters(self):
        """Recarga la lista de adaptadores."""
        self.adapters = get_network_adapters()
        self.cb_adapter.configure(values=self.adapters)
        if self.adapters:
            self.cb_adapter.current(0)
        self._log("inf", "Adaptadores: {}".format(len(self.adapters)))

    def _on_adapter_change(self, event=None):
        pass

    def _on_profile_change(self, event=None):
        """Actualiza etiquetas de detalle al cambiar perfil."""
        key = self.profile_var.get()
        if key and key in self.profiles:
            p = self.profiles[key]
            self.lbl_ip.configure(text=p["ip"])
            self.lbl_mask.configure(text=p["mask"])
            self.lbl_gw.configure(text=p["gateway"])

    def _apply(self):
        """Valida y aplica el perfil seleccionado."""
        adapter     = self.adapter_var.get().strip()
        profile_key = self.profile_var.get().strip()

        if not adapter:
            self._log("err", t("error_adapter", "(vacio)"))
            return
        if not profile_key:
            self._log("err", t("error_profile", "(vacio)"))
            return

        profile = self.profiles[profile_key]
        ok = messagebox.askyesno(
            t("confirm_title"),
            t("confirm_msg", profile["ip"], adapter),
        )
        if not ok:
            return

        # Hilo para no bloquear la GUI
        th = threading.Thread(
            target=self._apply_thread,
            args=(adapter, profile_key, profile),
        )
        th.daemon = True
        th.start()

    def _apply_thread(self, adapter, profile_key, profile):
        """Hilo de aplicacion del perfil."""
        self._log("inf", "Aplicando '{}' en '{}'...".format(profile_key, adapter))
        try:
            apply_profile(adapter, profile)
            self._log("ok", t("success"))
        except RuntimeError as exc:
            self._log("err", t("error_apply", str(exc)))

    def _log(self, tag, message):
        """Agrega una linea al widget de log."""
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n", tag)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")


# ---------------------------------------------------------------------------
# CLI (optparse, Python 2.7 - argparse no incluido en 2.7 stdlib para XP)
# ---------------------------------------------------------------------------
def build_parser():
    """Crea el parser de opciones compatible con Python 2.7."""
    parser = optparse.OptionParser(
        prog=APP_NAME,
        usage="%prog [opciones]",
        version="%prog {}".format(APP_VERSION),
    )
    parser.add_option(
        "--list",
        action="store_true",
        default=False,
        help="Lista los adaptadores disponibles.",
    )
    parser.add_option(
        "--adapter",
        metavar="NOMBRE",
        help="Nombre del adaptador de red.",
    )
    parser.add_option(
        "--profile",
        metavar="CLAVE",
        help='Clave del perfil (ej: "Linea 1 / Maquina 1 / Equipo 1").',
    )
    parser.add_option(
        "--gui",
        action="store_true",
        default=False,
        help="Abre la interfaz grafica.",
    )
    parser.add_option(
        "--lang",
        choices=["es", "en"],
        help="Idioma de la interfaz (es/en).",
    )
    return parser


def main():
    """Punto de entrada principal."""
    global LANG

    parser        = build_parser()
    opts, _args   = parser.parse_args()

    if opts.lang:
        LANG = opts.lang

    raw_data = load_profiles()
    profiles = get_flat_profiles(raw_data)

    if opts.list:
        adapters = get_network_adapters()
        print(t("list_header"))
        if not adapters:
            print("  " + t("no_adapters"))
        else:
            for i, a in enumerate(adapters, 1):
                print("  {:2}. {}".format(i, a))
        sys.exit(0)

    if opts.adapter and opts.profile:
        if not check_privileges():
            print("ERROR: " + t("error_root"))
            sys.exit(1)

        adapters = get_network_adapters()
        if opts.adapter not in adapters:
            print("ERROR: " + t("error_adapter", opts.adapter))
            sys.exit(1)

        if opts.profile not in profiles:
            print("ERROR: " + t("error_profile", opts.profile))
            sys.exit(1)

        try:
            apply_profile(opts.adapter, profiles[opts.profile])
            print(t("profile_applied", opts.profile, opts.adapter))
        except RuntimeError as exc:
            print("ERROR: " + t("error_apply", str(exc)))
            sys.exit(1)

        sys.exit(0)

    # GUI por defecto
    if tk is None:
        print("ERROR: Tkinter no disponible. Use --adapter y --profile.")
        sys.exit(1)

    root = tk.Tk()
    app  = IPSwitcherGUI(root, profiles)

    if not check_privileges():
        messagebox.showwarning(APP_NAME, t("error_root"))

    root.mainloop()


if __name__ == "__main__":
    main()
