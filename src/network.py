#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
network.py — Operaciones de red de IPSwitcher
=============================================
Encapsula toda la logica de sistema relacionada con la red:

- Deteccion de adaptadores de red (Linux / Windows).
- Consulta del hardware de cada adaptador.
- Aplicacion de configuracion IP estatica (iproute2 en Linux, netsh en Windows).
- Configuracion de DHCP automatico.

Dependencias del sistema
------------------------
Linux  : iproute2 (``ip``), udevadm, dhclient o dhcpcd.
Windows: netsh, ipconfig, PowerShell/WMI.
"""

import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from .constants import APP_NAME, _POPEN_FLAGS
from .i18n import t

logger = logging.getLogger(APP_NAME)

# Sistema operativo detectado una sola vez al importar el modulo
_OS = platform.system()


# ===========================================================================
# Deteccion de adaptadores
# ===========================================================================

def get_network_adapters() -> list[str]:
    """
    Devuelve la lista de nombres de adaptadores de red activos en el sistema.

    Linux  : Lee ``/sys/class/net`` excluyendo la interfaz de loopback ``lo``.
    Windows: Parsea la salida de ``netsh interface show interface``.

    Returns
    -------
    list[str]
        Lista ordenada alfabeticamente. Puede estar vacia si no se detectan
        adaptadores o el sistema operativo no esta soportado.
    """
    adapters: list[str] = []

    if _OS == "Linux":
        net_path = Path("/sys/class/net")
        if net_path.exists():
            adapters = [
                iface.name
                for iface in net_path.iterdir()
                if iface.name != "lo"
            ]

    elif _OS == "Windows":
        try:
            result = subprocess.run(
                ["netsh", "interface", "show", "interface"],
                capture_output=True, text=True, timeout=10, **_POPEN_FLAGS,
            )
            lines = [l for l in result.stdout.splitlines() if l.strip()]
            for line in lines[2:]:   # salta cabecera y separador de guiones
                parts = line.split()
                if len(parts) >= 4:
                    adapters.append(" ".join(parts[3:]))
        except (subprocess.SubprocessError, FileNotFoundError) as exc:
            logger.warning("No se pudo listar adaptadores (Windows): %s", exc)

    else:
        logger.warning("Sistema operativo no soportado: %s", _OS)

    return sorted(adapters)


# ===========================================================================
# Deteccion de hardware de adaptadores
# ===========================================================================

def get_adapter_hardware(adapter: str, _cache: Optional[dict] = None) -> str:
    """
    Devuelve una descripcion del hardware asociado a un adaptador de red.

    Linux  : Lee ``ID_MODEL_FROM_DATABASE`` / ``ID_MODEL`` de udevadm.
             Fallback al nombre del driver en
             ``/sys/class/net/<iface>/device/driver``.
    Windows: Usa el diccionario pre-cargado ``_cache`` generado por
             :func:`get_all_adapter_hardware` para evitar un proceso
             PowerShell por cada adaptador. Si no hay cache realiza una
             consulta individual (mas lenta).

    Parameters
    ----------
    adapter : str
        Nombre del adaptador (ej: ``'eth0'``, ``'Ethernet'``).
    _cache : dict, optional
        En Windows, dict ``{nombre_adaptador: descripcion}`` pre-cargado.
        Si es ``None`` se realiza la consulta individual.

    Returns
    -------
    str
        Descripcion del hardware o cadena vacia si no se pudo determinar.
    """
    if _OS == "Linux":
        try:
            result = subprocess.run(
                ["udevadm", "info", "--query=property",
                 "--path=/sys/class/net/{}".format(adapter)],
                capture_output=True, text=True, timeout=5, **_POPEN_FLAGS,
            )
            for line in result.stdout.splitlines():
                if line.startswith("ID_MODEL_FROM_DATABASE="):
                    return line.split("=", 1)[1].strip()
                if line.startswith("ID_MODEL="):
                    return line.split("=", 1)[1].strip()
        except Exception:
            pass

        driver_path = Path("/sys/class/net/{}/device/driver".format(adapter))
        if driver_path.is_symlink():
            return "drv:{}".format(Path(os.readlink(str(driver_path))).name)

        type_path = Path("/sys/class/net/{}/type".format(adapter))
        if type_path.exists():
            return "(virtual)"

    elif _OS == "Windows":
        if _cache is not None:
            return _cache.get(adapter, "")
        # Fallback individual si se llama sin cache
        try:
            script = (
                "Get-WmiObject Win32_NetworkAdapter | "
                "Where-Object {{ $_.NetConnectionID -eq '{name}' }} | "
                "Select-Object -ExpandProperty Name"
            ).format(name=adapter.replace("'", "''"))
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True, text=True, timeout=5, **_POPEN_FLAGS,
            )
            lines = result.stdout.strip().splitlines()
            if lines:
                return lines[0].strip()
        except Exception:
            pass

    return ""


def get_all_adapter_hardware() -> dict[str, str]:
    """
    Consulta el hardware de TODOS los adaptadores en una sola operacion.

    Linux  : Llama a :func:`get_adapter_hardware` por cada interfaz
             (udevadm es rapido y no abre ventana de consola).
    Windows: Una sola llamada PowerShell/WMI que devuelve todos los
             adaptadores serializados como JSON, evitando el parpadeo de
             consola que causaria un proceso por cada interfaz.

    Returns
    -------
    dict[str, str]
        ``{nombre_adaptador: descripcion_hardware}``.
        Diccionario vacio si la consulta falla.
    """
    result_map: dict[str, str] = {}

    if _OS == "Linux":
        for iface in get_network_adapters():
            hw = get_adapter_hardware(iface)
            if hw:
                result_map[iface] = hw

    elif _OS == "Windows":
        try:
            script = (
                "Get-WmiObject Win32_NetworkAdapter | "
                "Where-Object { $_.NetConnectionID -ne $null } | "
                "Select-Object NetConnectionID, Name | "
                "ConvertTo-Json -Compress"
            )
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True, text=True, timeout=10, **_POPEN_FLAGS,
            )
            raw = proc.stdout.strip()
            if raw:
                import json
                parsed = json.loads(raw)
                # PowerShell devuelve objeto unico (no array) si hay 1 sola NIC
                if isinstance(parsed, dict):
                    parsed = [parsed]
                for entry in parsed:
                    cid  = (entry.get("NetConnectionID") or "").strip()
                    name = (entry.get("Name") or "").strip()
                    if cid and name:
                        result_map[cid] = name
        except Exception as exc:
            logger.debug("get_all_adapter_hardware (Windows) fallo: %s", exc)

    return result_map


def get_current_ip(adapter: str) -> str:
    """
    Consulta la direccion IP actualmente asignada a un adaptador de red.

    Linux  : ``ip -o -4 addr show dev <adapter>``
    Windows: Parsea la salida de ``ipconfig`` buscando el bloque del adaptador.

    Parameters
    ----------
    adapter : str
        Nombre real del adaptador (sin etiqueta de hardware).

    Returns
    -------
    str
        Direccion IPv4 o cadena vacia si no se pudo determinar.
    """
    ip = ""
    try:
        if _OS == "Linux":
            result = subprocess.run(
                ["ip", "-o", "-4", "addr", "show", "dev", adapter],
                capture_output=True, text=True, **_POPEN_FLAGS,
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 4:
                    ip = parts[3].split("/")[0]
                    break

        elif _OS == "Windows":
            script = (
                "Get-NetIPAddress"
                " -InterfaceAlias '{name}'"
                " -AddressFamily IPv4"
                " -ErrorAction SilentlyContinue"
                " | Select-Object -ExpandProperty IPAddress"
            ).format(name=adapter.replace("'", "''"))
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True, text=True, timeout=5, **_POPEN_FLAGS,
            )
            lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
            if lines:
                ip = lines[0]
            except Exception:
                pass

            return ip


# ===========================================================================
# Aplicacion de configuracion IP
# ===========================================================================

def apply_profile(adapter: str, profile: dict) -> None:
    """
    Aplica una configuracion IP estatica a un adaptador de red.

    Delega en :func:`_apply_linux` o :func:`_apply_windows` segun el SO.

    Parameters
    ----------
    adapter : str
        Nombre del adaptador de red.
    profile : dict
        Diccionario con claves ``'ip'``, ``'mask'`` y ``'gateway'``.

    Raises
    ------
    RuntimeError
        Si el comando subyacente falla o el SO no esta soportado.
    """
    ip      = profile["ip"]
    mask    = profile["mask"]
    gateway = profile.get("gateway", "").strip()

    logger.info(
        t("log_applying", "{}/{}/{}".format(ip, mask, gateway), adapter)
    )

    if _OS == "Linux":
        _apply_linux(adapter, ip, mask, gateway)
    elif _OS == "Windows":
        _apply_windows(adapter, ip, mask, gateway)
    else:
        raise RuntimeError("Sistema operativo no soportado: {}".format(_OS))

    logger.info(t("log_success"))


def set_dhcp(adapter: str) -> None:
    """
    Configura un adaptador para obtener IP por DHCP automaticamente.

    Linux  : Usa ``dhclient`` o ``dhcpcd`` segun disponibilidad.
             Libera la concesion actual antes de solicitar una nueva.
    Windows: ``netsh interface ip set address source=dhcp``.

    Parameters
    ----------
    adapter : str
        Nombre del adaptador de red.

    Raises
    ------
    RuntimeError
        Si no hay cliente DHCP disponible, el comando falla o el SO no
        esta soportado.
    """
    if _OS == "Linux":
        subprocess.run(
            ["ip", "addr", "flush", "dev", adapter],
            capture_output=True,
        )
        if shutil.which("dhclient"):
            _run(["dhclient", "-r", adapter])
            _run(["dhclient", adapter])
        elif shutil.which("dhcpcd"):
            _run(["dhcpcd", adapter])
        else:
            raise RuntimeError(
                "No se encontro dhclient ni dhcpcd. "
                "Instala isc-dhcp-client: sudo apt install isc-dhcp-client"
            )

    elif _OS == "Windows":
        _run([
            "netsh", "interface", "ip", "set", "address",
            "name={}".format(adapter), "source=dhcp",
        ])
    else:
        raise RuntimeError("Sistema operativo no soportado: {}".format(_OS))


# ===========================================================================
# Helpers privados
# ===========================================================================

def _run(cmd: list[str]) -> None:
    """
    Ejecuta un comando del sistema y lanza ``RuntimeError`` si falla.

    Parameters
    ----------
    cmd : list[str]
        Tokens del comando a ejecutar.

    Raises
    ------
    RuntimeError
        Con el mensaje de error de stderr (o stdout si stderr esta vacio).
    """
    logger.debug("Ejecutando: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, **_POPEN_FLAGS)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def _mask_to_cidr(mask: str) -> int:
    """
    Convierte mascara en notacion decimal punteada a longitud de prefijo CIDR.

    Parameters
    ----------
    mask : str
        Mascara en formato ``'x.x.x.x'`` (ej: ``'255.255.255.0'``).

    Returns
    -------
    int
        Longitud del prefijo (ej: 24).
    """
    return sum(bin(int(octet)).count("1") for octet in mask.split("."))


def _find_adapter_with_ip(ip: str) -> Optional[str]:
    """
    Busca en que adaptador del sistema esta asignada una direccion IP.

    Solo funciona en Linux. Recorre la salida de ``ip -o -4 addr show``.

    Parameters
    ----------
    ip : str
        Direccion IPv4 a buscar (sin mascara).

    Returns
    -------
    str or None
        Nombre del adaptador que tiene esa IP, o ``None`` si no se encuentra.
    """
    try:
        result = subprocess.run(
            ["ip", "-o", "-4", "addr", "show"],
            capture_output=True, text=True, **_POPEN_FLAGS,
        )
        for line in result.stdout.splitlines():
            # Formato: "2: eth0    inet 192.168.1.10/24 ..."
            parts = line.split()
            if len(parts) >= 4:
                addr = parts[3].split("/")[0]
                if addr == ip:
                    return parts[1].rstrip(":")
    except Exception:
        pass
    return None


def _apply_linux(adapter: str, ip: str, mask: str, gateway: str) -> None:
    """
    Aplica configuracion IP en Linux usando iproute2.

    Pasos:
    1. Comprueba conflictos de IP en otros adaptadores.
    2. Elimina las direcciones IP previas del adaptador destino.
    3. Asigna la nueva IP con prefijo CIDR.
    4. Levanta el interfaz si estuviera caido.
    5. Establece la ruta predeterminada si se indico gateway.

    Parameters
    ----------
    adapter : str
        Nombre del interfaz (ej: ``'eth0'``, ``'enp3s0'``).
    ip      : str
        Direccion IPv4 a asignar.
    mask    : str
        Mascara de subred.
    gateway : str
        Puerta de enlace predeterminada. Cadena vacia para no configurar.

    Raises
    ------
    RuntimeError
        Si la IP ya esta asignada a otro adaptador o el comando falla.
    """
    cidr = _mask_to_cidr(mask)

    # La comprobacion de conflicto se hace ANTES de cualquier modificacion
    # para no dejar el adaptador sin IP si hay conflicto.
    existing = _find_adapter_with_ip(ip)
    if existing and existing != adapter:
        raise RuntimeError(t("error_ip_in_use", ip, existing))

    # Si la IP ya esta en este adaptador no hay nada que hacer
    if existing == adapter:
        return

    _run(["ip", "addr", "flush", "dev", adapter])
    _run(["ip", "addr", "add", "{}/{}".format(ip, cidr), "dev", adapter])
    _run(["ip", "link", "set", adapter, "up"])

    if gateway:
        subprocess.run(
            ["ip", "route", "del", "default", "dev", adapter],
            capture_output=True, **_POPEN_FLAGS,
        )
        _run(["ip", "route", "add", "default", "via", gateway, "dev", adapter])


def _apply_windows(adapter: str, ip: str, mask: str, gateway: str) -> None:
    """
    Aplica configuracion IP en Windows usando netsh.

    Parameters
    ----------
    adapter : str
        Nombre del adaptador (ej: ``'Local Area Connection'``).
    ip      : str
        Direccion IPv4 a asignar.
    mask    : str
        Mascara de subred.
    gateway : str
        Puerta de enlace predeterminada. Cadena vacia para no configurar.

    Raises
    ------
    RuntimeError
        Si el comando netsh falla.
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
