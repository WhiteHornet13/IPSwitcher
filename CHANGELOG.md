# Changelog — IPSwitcher

Todos los cambios notables de este proyecto se documentan en este archivo.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

## [1.0.0] — 2024-01-01

### Añadido
- Versión inicial de IPSwitcher.
- Detección automática de adaptadores de red (Linux e Windows).
- Carga de perfiles de IP desde `ips.json`.
- Interfaz gráfica (GUI) con Tkinter, tema oscuro, log de operaciones.
- Modo consola con argumentos `--list`, `--adapter`, `--profile`, `--lang`, `--verbose`.
- Detección automática del idioma del sistema (español / inglés).
- `ipswitcher.py` — Python 3.10+, compatible con Linux y Windows 7/10/11.
- `ipswitcherXP.py` — Python 2.7, compatible con Windows XP/Vista/7.
- Scripts de compilación para Linux (`build_linux.sh`, `build_windows.sh`, `build_windows_xp.sh`).
- Pipeline GitHub Actions con 5 jobs (Linux portable, Linux .deb, Windows exe, XP exe, XP instalador NSIS).
- Publicación automática de releases al hacer push de tags `v*`.
- Paquete `.deb` con entrada en el menú de aplicaciones.
- Instalador NSIS para Windows XP con asistente, accesos directos y desinstalador.
