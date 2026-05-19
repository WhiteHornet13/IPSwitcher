#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
i18n.py — Internacionalizacion de IPSwitcher
=============================================
Proporciona todas las cadenas de texto de la interfaz en español e ingles,
deteccion automatica del idioma del sistema operativo y una funcion de
traduccion ``t()`` utilizada en toda la aplicacion.

Uso tipico
----------
    from src.i18n import t, set_language

    set_language("es")           # forzar idioma
    print(t("btn_apply"))        # "Aplicar"
    print(t("error_load", "/x")) # "No se pudo cargar el archivo de perfiles: /x"
"""

import locale

# ---------------------------------------------------------------------------
# Diccionario de traducciones
# ---------------------------------------------------------------------------

_STRINGS: dict[str, dict[str, str]] = {
    "es": {
        "title"            : "IP Switcher - Cambio de IP",
        "select_adapter"   : "Adaptador de red:",
        "select_profile"   : "Perfil de IP:",
        "btn_apply"        : "Aplicar",
        "btn_refresh"      : "Actualizar",
        "success"          : "IP aplicada correctamente.",
        "error_root"       : "Esta aplicacion requiere privilegios de administrador.",
        "error_load"       : "No se pudo cargar el archivo de perfiles: {}",
        "error_adapter"    : "No se encontro el adaptador: {}",
        "error_profile"    : "No se encontro el perfil: {}",
        "error_apply"      : "Error al aplicar la configuracion: {}",
        "no_adapters"      : "No se detectaron adaptadores de red.",
        "list_header"      : "Adaptadores de red disponibles:",
        "profile_applied"  : "Perfil '{}' aplicado al adaptador '{}'.",
        "current_ip"       : "IP actual",
        "new_ip"           : "Nueva IP",
        "mask"             : "Mascara",
        "gateway"          : "Puerta de enlace",
        "destino"          : "IP Destino",
        "log_applying"     : "Aplicando perfil '{}' en adaptador '{}'...",
        "log_success"      : "Configuracion aplicada correctamente.",
        "confirm_title"    : "Confirmar cambio",
        "error_ip_in_use"  : "La IP {} ya esta asignada al adaptador '{}'.",
        "confirm_msg"      : "Aplicar IP {} al adaptador {}?",
        "btn_dhcp_one"     : "DHCP adaptador",
        "btn_dhcp_all"     : "DHCP todos",
        "confirm_dhcp_one" : "Pasar {} a DHCP automatico?",
        "confirm_dhcp_all" : "Pasar TODOS los adaptadores a DHCP automatico?",
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
        "btn_dhcp_one"     : "DHCP adapter",
        "btn_dhcp_all"     : "DHCP all",
        "confirm_dhcp_one" : "Set {} to automatic DHCP?",
        "confirm_dhcp_all" : "Set ALL adapters to automatic DHCP?",
    },
}

# ---------------------------------------------------------------------------
# Estado del idioma activo (modifiable mediante set_language)
# ---------------------------------------------------------------------------

_active_lang: str = "en"


def detect_language() -> str:
    """
    Detecta el idioma del sistema operativo.

    Comprueba el locale por defecto del SO. Devuelve ``'es'`` si el codigo
    de idioma comienza por ``es``, y ``'en'`` en cualquier otro caso.

    Returns
    -------
    str
        ``'es'`` o ``'en'``.
    """
    try:
        lang, _ = locale.getdefaultlocale()
        if lang and lang.lower().startswith("es"):
            return "es"
    except Exception:
        pass
    return "en"


def set_language(lang: str) -> None:
    """
    Establece el idioma activo de la interfaz.

    Parameters
    ----------
    lang : str
        Codigo de idioma: ``'es'`` o ``'en'``.
        Si el valor no esta en el diccionario se usa ``'en'`` como fallback.
    """
    global _active_lang
    _active_lang = lang if lang in _STRINGS else "en"


def get_language() -> str:
    """Devuelve el codigo del idioma activo."""
    return _active_lang


def t(key: str, *args: object) -> str:
    """
    Traduce una clave al idioma activo.

    Parameters
    ----------
    key  : str
        Clave del diccionario de traducciones.
    args : object
        Argumentos opcionales pasados a ``str.format()``.

    Returns
    -------
    str
        Cadena traducida. Si la clave no existe devuelve la propia clave
        para facilitar la deteccion de cadenas sin traducir.

    Examples
    --------
    >>> set_language("es")
    >>> t("btn_apply")
    'Aplicar'
    >>> t("error_load", "/ruta/ips.json")
    'No se pudo cargar el archivo de perfiles: /ruta/ips.json'
    """
    text = _STRINGS.get(_active_lang, _STRINGS["en"]).get(key, key)
    if args:
        text = text.format(*args)
    return text


# ---------------------------------------------------------------------------
# Inicializar con el idioma del sistema al importar el modulo
# ---------------------------------------------------------------------------

set_language(detect_language())
