#!/usr/bin/env bash
# =============================================================================
# build_linux.sh — Script de compilación para Linux
# =============================================================================
# Genera dos artefactos:
#   1. dist/linux/IPSwitcher          → ejecutable portable (PyInstaller)
#   2. dist/linux/ipswitcher_1.0.0_amd64.deb  → paquete instalable Debian/Ubuntu
#
# Uso:
#   chmod +x scripts/build_linux.sh
#   ./scripts/build_linux.sh
#
# Requiere: Python 3.10+, pip, dpkg-deb (pre-instalado en Ubuntu)
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Variables de configuración
# ---------------------------------------------------------------------------
APP_NAME="IPSwitcher"
APP_VERSION="1.0.0"
APP_LOWER="ipswitcher"
ARCH="amd64"
MAINTAINER="IPSwitcher Project <ipswitcher@example.com>"
DESCRIPTION="Herramienta para cambiar la IPv4 de adaptadores de red"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_FILE="${REPO_ROOT}/src/ipswitcher.py"
JSON_FILE="${REPO_ROOT}/ips.json"
DIST_DIR="${REPO_ROOT}/dist/linux"
BUILD_DIR="${REPO_ROOT}/build"

# ---------------------------------------------------------------------------
# Colores para la salida
# ---------------------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[1;33m'; RESET='\033[0m'; BOLD='\033[1m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*"; exit 1; }

# ---------------------------------------------------------------------------
# Comprobaciones previas
# ---------------------------------------------------------------------------
info "=== ${APP_NAME} v${APP_VERSION} — Build Linux ==="

[[ -f "${SRC_FILE}" ]] || error "Fuente no encontrada: ${SRC_FILE}"
[[ -f "${JSON_FILE}" ]] || error "JSON no encontrado: ${JSON_FILE}"

# Comprobar Python 3.10+
PYTHON=$(command -v python3 || true)
[[ -n "${PYTHON}" ]] || error "Python 3 no encontrado. Instala con: sudo apt install python3"

PY_VERSION=$(${PYTHON} -c "import sys; print('{}.{}'.format(*sys.version_info[:2]))")
PY_MAJOR=$(echo "${PY_VERSION}" | cut -d. -f1)
PY_MINOR=$(echo "${PY_VERSION}" | cut -d. -f2)
[[ "${PY_MAJOR}" -ge 3 && "${PY_MINOR}" -ge 10 ]] || \
    error "Se requiere Python 3.10+. Versión detectada: ${PY_VERSION}"

info "Python detectado: ${PY_VERSION}"

# ---------------------------------------------------------------------------
# Instalación de dependencias Python
# ---------------------------------------------------------------------------
info "Instalando dependencias Python..."
${PYTHON} -m pip install --upgrade pip --quiet --break-system-packages
${PYTHON} -m pip install pyinstaller --quiet --break-system-packages
success "PyInstaller instalado."

# ---------------------------------------------------------------------------
# Preparar directorios de salida
# ---------------------------------------------------------------------------
rm -rf "${DIST_DIR}" "${BUILD_DIR}"
mkdir -p "${DIST_DIR}"

# ---------------------------------------------------------------------------
# 1. Compilar ejecutable portable con PyInstaller
# ---------------------------------------------------------------------------
info "Compilando ejecutable portable con PyInstaller..."

${PYTHON} -m PyInstaller \
    --onefile \
    --name "${APP_NAME}" \
    --add-data "${JSON_FILE}:." \
    --distpath "${DIST_DIR}" \
    --workpath "${BUILD_DIR}/pyinstaller" \
    --specpath "${BUILD_DIR}" \
    --clean \
    --noconfirm \
    "${SRC_FILE}"

EXE_PATH="${DIST_DIR}/${APP_NAME}"
[[ -f "${EXE_PATH}" ]] || error "PyInstaller no generó el ejecutable esperado."
chmod +x "${EXE_PATH}"
success "Ejecutable portable: ${EXE_PATH}"

# ---------------------------------------------------------------------------
# 2. Crear paquete .deb
# ---------------------------------------------------------------------------
info "Creando paquete .deb..."

DEB_STAGE="${BUILD_DIR}/deb_stage"
DEB_ROOT="${DEB_STAGE}/${APP_LOWER}_${APP_VERSION}_${ARCH}"

# Estructura de directorios del paquete
mkdir -p "${DEB_ROOT}/DEBIAN"
mkdir -p "${DEB_ROOT}/usr/bin"
mkdir -p "${DEB_ROOT}/usr/share/applications"
mkdir -p "${DEB_ROOT}/usr/share/${APP_LOWER}"
mkdir -p "${DEB_ROOT}/usr/share/doc/${APP_LOWER}"

# ── Binario ──────────────────────────────────────────────────────────────────
cp "${EXE_PATH}" "${DEB_ROOT}/usr/bin/${APP_LOWER}"
chmod 755 "${DEB_ROOT}/usr/bin/${APP_LOWER}"

# ── Datos ────────────────────────────────────────────────────────────────────
cp "${JSON_FILE}" "${DEB_ROOT}/usr/share/${APP_LOWER}/ips.json"
chmod 644 "${DEB_ROOT}/usr/share/${APP_LOWER}/ips.json"

# ── Entrada de menú .desktop ──────────────────────────────────────────────────
cat > "${DEB_ROOT}/usr/share/applications/${APP_LOWER}.desktop" << DESKTOP
[Desktop Entry]
Name=${APP_NAME}
Comment=${DESCRIPTION}
Exec=pkexec /usr/bin/${APP_LOWER}
Icon=${APP_LOWER}
Terminal=false
Type=Application
Categories=Network;Settings;
Keywords=IP;Network;Switch;IPv4;
StartupNotify=true
DESKTOP
chmod 644 "${DEB_ROOT}/usr/share/applications/${APP_LOWER}.desktop"

# ── Documentacion ────────────────────────────────────────────────────────────
cat > "${DEB_ROOT}/usr/share/doc/${APP_LOWER}/copyright" << COPYRIGHT
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: ${APP_NAME}
Source: https://github.com/WhiteHornet13/IPSwitcher

Files: *
Copyright: $(date +%Y) IPSwitcher Project
License: MIT
COPYRIGHT

gzip --best -n -c /dev/null > "${DEB_ROOT}/usr/share/doc/${APP_LOWER}/changelog.gz"

# ── Scripts de pre/post instalación ──────────────────────────────────────────
cat > "${DEB_ROOT}/DEBIAN/postinst" << 'POSTINST'
#!/bin/sh
set -e
# Actualizar la base de datos de menús
if command -v update-desktop-database > /dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
POSTINST
chmod 755 "${DEB_ROOT}/DEBIAN/postinst"

cat > "${DEB_ROOT}/DEBIAN/prerm" << 'PRERM'
#!/bin/sh
set -e
PRERM
chmod 755 "${DEB_ROOT}/DEBIAN/prerm"

# ── Control ───────────────────────────────────────────────────────────────────
# Calcular tamaño instalado (en KB)
INSTALLED_SIZE=$(du -sk "${DEB_ROOT}/usr" | cut -f1)

cat > "${DEB_ROOT}/DEBIAN/control" << CONTROL
Package: ${APP_LOWER}
Version: ${APP_VERSION}
Architecture: ${ARCH}
Maintainer: ${MAINTAINER}
Installed-Size: ${INSTALLED_SIZE}
Depends: libgtk-3-0, pkexec
Recommends: policykit-1
Section: net
Priority: optional
Homepage: https://github.com/WhiteHornet13/IPSwitcher
Description: ${DESCRIPTION}
 IPSwitcher permite seleccionar un adaptador de red y aplicar
 configuraciones IP fijas almacenadas en un archivo JSON.
 .
 Soporta deteccion automatica de adaptadores, interfaz grafica
 (Tkinter) y modo consola con argumentos.
CONTROL

# ── Compilar el .deb ──────────────────────────────────────────────────────────
DEB_FILE="${DIST_DIR}/${APP_LOWER}_${APP_VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "${DEB_ROOT}" "${DEB_FILE}"

[[ -f "${DEB_FILE}" ]] || error "dpkg-deb no generó el archivo esperado."
success "Paquete .deb: ${DEB_FILE}"

# ---------------------------------------------------------------------------
# Resumen final
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}=== Artefactos generados ===${RESET}"
echo -e "  ${GREEN}▶${RESET} Portable: ${EXE_PATH}"
echo -e "  ${GREEN}▶${RESET} Paquete:  ${DEB_FILE}"
echo ""
echo -e "${GREEN}Build completado correctamente.${RESET}"
