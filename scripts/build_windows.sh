#!/usr/bin/env bash
# =============================================================================
# build_windows.sh — Compilación cruzada .exe para Windows 10/11 desde Linux
# =============================================================================
# Este script usa un entorno Python de Windows ejecutado con Wine para
# producir un .exe portable con PyInstaller.
#
# Alternativamente, en GitHub Actions se usa un runner windows-latest.
# Este script está diseñado para desarrollo local en Ubuntu.
#
# Uso:
#   chmod +x scripts/build_windows.sh
#   ./scripts/build_windows.sh
#
# Requisitos:
#   - wine64 (sudo apt install wine64)
#   - Python 3.10 para Windows (descargado automáticamente si no existe)
# =============================================================================

set -euo pipefail

APP_NAME="IPSwitcher"
APP_VERSION="1.0.0"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_FILE="${REPO_ROOT}/src/ipswitcher.py"
JSON_FILE="${REPO_ROOT}/ips.json"
DIST_DIR="${REPO_ROOT}/dist/windows"
BUILD_DIR="${REPO_ROOT}/build"
WINE_PY_DIR="${BUILD_DIR}/wine_python"
PYTHON_WIN_URL="https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip"
GET_PIP_URL="https://bootstrap.pypa.io/get-pip.py"

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; RESET='\033[0m'; BOLD='\033[1m'
info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*"; exit 1; }

info "=== ${APP_NAME} v${APP_VERSION} — Build Windows (Wine) ==="

# ---------------------------------------------------------------------------
# Verificar Wine
# ---------------------------------------------------------------------------
if ! command -v wine64 &>/dev/null && ! command -v wine &>/dev/null; then
    error "Wine no encontrado. Instala con: sudo apt install wine64"
fi
WINE=$(command -v wine64 || command -v wine)
info "Wine: ${WINE}"

# ---------------------------------------------------------------------------
# Preparar directorios
# ---------------------------------------------------------------------------
rm -rf "${DIST_DIR}" "${WINE_PY_DIR}"
mkdir -p "${DIST_DIR}" "${WINE_PY_DIR}"

# ---------------------------------------------------------------------------
# Descargar Python embebido para Windows si no existe en cache
# ---------------------------------------------------------------------------
PY_ZIP="${BUILD_DIR}/python-win.zip"
if [[ ! -f "${PY_ZIP}" ]]; then
    info "Descargando Python embebido para Windows..."
    curl -L -o "${PY_ZIP}" "${PYTHON_WIN_URL}" || \
        error "No se pudo descargar Python para Windows."
fi

info "Extrayendo Python para Windows..."
unzip -q -o "${PY_ZIP}" -d "${WINE_PY_DIR}"

# Habilitar pip en la distribución embebida
# (en la versión embebida hay que descomentar 'import site' en python3XX._pth)
PTH_FILE=$(find "${WINE_PY_DIR}" -name "python3*._pth" 2>/dev/null | head -1)
if [[ -n "${PTH_FILE}" ]]; then
    sed -i 's/#import site/import site/' "${PTH_FILE}"
fi

# Descargar e instalar pip
GET_PIP="${BUILD_DIR}/get-pip.py"
if [[ ! -f "${GET_PIP}" ]]; then
    curl -L -o "${GET_PIP}" "${GET_PIP_URL}"
fi

info "Instalando pip en el entorno Wine..."
WINEPREFIX="${BUILD_DIR}/wineprefix" ${WINE} \
    "${WINE_PY_DIR}/python.exe" "${GET_PIP}" --quiet 2>/dev/null || true

# ---------------------------------------------------------------------------
# Instalar PyInstaller en el entorno Wine
# ---------------------------------------------------------------------------
info "Instalando PyInstaller en entorno Wine..."
WINEPREFIX="${BUILD_DIR}/wineprefix" ${WINE} \
    "${WINE_PY_DIR}/python.exe" -m pip install pyinstaller --quiet 2>/dev/null

# ---------------------------------------------------------------------------
# Compilar con PyInstaller
# ---------------------------------------------------------------------------
info "Compilando ${APP_NAME}.exe con PyInstaller..."

WINEPREFIX="${BUILD_DIR}/wineprefix" ${WINE} \
    "${WINE_PY_DIR}/python.exe" -m PyInstaller \
    --onefile \
    --windowed \
    --name "${APP_NAME}" \
    --add-data "${JSON_FILE};." \
    --distpath "${DIST_DIR}" \
    --workpath "${BUILD_DIR}/pyinstaller_win" \
    --specpath "${BUILD_DIR}" \
    --clean \
    --noconfirm \
    "${SRC_FILE}" 2>/dev/null

EXE="${DIST_DIR}/${APP_NAME}.exe"
[[ -f "${EXE}" ]] || error "No se generó ${APP_NAME}.exe"
success "Ejecutable: ${EXE}"

echo ""
echo -e "${BOLD}=== Artefactos generados ===${RESET}"
echo -e "  ${GREEN}▶${RESET} Windows EXE: ${EXE}"
echo ""
echo -e "${GREEN}Build Windows completado.${RESET}"
