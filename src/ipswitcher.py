#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPSwitcher - Network IP Address Switcher
========================================
Aplicación para cambiar la dirección IPv4 de adaptadores de red
a partir de perfiles almacenados en un archivo JSON.

Versión   : 1.1.0
Plataforma: Windows 7/10/11 y Linux (Python 3.10+)
Autor     : IPSwitcher Project
Repositorio: https://github.com/WhiteHornet13/IPSwitcher

Uso en consola:
    python ipswitcher.py --list
    python ipswitcher.py --adapter "eth0" --profile "Linea 1/Maquina 1/Equipo 1"
    python ipswitcher.py --gui

Requiere privilegios de administrador / root para aplicar cambios de red.
"""

import os
import sys
import json
import locale
import logging
import argparse
import platform
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constantes globales
# ---------------------------------------------------------------------------
APP_NAME    = "IPSwitcher"
APP_VERSION = "1.0.0"
APP_REPO    = "https://github.com/WhiteHornet13/IPSwitcher"

# Resolución de la ruta al JSON de perfiles.
# Si la app está compilada con PyInstaller, los datos están junto al ejecutable.
if getattr(sys, "frozen", False):
    _BASE_DIR = Path(sys.executable).parent
else:
    _BASE_DIR = Path(__file__).resolve().parent.parent   # raíz del proyecto

PROFILES_FILE = _BASE_DIR / "ips.json"

# ---------------------------------------------------------------------------
# Internacionalización (i18n)
# ---------------------------------------------------------------------------
STRINGS = {
    "es": {
        "title"            : "IP Switcher - Cambio de IP",
        "select_adapter"   : "Adaptador de red:",
        "select_profile"   : "Perfil de IP:",
        "btn_apply"        : "Aplicar",
        "btn_refresh"      : "Actualizar",
        "success"          : "IP aplicada correctamente.",
        "error_root"       : "Esta aplicación requiere privilegios de administrador.",
        "error_load"       : "No se pudo cargar el archivo de perfiles: {}",
        "error_adapter"    : "No se encontró el adaptador: {}",
        "error_profile"    : "No se encontró el perfil: {}",
        "error_apply"      : "Error al aplicar la configuración: {}",
        "no_adapters"      : "No se detectaron adaptadores de red.",
        "list_header"      : "Adaptadores de red disponibles:",
        "profile_applied"  : "Perfil '{}' aplicado al adaptador '{}'.",
        "current_ip"       : "IP actual",
        "new_ip"           : "Nueva IP",
        "mask"             : "Máscara",
        "gateway"          : "Puerta de enlace",
        "destino"          : "IP Destino",
        "log_applying"     : "Aplicando perfil '{}' en adaptador '{}'...",
        "log_success"      : "Configuración aplicada correctamente.",
        "confirm_title"    : "Confirmar cambio",
        "error_ip_in_use"  : "La IP {} ya está asignada al adaptador '{}'.",
        "confirm_msg"      : "¿Aplicar IP {} al adaptador {}?",
    },
    "en": {
        "title"            : "IP Switcher - IP Changer",
        "select_adapter"   : "Network adapter:",
        "select_profile"   : "IP profile:",
        "btn_apply"        : "Apply",
        "btn_refresh"      : "Refresh",
        "success"          : "IP applied successfully.",
        "error_root"       : "This application requires administrator privileges.",
        "error_load"       : "Could not load profiles file: {}",
        "error_adapter"    : "Adapter not found: {}",
        "error_profile"    : "Profile not found: {}",
        "error_apply"      : "Error applying configuration: {}",
        "no_adapters"      : "No network adapters detected.",
        "list_header"      : "Available network adapters:",
        "profile_applied"  : "Profile '{}' applied to adapter '{}'.",
        "current_ip"       : "Current IP",
        "new_ip"           : "New IP",
        "mask"             : "Subnet mask",
        "gateway"          : "Gateway",
        "destino"          : "Target IP",
        "log_applying"     : "Applying profile '{}' on adapter '{}'...",
        "log_success"      : "Configuration applied successfully.",
        "confirm_title"    : "Confirm change",
        "error_ip_in_use"  : "IP {} is already assigned to adapter '{}'.",
        "confirm_msg"      : "Apply IP {} to adapter {}?",
    },
}


def detect_language() -> str:
    """
    Detecta el idioma del sistema operativo.

    Devuelve 'es' si el idioma del sistema comienza por 'es',
    en cualquier otro caso devuelve 'en'.
    """
    try:
        lang, _ = locale.getdefaultlocale()
        if lang and lang.lower().startswith("es"):
            return "es"
    except Exception:
        pass
    return "en"


# Idioma activo (se puede sobreescribir con argumento --lang)
LANG = detect_language()


def t(key: str, *args) -> str:
    """
    Traduce una clave al idioma activo.

    Parameters
    ----------
    key  : clave del diccionario de traducciones
    args : argumentos opcionales para format()

    Returns
    -------
    Cadena traducida; si la clave no existe devuelve la clave misma.
    """
    text = STRINGS.get(LANG, STRINGS["en"]).get(key, key)
    if args:
        text = text.format(*args)
    return text


# ---------------------------------------------------------------------------
# Configuración del logger
# ---------------------------------------------------------------------------
def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    Configura y devuelve el logger principal de la aplicación.

    Parameters
    ----------
    verbose : Si True activa nivel DEBUG, si False usa INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    fmt   = "[%(asctime)s] %(levelname)s - %(message)s"
    logging.basicConfig(level=level, format=fmt, datefmt="%H:%M:%S")
    return logging.getLogger(APP_NAME)


logger = setup_logging()


# ---------------------------------------------------------------------------
# Carga de perfiles desde JSON
# ---------------------------------------------------------------------------
def load_profiles(path: Path = PROFILES_FILE) -> dict:
    """
    Carga el archivo JSON de perfiles de IP.

    El esquema esperado es:
    {
        "IPs": {
            "lineas": [
                {
                    "nombre": "...",
                    "maquinas": [
                        {
                            "nombre": "...",
                            "equipos": [
                                {
                                    "nombre"    : "...",
                                    "IP-PC"     : "x.x.x.x",
                                    "Mascara"   : "x.x.x.x",
                                    "IP-Destino": "x.x.x.x"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }

    Parameters
    ----------
    path : Ruta al archivo JSON

    Returns
    -------
    dict con los perfiles cargados

    Raises
    ------
    SystemExit si el archivo no existe o tiene formato incorrecto.
    """
    if not path.exists():
        msg = t("error_load", str(path))
        logger.error(msg)
        # Mostrar diálogo aunque no haya ventana principal aún
        try:
            _root = tk.Tk()
            _root.withdraw()
            messagebox.showerror(APP_NAME, msg)
            _root.destroy()
        except Exception:
            pass
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, IOError) as exc:
        msg = t("error_load", exc)
        logger.error(msg)
        try:
            _root = tk.Tk()
            _root.withdraw()
            messagebox.showerror(APP_NAME, msg)
            _root.destroy()
        except Exception:
            pass
        sys.exit(1)

    return data


def get_flat_profiles(data: dict) -> dict[str, dict]:
    """
    Aplana la estructura jerárquica del JSON en un diccionario plano.

    La clave resultante tiene el formato:
        "Linea X / Maquina Y / Equipo Z"

    Parameters
    ----------
    data : dict cargado desde el JSON

    Returns
    -------
    dict { "Linea X / Maquina Y / Equipo Z": { ip, mask, destino } }
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
                    "destino": equipo.get("IP-Destino", ""), #solo informativo no se usa de momento
                    "gateway":""  #siempre en blanco
                }
    return flat


# ---------------------------------------------------------------------------
# Detección de adaptadores de red
# ---------------------------------------------------------------------------
def get_network_adapters() -> list[str]:
    """
    Devuelve la lista de nombres de adaptadores de red activos en el sistema.

    En Linux usa el directorio /sys/class/net.
    En Windows usa 'netsh interface show interface'.

    Returns
    -------
    Lista de nombres de adaptadores (puede estar vacía).
    """
    adapters: list[str] = []
    os_name = platform.system()

    if os_name == "Linux":
        # /sys/class/net lista todos los interfaces, incluido 'lo'
        net_path = Path("/sys/class/net")
        if net_path.exists():
            adapters = [
                iface.name
                for iface in net_path.iterdir()
                if iface.name != "lo"                 # excluir loopback
            ]

    elif os_name == "Windows":
        try:
            result = subprocess.run(
                ["netsh", "interface", "show", "interface"],
                capture_output=True, text=True, timeout=10,
            )
            # Cada línea de la salida contiene el nombre del adaptador al final
            for line in result.stdout.splitlines():
                parts = line.split()
                # Líneas de datos tienen al menos 4 columnas
                if len(parts) >= 4 and parts[0] not in ("Admin", "---"):
                    adapters.append(" ".join(parts[3:]))
        except (subprocess.SubprocessError, FileNotFoundError) as exc:
            logger.warning("No se pudo listar adaptadores (Windows): %s", exc)

    else:
        logger.warning("Sistema operativo no soportado: %s", os_name)

    return sorted(adapters)


# ---------------------------------------------------------------------------
# Aplicación del perfil de IP
# ---------------------------------------------------------------------------
def apply_profile(adapter: str, profile: dict) -> None:
    """
    Aplica una configuración IP fija a un adaptador de red.

    En Linux usa el comando 'ip addr' e 'ip route'.
    En Windows usa 'netsh interface ip set address'.

    Parameters
    ----------
    adapter : Nombre del adaptador de red
    profile : dict con claves 'ip', 'mask', 'gateway'

    Raises
    ------
    RuntimeError si el comando falla o el SO no está soportado.
    """
    ip      = profile["ip"]
    mask    = profile["mask"]
    gateway = profile.get("gateway", "").strip()
    os_name = platform.system()

    logger.info(t("log_applying", "{}/{}/{}".format(ip, mask, gateway), adapter))

    if os_name == "Linux":
        _apply_linux(adapter, ip, mask, gateway)

    elif os_name == "Windows":
        _apply_windows(adapter, ip, mask, gateway)

    else:
        raise RuntimeError("Sistema operativo no soportado: {}".format(os_name))

    logger.info(t("log_success"))


def _mask_to_cidr(mask: str) -> int:
    """
    Convierte una máscara en notación decimal punteada a prefijo CIDR.

    Ejemplo: '255.255.255.0' → 24

    Parameters
    ----------
    mask : Máscara en formato 'x.x.x.x'

    Returns
    -------
    Longitud del prefijo como entero.
    """
    return sum(bin(int(octet)).count("1") for octet in mask.split("."))


def _run(cmd: list[str]) -> None:
    """
    Ejecuta un comando del sistema y lanza RuntimeError si falla.

    Parameters
    ----------
    cmd : Lista de tokens del comando
    """
    logger.debug("Ejecutando: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())

def _find_adapter_with_ip(ip: str) -> str | None:
    """
    Busca en qué adaptador del sistema está asignada una dirección IP.

    Recorre /sys/class/net y lee la dirección de cada interfaz mediante
    'ip addr show'. Solo funciona en Linux.

    Parameters
    ----------
    ip : Dirección IPv4 a buscar (sin máscara)

    Returns
    -------
    Nombre del adaptador que ya tiene esa IP, o None si no se encuentra.
    """
    try:
        result = subprocess.run(
            ["ip", "-o", "-4", "addr", "show"],
            capture_output=True, text=True,
        )
        for line in result.stdout.splitlines():
            # Formato: "2: eth0    inet 192.168.1.10/24 ..."
            parts = line.split()
            if len(parts) >= 4:
                addr = parts[3].split("/")[0]   # quitar el prefijo CIDR
                if addr == ip:
                    return parts[1]             # nombre del adaptador
    except Exception:
        pass
    return None



def _apply_linux(adapter: str, ip: str, mask: str, gateway: str) -> None:
    """
    Aplica configuración IP en Linux usando iproute2.

    Pasos:
    1. Elimina direcciones IP previas del adaptador.
    2. Asigna la nueva IP con máscara CIDR.
    3. Establece la puerta de enlace predeterminada.

    Parameters
    ----------
    adapter : Nombre del interfaz (ej: 'eth0', 'enp3s0')
    ip      : Dirección IP a asignar
    mask    : Máscara de subred
    gateway : Puerta de enlace predeterminada
    """
    cidr = _mask_to_cidr(mask)

    # Comprueba si la IP ya está en uso en OTRO adaptador
    existing = _find_adapter_with_ip(ip)
    if existing and existing != adapter:
        raise RuntimeError(t("error_ip_in_use", ip, existing))

    # Elimina IPs existentes para evitar conflictos
    _run(["ip", "addr", "flush", "dev", adapter])

    # Asigna la nueva dirección
    _run(["ip", "addr", "add", "{}/{}".format(ip, cidr), "dev", adapter])

    # Levanta el interfaz por si estuviera caído
    _run(["ip", "link", "set", adapter, "up"])

    # Establece la ruta predeterminada solo si se ha especificado gateway
    # Primero borra rutas default existentes para evitar duplicados
    if gateway:
        subprocess.run(
            ["ip", "route", "del", "default", "dev", adapter],
            capture_output=True,
        )
        _run(["ip", "route", "add", "default", "via", gateway, "dev", adapter])


def _apply_windows(adapter: str, ip: str, mask: str, gateway: str) -> None:
    """
    Aplica configuración IP en Windows usando netsh.

    Parameters
    ----------
    adapter : Nombre del adaptador (ej: 'Local Area Connection')
    ip      : Dirección IP a asignar
    mask    : Máscara de subred
    gateway : Puerta de enlace predeterminada
    """
    cmd = [
        "netsh", "interface", "ip", "set", "address",
        "name={}".format(adapter),
        "source=static",
        "address={}".format(ip),
        "mask={}".format(mask),
    ]
    if gateway:
        cmd += ["gateway={}".format(gateway), "gwmetric=1"]
    _run(cmd)


# ---------------------------------------------------------------------------
# Verificación de privilegios
# ---------------------------------------------------------------------------
def check_privileges() -> bool:
    """
    Comprueba si la aplicación se está ejecutando con privilegios de root/admin.

    Returns
    -------
    True si tiene privilegios suficientes, False en caso contrario.
    """
    if platform.system() == "Windows":
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    else:
        return os.geteuid() == 0


# ---------------------------------------------------------------------------
# Interfaz de línea de comandos (CLI)
# ---------------------------------------------------------------------------
def cli_list(adapters: list[str]) -> None:
    """Imprime la lista de adaptadores de red disponibles."""
    print(t("list_header"))
    if not adapters:
        print("  " + t("no_adapters"))
    else:
        for i, adapter in enumerate(adapters, 1):
            print("  {:2}. {}".format(i, adapter))


def cli_apply(adapter: str, profile_key: str, profiles: dict[str, dict]) -> None:
    """
    Aplica un perfil de IP por nombre de adaptador y clave de perfil.

    Parameters
    ----------
    adapter     : Nombre exacto del adaptador
    profile_key : Clave del perfil en formato "Linea X / Maquina Y / Equipo Z"
    profiles    : Diccionario plano de perfiles
    """
    adapters = get_network_adapters()
    if adapter not in adapters:
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


# ---------------------------------------------------------------------------
# Interfaz gráfica (GUI) con Tkinter
# ---------------------------------------------------------------------------
class IPSwitcherGUI:
    """
    Ventana principal de la aplicación IPSwitcher.

    Estructura de la GUI:
    ┌──────────────────────────────────────┐
    │ Título                               │
    ├──────────────────────────────────────┤
    │ Adaptador: [ComboBox]   [Actualizar] │
    │ Perfil:    [ComboBox]                │
    │ IP:  ...   Máscara: ...  GW: ...     │
    ├──────────────────────────────────────┤
    │ [          Aplicar          ]        │
    ├──────────────────────────────────────┤
    │ Log de mensajes                      │
    └──────────────────────────────────────┘
    """

    # Paleta de colores de la aplicación
    COLORS = {
        "bg"        : "#1a1d2e",   # fondo principal (azul noche)
        "panel"     : "#252840",   # fondo de paneles
        "accent"    : "#00d4ff",   # cian eléctrico
        "accent2"   : "#7c3aed",   # violeta
        "text"      : "#e2e8f0",   # texto principal
        "text_dim"  : "#64748b",   # texto secundario
        "success"   : "#22c55e",   # verde éxito
        "error"     : "#ef4444",   # rojo error
        "warning"   : "#f59e0b",   # naranja aviso
        "border"    : "#334155",   # borde sutil
    }

    def __init__(self, root: tk.Tk, profiles: dict[str, dict]) -> None:
        """
        Inicializa la ventana principal.

        Parameters
        ----------
        root     : Instancia de Tk raíz
        profiles : Diccionario plano de perfiles { clave: {ip, mask, gateway} }
        """
        self.root     = root
        self.profiles = profiles
        self.adapters : list[str] = []

        self._setup_window()
        self._build_ui()
        self._refresh_adapters()

    # ------------------------------------------------------------------
    # Configuración de la ventana
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        """Configura propiedades básicas de la ventana principal."""
        self.root.title(t("title"))
        self.root.resizable(False, False)
        self.root.configure(bg=self.COLORS["bg"])

        # Centrar en pantalla
        w, h = 600, 520
        sx   = self.root.winfo_screenwidth()
        sy   = self.root.winfo_screenheight()
        x    = (sx - w) // 2
        y    = (sy - h) // 2
        self.root.geometry("{}x{}+{}+{}".format(w, h, x, y))

        # Icono — .ico en Windows, .png en Linux
        try:
            ico_path = _BASE_DIR / "assets" / "ipswitcher.ico"
            png_path = _BASE_DIR / "assets" / "ipswitcher.png"
            if ico_path.exists():
                self.root.iconbitmap(str(ico_path))
            elif png_path.exists():
                img = tk.PhotoImage(file=str(png_path))
                self.root.iconphoto(True, img)
        except Exception:
            pass

        # Estilos ttk
        self._configure_styles()

    def _configure_styles(self) -> None:
        """Define estilos personalizados para los widgets ttk."""
        style = ttk.Style(self.root)
        style.theme_use("clam")

        c = self.COLORS

        # Marco general
        style.configure("App.TFrame",     background=c["bg"])
        style.configure("Panel.TFrame",   background=c["panel"])

        # Etiquetas
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

        # ComboBox — colores del campo y del texto seleccionado
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
            fieldbackground=[("readonly", c["panel"]),
                             ("disabled", c["bg"])],
            foreground=[("readonly", c["text"]),
                        ("disabled", c["text_dim"])],
            selectbackground=[("readonly", c["accent2"])],
            selectforeground=[("readonly", c["text"])],
            background=[("readonly", c["accent"]),
                        ("active",   c["accent2"])],
        )
        # Forzar colores internos de la lista desplegable
        self.root.option_add("*TCombobox*Listbox.background",      c["panel"])
        self.root.option_add("*TCombobox*Listbox.foreground",      c["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", c["accent2"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", c["text"])
        self.root.option_add("*TCombobox*Listbox.font",            "DejaVu Sans Mono 10")

        # Botón principal
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

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Construye y dispone todos los widgets de la interfaz."""
        c = self.COLORS
        pad = {"padx": 18, "pady": 6}

        # ── Título ──────────────────────────────────────────────────────
        header = ttk.Frame(self.root, style="App.TFrame")
        header.pack(fill="x", padx=18, pady=(18, 4))

        ttk.Label(
            header, text="◈  " + APP_NAME, style="Title.TLabel"
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

        # Separador
        tk.Frame(self.root, bg=c["accent"], height=1).pack(
            fill="x", padx=18, pady=(4, 10)
        )

        # ── Panel de selección ──────────────────────────────────────────
        sel_frame = ttk.Frame(self.root, style="Panel.TFrame")
        sel_frame.pack(fill="x", padx=18, pady=4, ipady=10)

        # Fila adaptador
        row1 = ttk.Frame(sel_frame, style="Panel.TFrame")
        row1.pack(fill="x", padx=12, pady=(8, 4))

        tk.Label(
            row1, text=t("select_adapter"),
            bg=c["panel"], fg=c["text_dim"],
            font=("DejaVu Sans Mono", 9),
        ).pack(side="left")

        self.adapter_var = tk.StringVar()
        self.cb_adapter  = ttk.Combobox(
            row1,
            textvariable=self.adapter_var,
            state="readonly",
            width=28,
            style="App.TCombobox",
        )
        self.cb_adapter.pack(side="left", padx=(8, 0))
        self.cb_adapter.bind("<<ComboboxSelected>>", self._on_adapter_change)

        tk.Button(
            row1,
            text="⟳ " + t("btn_refresh"),
            bg=c["accent"],
            fg=c["bg"],
            activebackground=c["accent2"],
            activeforeground=c["text"],
            font=("DejaVu Sans Mono", 9, "bold"),
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._refresh_adapters,
        ).pack(side="left", padx=(8, 0))

        # Fila perfil
        row2 = ttk.Frame(sel_frame, style="Panel.TFrame")
        row2.pack(fill="x", padx=12, pady=4)

        tk.Label(
            row2, text=t("select_profile"),
            bg=c["panel"], fg=c["text_dim"],
            font=("DejaVu Sans Mono", 9),
        ).pack(side="left")

        self.profile_var = tk.StringVar()
        self.cb_profile  = ttk.Combobox(
            row2,
            textvariable=self.profile_var,
            values=sorted(self.profiles.keys()),
            state="readonly",
            width=36,
            style="App.TCombobox",
        )
        self.cb_profile.pack(side="left", padx=(8, 0))
        self.cb_profile.bind("<<ComboboxSelected>>", self._on_profile_change)

        # ── Detalle del perfil seleccionado ─────────────────────────────
        detail_frame = ttk.Frame(self.root, style="Panel.TFrame")
        detail_frame.pack(fill="x", padx=18, pady=4, ipady=8)

        for label, var_name in [
            (t("new_ip"),   "lbl_ip"),
            (t("mask"),     "lbl_mask"),
            (t("destino"),  "lbl_gw"),
        ]:
            col = ttk.Frame(detail_frame, style="Panel.TFrame")
            col.pack(side="left", expand=True, fill="x", padx=12)

            tk.Label(
                col, text=label,
                bg=c["panel"], fg=c["text_dim"],
                font=("DejaVu Sans Mono", 8),
            ).pack(anchor="w")

            lbl = tk.Label(
                col, text="—",
                bg=c["panel"], fg=c["accent"],
                font=("DejaVu Sans Mono", 11, "bold"),
            )
            lbl.pack(anchor="w")
            setattr(self, var_name, lbl)

        # ── Botón Aplicar ────────────────────────────────────────────────
        ttk.Button(
            self.root,
            text="▶  " + t("btn_apply"),
            style="Apply.TButton",
            command=self._apply,
        ).pack(fill="x", padx=18, pady=(10, 4))

        # ── Log de mensajes ──────────────────────────────────────────────
        log_frame = ttk.Frame(self.root, style="App.TFrame")
        log_frame.pack(fill="both", expand=True, padx=18, pady=(4, 16))

        tk.Label(
            log_frame, text="LOG",
            bg=c["bg"], fg=c["text_dim"],
            font=("DejaVu Sans Mono", 8),
        ).pack(anchor="w")

        self.log_box = tk.Text(
            log_frame,
            bg=c["panel"], fg=c["text"],
            font=("DejaVu Sans Mono", 9),
            relief="flat",
            height=8,
            state="disabled",
            bd=0,
            wrap="word",
        )
        self.log_box.pack(fill="both", expand=True)

        # Tags de color para el log
        self.log_box.tag_configure("ok",      foreground=c["success"])
        self.log_box.tag_configure("err",     foreground=c["error"])
        self.log_box.tag_configure("info",    foreground=c["accent"])
        self.log_box.tag_configure("warning", foreground=c["warning"])

    # ------------------------------------------------------------------
    # Eventos y lógica
    # ------------------------------------------------------------------

    def _refresh_adapters(self) -> None:
        """Actualiza la lista de adaptadores de red disponibles."""
        self.adapters = get_network_adapters()
        self.cb_adapter.configure(values=self.adapters)
        if self.adapters:
            self.cb_adapter.current(0)
        self._log("info", "Adaptadores detectados: {}".format(len(self.adapters)))

    def _on_adapter_change(self, _event=None) -> None:
        """Callback al cambiar el adaptador seleccionado."""
        self.cb_adapter.selection_clear()
        self._log("info", "Adaptador: {}".format(self.adapter_var.get()))

    def _on_profile_change(self, _event=None) -> None:
        """Callback al cambiar el perfil; actualiza los labels de detalle."""
        self.cb_profile.selection_clear()
        key = self.profile_var.get()
        if key and key in self.profiles:
            p = self.profiles[key]
            self.lbl_ip.configure(text=p["ip"])
            self.lbl_mask.configure(text=p["mask"])
            self.lbl_gw.configure(text=p["destino"])

    def _apply(self) -> None:
        """Valida la selección y aplica el perfil en un hilo separado."""
        adapter = self.adapter_var.get().strip()
        profile_key = self.profile_var.get().strip()

        if not adapter:
            self._log("err", t("error_adapter", "(vacío)"))
            return
        if not profile_key:
            self._log("err", t("error_profile", "(vacío)"))
            return

        # Pide confirmación al usuario
        profile = self.profiles[profile_key]
        ok = messagebox.askyesno(
            t("confirm_title"),
            t("confirm_msg", profile["ip"], adapter),
            parent=self.root,
        )
        if not ok:
            return

        # Ejecuta en hilo para no bloquear la GUI
        threading.Thread(
            target=self._apply_thread,
            args=(adapter, profile_key, profile),
            daemon=True,
        ).start()

    def _apply_thread(self, adapter: str, profile_key: str, profile: dict) -> None:
        """
        Hilo de aplicación del perfil.
        Actualiza el log con el resultado.
        """
        self._log("info", t("log_applying", profile_key, adapter))
        try:
            apply_profile(adapter, profile)
            self._log("ok", t("success"))
        except RuntimeError as exc:
            self._log("err", t("error_apply", exc))

    def _log(self, tag: str, message: str) -> None:
        """
        Añade un mensaje al widget de log con el color correspondiente.

        Parameters
        ----------
        tag     : 'ok', 'err', 'info', 'warning'
        message : Texto a mostrar
        """
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n", tag)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")


# ---------------------------------------------------------------------------
# Punto de entrada principal
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """
    Construye y devuelve el parser de argumentos de línea de comandos.

    Argumentos:
    --list              Lista los adaptadores disponibles y sale.
    --adapter NOMBRE    Nombre del adaptador a configurar.
    --profile CLAVE     Clave del perfil en formato "Linea/Maquina/Equipo".
    --gui               Abre la interfaz gráfica (por defecto si no hay args).
    --lang {es,en}      Fuerza el idioma de la interfaz.
    --verbose           Activa mensajes de depuración.
    """
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description="Cambia la IP de adaptadores de red a partir de perfiles JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  ipswitcher --list\n"
            '  ipswitcher --adapter eth0 --profile "Linea 1 / Maquina 1 / Equipo 1"\n'
            "  ipswitcher --gui\n"
        ),
    )
    parser.add_argument("--list",    action="store_true",    help="Lista adaptadores disponibles.")
    parser.add_argument("--adapter", metavar="NOMBRE",       help="Nombre del adaptador.")
    parser.add_argument("--profile", metavar="CLAVE",        help="Clave del perfil de IP.")
    parser.add_argument("--gui",     action="store_true",    help="Abre la interfaz gráfica.")
    parser.add_argument("--lang",    choices=["es", "en"],   help="Idioma de la interfaz.")
    parser.add_argument("--verbose", action="store_true",    help="Modo verbose (debug).")
    parser.add_argument("--version", action="version",       version="{} {}".format(APP_NAME, APP_VERSION))
    return parser


def main() -> None:
    """
    Función principal.

    Flujo:
    1. Parsea argumentos.
    2. Configura idioma y logging.
    3. Carga perfiles JSON.
    4. Según los argumentos: lista, aplica o abre GUI.
    """
    global LANG

    parser = build_parser()
    args   = parser.parse_args()

    # Idioma
    if args.lang:
        LANG = args.lang

    # Logging
    if args.verbose:
        logging.getLogger(APP_NAME).setLevel(logging.DEBUG)

    # Carga de perfiles
    raw_data = load_profiles()
    profiles = get_flat_profiles(raw_data)

    # ── Modo --list ──────────────────────────────────────────────────────
    if args.list:
        cli_list(get_network_adapters())
        sys.exit(0)

    # ── Modo --adapter + --profile ───────────────────────────────────────
    if args.adapter and args.profile:
        if not check_privileges():
            logger.error(t("error_root"))
            sys.exit(1)
        cli_apply(args.adapter, args.profile, profiles)
        sys.exit(0)

    # ── Modo GUI (por defecto o con --gui) ───────────────────────────────
    root = tk.Tk()
    app  = IPSwitcherGUI(root, profiles)

    if not check_privileges():
        messagebox.showwarning(APP_NAME, t("error_root"))

    root.mainloop()


if __name__ == "__main__":
    main()
