#!/usr/bin/env bash
# =============================================================================
# build_windows_xp.sh — Compilación para Windows XP (Python 2.7 + cx_Freeze)
# =============================================================================
# Este script crea:
#   1. dist/windowsXP/IPSwitcherXP.exe      → portable (cx_Freeze)
#   2. dist/windowsXP/IPSwitcherXP_Setup.exe → instalador NSIS
#
# La compilación de Python 2.7 para XP se realiza en el runner Windows
# del workflow de GitHub Actions. Este script se incluye como referencia
# y para entornos locales con Wine + Python 2.7 para Windows.
#
# Para compilar localmente en Windows XP real:
#   1. Instalar Python 2.7.18 (última versión)
#   2. Instalar cx_Freeze: pip install cx_Freeze==5.1.1
#   3. Instalar NSIS (Nullsoft Scriptable Install System)
#   4. Ejecutar: python setup_xp.py build
#   5. Para instalador: makensis installer_xp.nsi
#
# Uso desde Linux (requiere Wine):
#   chmod +x scripts/build_windows_xp.sh
#   ./scripts/build_windows_xp.sh
# =============================================================================

set -euo pipefail

APP_NAME="IPSwitcherXP"
APP_VERSION="1.0.0"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${REPO_ROOT}/dist/windowsXP"
BUILD_DIR="${REPO_ROOT}/build"

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; RESET='\033[0m'
info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*"; exit 1; }

info "=== ${APP_NAME} v${APP_VERSION} — Build Windows XP ==="

mkdir -p "${DIST_DIR}"

# ---------------------------------------------------------------------------
# Generar setup_xp.py (cx_Freeze setup script)
# Este archivo se usa tanto localmente como en el runner de GitHub Actions.
# ---------------------------------------------------------------------------
info "Generando setup_xp.py..."

cat > "${REPO_ROOT}/setup_xp.py" << 'SETUP'
# -*- coding: utf-8 -*-
"""
setup_xp.py — cx_Freeze setup para Windows XP (Python 2.7)
============================================================
Uso:
    python setup_xp.py build            → directorio portable
    python setup_xp.py bdist_msi        → paquete MSI (no XP)
"""

import sys
import os
from cx_Freeze import setup, Executable

# Directorio del script
HERE = os.path.dirname(os.path.abspath(__file__))

# Opciones de compilacion
build_options = {
    "packages": [
        "os", "sys", "json", "locale", "logging",
        "optparse", "platform", "subprocess", "threading",
        "Tkinter", "ttk", "tkMessageBox", "ctypes",
    ],
    "excludes": [
        "email", "html", "http", "urllib", "xml", "unittest",
        "pydoc", "doctest", "difflib", "inspect",
    ],
    "include_files": [
        (os.path.join(HERE, "ips.json"), "ips.json"),
    ],
    "optimize": 2,
    "build_exe": os.path.join(HERE, "dist", "windowsXP", "IPSwitcherXP"),
}

executables = [
    Executable(
        script=os.path.join(HERE, "src", "ipswitcherXP.py"),
        base="Win32GUI",           # Sin ventana de consola
        targetName="IPSwitcherXP.exe",
        shortcutName="IPSwitcherXP",
        shortcutDir="ProgramMenuFolder",
        copyright="IPSwitcher Project 2024",
    ),
]

setup(
    name="IPSwitcherXP",
    version="1.0.0",
    description="Cambia la IP de adaptadores de red (Windows XP)",
    options={"build_exe": build_options},
    executables=executables,
)
SETUP

success "setup_xp.py generado en: ${REPO_ROOT}/setup_xp.py"

# ---------------------------------------------------------------------------
# Generar script NSIS para el instalador
# ---------------------------------------------------------------------------
info "Generando installer_xp.nsi (NSIS)..."

cat > "${REPO_ROOT}/installer_xp.nsi" << 'NSIS'
; =============================================================================
; installer_xp.nsi — NSIS Installer para IPSwitcherXP (Windows XP+)
; =============================================================================
; Compilar con: makensis installer_xp.nsi
; Requiere NSIS 2.46+ instalado en el sistema de compilacion.

Unicode true

; ── Metadatos ─────────────────────────────────────────────────────────────────
!define APP_NAME        "IPSwitcherXP"
!define APP_VERSION     "1.0.0"
!define APP_PUBLISHER   "IPSwitcher Project"
!define APP_URL         "https://github.com/WhiteHornet13/IPSwitcher"
!define APP_EXE         "IPSwitcherXP.exe"
!define INSTALL_DIR     "$PROGRAMFILES\${APP_NAME}"
!define REG_KEY         "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"

; ── Configuración general ──────────────────────────────────────────────────────
Name                    "${APP_NAME} ${APP_VERSION}"
OutFile                 "dist\windowsXP\${APP_NAME}_${APP_VERSION}_Setup.exe"
InstallDir              "${INSTALL_DIR}"
InstallDirRegKey HKLM   "${REG_KEY}" "InstallLocation"
RequestExecutionLevel   admin
SetCompressor           lzma
ShowInstDetails         show
ShowUninstDetails       show

; ── Páginas del asistente ─────────────────────────────────────────────────────
Page license
Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

; ── Textos de la licencia ─────────────────────────────────────────────────────
LicenseData             "LICENSE"

; ── Sección principal de instalación ─────────────────────────────────────────
Section "Archivos principales" SecMain
    SectionIn RO   ; obligatorio

    SetOutPath "${INSTALL_DIR}"

    ; Copiar todos los archivos del directorio portable
    File /r "dist\windowsXP\IPSwitcherXP\*.*"

    ; Acceso directo en el escritorio
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" \
        "${INSTALL_DIR}\${APP_EXE}" "" \
        "${INSTALL_DIR}\${APP_EXE}" 0

    ; Acceso directo en el menú Inicio
    CreateDirectory "$SMPROGRAMS\${APP_PUBLISHER}"
    CreateShortCut "$SMPROGRAMS\${APP_PUBLISHER}\${APP_NAME}.lnk" \
        "${INSTALL_DIR}\${APP_EXE}" "" \
        "${INSTALL_DIR}\${APP_EXE}" 0
    CreateShortCut "$SMPROGRAMS\${APP_PUBLISHER}\Desinstalar ${APP_NAME}.lnk" \
        "${INSTALL_DIR}\uninstall.exe"

    ; Registrar para que aparezca en "Agregar o quitar programas"
    WriteRegStr   HKLM "${REG_KEY}" "DisplayName"          "${APP_NAME}"
    WriteRegStr   HKLM "${REG_KEY}" "DisplayVersion"       "${APP_VERSION}"
    WriteRegStr   HKLM "${REG_KEY}" "Publisher"            "${APP_PUBLISHER}"
    WriteRegStr   HKLM "${REG_KEY}" "URLInfoAbout"         "${APP_URL}"
    WriteRegStr   HKLM "${REG_KEY}" "InstallLocation"      "${INSTALL_DIR}"
    WriteRegStr   HKLM "${REG_KEY}" "UninstallString"      "${INSTALL_DIR}\uninstall.exe"
    WriteRegDWORD HKLM "${REG_KEY}" "NoModify"             1
    WriteRegDWORD HKLM "${REG_KEY}" "NoRepair"             1

    ; Crear desinstalador
    WriteUninstaller "${INSTALL_DIR}\uninstall.exe"
SectionEnd

; ── Sección de desinstalación ─────────────────────────────────────────────────
Section "Uninstall"
    ; Borrar archivos
    RMDir /r "${INSTALL_DIR}"

    ; Borrar accesos directos
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_PUBLISHER}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_PUBLISHER}\Desinstalar ${APP_NAME}.lnk"
    RMDir  "$SMPROGRAMS\${APP_PUBLISHER}"

    ; Borrar registros
    DeleteRegKey HKLM "${REG_KEY}"
SectionEnd
NSIS

success "installer_xp.nsi generado en: ${REPO_ROOT}/installer_xp.nsi"

# ---------------------------------------------------------------------------
# Intentar compilar si hay Wine y Python 2.7 disponibles
# ---------------------------------------------------------------------------
if command -v wine &>/dev/null || command -v wine64 &>/dev/null; then
    WINE=$(command -v wine64 || command -v wine)
    PY27_WIN="${BUILD_DIR}/python27_win/python.exe"

    if [[ -f "${PY27_WIN}" ]]; then
        info "Compilando con cx_Freeze (Wine + Python 2.7)..."
        cd "${REPO_ROOT}"
        WINEPREFIX="${BUILD_DIR}/wineprefix27" ${WINE} \
            "${PY27_WIN}" setup_xp.py build 2>/dev/null && \
            success "Build cx_Freeze completado." || \
            warn "Build cx_Freeze falló. Usar GitHub Actions para compilar."
    else
        warn "Python 2.7 para Windows no encontrado en ${PY27_WIN}."
        warn "La compilación XP se realizará automáticamente en GitHub Actions."
    fi
else
    warn "Wine no disponible. La compilación XP se realizará en GitHub Actions."
fi

echo ""
echo "Archivos de configuración generados:"
echo "  setup_xp.py      → cx_Freeze para Python 2.7"
echo "  installer_xp.nsi → Script NSIS para el instalador"
echo ""
echo "Para compilar manualmente en Windows XP:"
echo "  1. python setup_xp.py build"
echo "  2. makensis installer_xp.nsi"
