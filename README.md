# IPSwitcher

**IPSwitcher** es una herramienta para cambiar la dirección IPv4 de adaptadores de red a partir de perfiles almacenados en un archivo JSON. Dispone de interfaz gráfica (Tkinter) y modo consola con argumentos.

[![Build Status](https://github.com/WhiteHornet13/IPSwitcher/actions/workflows/compilar.yml/badge.svg)](https://github.com/WhiteHornet13/IPSwitcher/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Tabla de contenidos

- [Características](#características)
- [Requisitos del sistema](#requisitos-del-sistema)
- [Instalación](#instalación)
  - [Linux — paquete .deb](#linux--paquete-deb)
  - [Linux — ejecutable portable](#linux--ejecutable-portable)
  - [Windows 10/11 — portable](#windows-1011--portable)
  - [Windows XP — instalador](#windows-xp--instalador)
  - [Windows XP — portable](#windows-xp--portable)
- [Uso](#uso)
  - [Interfaz gráfica (GUI)](#interfaz-gráfica-gui)
  - [Línea de comandos (CLI)](#línea-de-comandos-cli)
- [Archivo de perfiles JSON](#archivo-de-perfiles-json)
- [Compilación desde el código fuente](#compilación-desde-el-código-fuente)
  - [Requisitos de compilación](#requisitos-de-compilación)
  - [Compilar en Linux](#compilar-en-linux)
  - [Compilar para Windows (desde Linux)](#compilar-para-windows-desde-linux)
  - [Compilar para Windows XP](#compilar-para-windows-xp)
  - [GitHub Actions (CI/CD)](#github-actions-cicd)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Internacionalización](#internacionalización)
- [Permisos de administrador](#permisos-de-administrador)
- [Solución de problemas](#solución-de-problemas)
- [Licencia](#licencia)

---

## Características

- **Detección automática** de todos los adaptadores de red del sistema.
- **Perfiles de IP** almacenados en un archivo JSON con estructura jerárquica (Línea → Máquina → Equipo).
- **Detección automática del idioma** del sistema operativo (español / inglés).
- **Interfaz gráfica** moderna con Tkinter (oscura, con log de operaciones).
- **Modo consola** con argumentos `--list`, `--adapter`, `--profile`.
- Dos versiones del código fuente:
  - `ipswitcher.py` → Python 3.10+, Windows 7/10/11 y Linux.
  - `ipswitcherXP.py` → Python 2.7, Windows XP/Vista/7.
- Cinco artefactos de distribución (ver tabla de descargas).

---

## Requisitos del sistema

| Plataforma       | Requisitos                                      |
|------------------|-------------------------------------------------|
| Linux            | Ubuntu 20.04+ / Debian 10+, Python 3.10+        |
| Windows 10/11    | Python 3.10+ (si usas el .py), o solo el .exe   |
| Windows 7        | Python 3.10+ o el .exe portable                 |
| Windows XP/Vista | Python 2.7 (si usas el .py), o el .exe XP       |

> La app requiere **privilegios de administrador** (root/sudo en Linux, Administrador en Windows) para modificar la configuración de red.

---

## Instalación

### Linux — paquete .deb

```bash
# Descargar el .deb desde la página de Releases
wget https://github.com/WhiteHornet13/IPSwitcher/releases/latest/download/ipswitcher_1.0.0_amd64.deb

# Instalar
sudo dpkg -i ipswitcher_1.0.0_amd64.deb

# Si faltan dependencias
sudo apt-get install -f

# Lanzar (desde terminal o desde el menú de aplicaciones)
sudo ipswitcher
```

El paquete .deb instala:
- Ejecutable en `/usr/bin/ipswitcher`
- Datos en `/usr/share/ipswitcher/ips.json`
- Acceso directo en el menú de aplicaciones (categoría Red/Configuración)

Para desinstalar:
```bash
sudo dpkg -r ipswitcher
```

### Linux — ejecutable portable

```bash
# Descargar
wget https://github.com/WhiteHornet13/IPSwitcher/releases/latest/download/IPSwitcher_v1.0.0_linux_amd64
chmod +x IPSwitcher_v1.0.0_linux_amd64

# Ejecutar con GUI
sudo ./IPSwitcher_v1.0.0_linux_amd64

# Ejecutar en modo consola
sudo ./IPSwitcher_v1.0.0_linux_amd64 --list
```

> **Nota:** El archivo `ips.json` debe estar en el mismo directorio que el ejecutable cuando se usa el portable.

### Windows 10/11 — portable

1. Descargar `IPSwitcher_v1.0.0_windows.exe` desde la página de [Releases](https://github.com/WhiteHornet13/IPSwitcher/releases).
2. Colocar `ips.json` en la misma carpeta que el `.exe`.
3. Clic derecho → **Ejecutar como administrador**.

### Windows XP — instalador

1. Descargar `IPSwitcherXP_1.0.0_Setup.exe` desde [Releases](https://github.com/WhiteHornet13/IPSwitcher/releases).
2. Doble clic para abrir el asistente de instalación.
3. Seguir los pasos del asistente (se requiere cuenta de Administrador).
4. El instalador creará accesos directos en el Escritorio y en el Menú Inicio.

Para desinstalar: Panel de control → Agregar o quitar programas → IPSwitcherXP.

### Windows XP — portable

1. Descargar `IPSwitcherXP_v1.0.0_WindowsXP_portable.zip`.
2. Extraer en cualquier carpeta.
3. Clic derecho en `IPSwitcherXP.exe` → **Ejecutar como administrador**.

---

## Uso

### Interfaz gráfica (GUI)

Al lanzar la aplicación sin argumentos se abre la GUI:

```
┌──────────────────────────────────────────────────────┐
│ ◈  IPSwitcher  v1.0.0                    ● admin     │
├──────────────────────────────────────────────────────┤
│ Adaptador de red: [eth0            ▼]  [⟳ Actualizar]│
│ Perfil de IP:     [Linea 1/Maquina 1/Equipo 1 ▼]     │
│                                                      │
│ Nueva IP        Máscara          Puerta de enlace    │
│ 192.168.1.10    255.255.255.0    192.168.1.254        │
├──────────────────────────────────────────────────────┤
│ [▶  Aplicar                                       ]  │
├──────────────────────────────────────────────────────┤
│ LOG                                                  │
│ Adaptadores detectados: 3                            │
│ Perfil aplicado correctamente.                       │
└──────────────────────────────────────────────────────┘
```

1. Selecciona el **adaptador de red** en el primer desplegable.
2. Selecciona el **perfil de IP** en el segundo desplegable.
3. Verifica los datos mostrados (IP, Máscara, Gateway).
4. Haz clic en **Aplicar** y confirma el cambio.

### Línea de comandos (CLI)

```bash
# Listar adaptadores disponibles (no requiere privilegios)
ipswitcher --list

# Aplicar un perfil concreto
sudo ipswitcher --adapter eth0 --profile "Linea 1 / Maquina 1 / Equipo 1"

# Forzar idioma inglés
sudo ipswitcher --lang en --adapter eth0 --profile "Linea 2 / Maquina 1 / Equipo 1"

# Abrir GUI explícitamente
sudo ipswitcher --gui

# Modo verbose (debug)
sudo ipswitcher --verbose --adapter eth0 --profile "Linea 1 / Maquina 1 / Equipo 1"

# Ver versión
ipswitcher --version
```

**Referencia de argumentos:**

| Argumento              | Descripción                                          |
|------------------------|------------------------------------------------------|
| `--list`               | Lista los adaptadores de red disponibles y sale.     |
| `--adapter NOMBRE`     | Nombre exacto del adaptador a configurar.            |
| `--profile CLAVE`      | Clave del perfil: `"Linea X / Maquina Y / Equipo Z"` |
| `--gui`                | Abre la interfaz gráfica (comportamiento por defecto)|
| `--lang {es,en}`       | Fuerza el idioma de la interfaz.                     |
| `--verbose`            | Activa mensajes de depuración (DEBUG).               |
| `--version`            | Muestra la versión y sale.                           |

---

## Archivo de perfiles JSON

El archivo `ips.json` define la estructura jerárquica de perfiles:

```json
{
  "IPs": {
    "lineas": [
      {
        "nombre": "Linea 1",
        "maquinas": [
          {
            "nombre": "Maquina 1",
            "equipos": [
              {
                "nombre"    : "Equipo 1",
                "IP-PC"     : "192.168.1.10",
                "Mascara"   : "255.255.255.0",
                "IP-Destino": "192.168.1.254"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

Campos de cada equipo:

| Campo        | Descripción                        | Ejemplo           |
|--------------|------------------------------------|-------------------|
| `nombre`     | Nombre descriptivo del equipo      | `"Equipo 1"`      |
| `IP-PC`      | Dirección IPv4 a asignar           | `"192.168.1.10"`  |
| `Mascara`    | Máscara de subred                  | `"255.255.255.0"` |
| `IP-Destino` | Puerta de enlace predeterminada    | `"192.168.1.254"` |

> El archivo `ips.json` debe estar en el mismo directorio que el ejecutable o script.  
> Si usas el paquete `.deb`, el archivo se instala en `/usr/share/ipswitcher/ips.json`.

---

## Compilación desde el código fuente

### Requisitos de compilación

**En Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-tk dpkg-dev
pip3 install pyinstaller
```

### Compilar en Linux

```bash
git clone https://github.com/WhiteHornet13/IPSwitcher.git
cd IPSwitcher

# Dar permisos a los scripts
chmod +x scripts/*.sh

# Compilar ejecutable portable + paquete .deb
./scripts/build_linux.sh

# Artefactos generados en:
#   dist/linux/IPSwitcher                        ← portable
#   dist/linux/ipswitcher_1.0.0_amd64.deb        ← paquete
```

### Compilar para Windows (desde Linux)

> Este método requiere Wine. Para producción se recomienda usar GitHub Actions.

```bash
sudo apt-get install wine64
./scripts/build_windows.sh

# Artefacto generado en:
#   dist/windows/IPSwitcher.exe
```

### Compilar para Windows XP

La compilación XP usa Python 2.7 y cx_Freeze. Se recomienda hacerlo en un runner de Windows via GitHub Actions. Para hacerlo manualmente en Windows:

```bat
rem Instalar Python 2.7.18 desde https://www.python.org/downloads/release/python-2718/
rem Instalar cx_Freeze
pip install cx_Freeze==5.1.1

rem Compilar el ejecutable portable
python setup_xp.py build

rem Compilar el instalador (requiere NSIS instalado)
rem Descargar NSIS desde https://nsis.sourceforge.io/
makensis installer_xp.nsi

rem Artefactos:
rem   dist\windowsXP\IPSwitcherXP\           ← carpeta portable
rem   dist\windowsXP\IPSwitcherXP_1.0.0_Setup.exe ← instalador
```

Para generar los scripts de configuración XP desde Linux:
```bash
./scripts/build_windows_xp.sh
# Genera setup_xp.py e installer_xp.nsi
```

### GitHub Actions (CI/CD)

El archivo `.github/workflows/compilar.yml` automatiza la compilación de los 5 artefactos:

```bash
# Compilar manualmente desde la UI de GitHub:
# Actions → Compilar IPSwitcher → Run workflow

# Publicar release (lanzar tag):
git tag v1.0.0
git push origin v1.0.0
# → El workflow compila automáticamente y crea el release con todos los artefactos
```

Jobs del workflow:

| Job                  | Runner            | Artefacto generado                        |
|----------------------|-------------------|-------------------------------------------|
| `build-linux`        | `ubuntu-22.04`    | Portable Linux + `.deb`                   |
| `build-windows`      | `windows-latest`  | `IPSwitcher.exe` portable (Win 10/11)     |
| `build-windows-xp`   | `windows-latest`  | `IPSwitcherXP/` portable (XP)             |
| `build-windows-xp-nsi`| `windows-latest` | `IPSwitcherXP_*_Setup.exe` instalador     |
| `release`            | `ubuntu-latest`   | GitHub Release con todos los artefactos   |

---

## Estructura del proyecto

```
IPSwitcher/
├── src/
│   ├── ipswitcher.py          ← App principal (Python 3.10+, Linux/Win 7-11)
│   └── ipswitcherXP.py        ← App Windows XP (Python 2.7)
├── scripts/
│   ├── build_linux.sh         ← Compila portable + .deb en Linux
│   ├── build_windows.sh       ← Compila .exe Win10/11 (requiere Wine)
│   └── build_windows_xp.sh   ← Genera configs para compilación XP
├── .github/
│   └── workflows/
│       └── compilar.yml       ← Pipeline CI/CD GitHub Actions
├── assets/
│   └── ipswitcher.ico         ← Icono (opcional)
├── ips.json                   ← Perfiles de IP
├── setup_xp.py                ← cx_Freeze setup (generado por build_windows_xp.sh)
├── installer_xp.nsi           ← Script NSIS (generado por build_windows_xp.sh)
├── LICENSE                    ← Licencia MIT
├── CHANGELOG.md               ← Historial de cambios
└── README.md                  ← Este archivo
```

---

## Internacionalización

IPSwitcher detecta automáticamente el idioma del sistema operativo:

- **Español** (`es_*`): Todos los textos en español.
- **Inglés** (cualquier otro locale): Textos en inglés.

Para forzar un idioma concreto:
```bash
# Forzar inglés
ipswitcher --lang en

# Forzar español
ipswitcher --lang es
```

---

## Permisos de administrador

Modificar la configuración de red requiere privilegios elevados:

**Linux:**
```bash
sudo ipswitcher                    # con sudo
pkexec ipswitcher                  # con PolicyKit (GUI)
```

**Windows:**
- Clic derecho en el `.exe` → "Ejecutar como administrador".
- O lanzar desde un símbolo del sistema con permisos de administrador.

Si se lanza sin privilegios suficientes, la app muestra una advertencia pero permite explorar los perfiles sin aplicar cambios.

---

## Solución de problemas

**La app no detecta adaptadores en Linux:**
```bash
# Verificar interfaces disponibles
ip link show
ls /sys/class/net/
```

**"No se pudo aplicar la configuración" en Linux:**
```bash
# Verificar que iproute2 está instalado
which ip
sudo apt-get install iproute2
```

**La GUI no abre en Linux (entorno sin escritorio):**
```bash
# Usar modo consola
sudo ipswitcher --list
sudo ipswitcher --adapter eth0 --profile "Linea 1 / Maquina 1 / Equipo 1"
```

**Error "no display" al ejecutar con sudo en Linux:**
```bash
# Opción 1: xhost
xhost +local:
sudo ipswitcher

# Opción 2: preservar variable DISPLAY
sudo DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY ipswitcher
```

**El .exe de Windows pide confirmación de UAC:**
Esto es normal. El ejecutable requiere permisos de administrador para modificar la red.

**En Windows XP el exe no abre:**
- Verifica que tienes los Visual C++ Redistributables de Microsoft instalados.
- Intenta ejecutar desde el símbolo del sistema para ver el error.

---

## Licencia

MIT License — ver [LICENSE](LICENSE) para más detalles.

---

## Repositorio

[https://github.com/WhiteHornet13/IPSwitcher](https://github.com/WhiteHornet13/IPSwitcher)
