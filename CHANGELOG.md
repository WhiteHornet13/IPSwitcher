**Changelog — IPSwitcher**  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
       
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
     Todos los cambios notables de este proyecto se documentan en este archivo. Formato basado en [Keep a Changelog. Versionado siguiendo ](https://keepachangelog.com/es/1.0.0/ "https://keepachangelog.com/es/1.0.0/")[SemVer.  
   
    
   
  ll  
   
  ](https://semver.org/ "https://semver.org/")## [1.3.2] — 2026-05-22  
   
### Corregido  
- `get_current_ip()` en Windows: el filtro de línea usaba `startswith(("ipv4",  
  "direcci"))` lo que provocaba que en sistemas con IPv6 activo se capturase  
  la dirección IPv6 (que aparece antes en la salida de `ipconfig`) en lugar  
  de la IPv4, o que en sistemas sin IPv6 se capturase otra línea que empezase  
  por "Dirección" (máscara, puerta de enlace). Sustituido por  
  `"ipv4" in stripped.lower()` que discrimina correctamente la línea IPv4  
  en cualquier locale (en-US, es-ES) independientemente de si hay IPv6.  
- `get_current_ip()` en Windows: `split(":", 1)` partía por el primer `:`  
  de la línea, lo que podía capturar texto de relleno en lugar del valor.  
  Sustituido por `rsplit(":", 1)` que parte siempre por el último `:`,  
  garantizando que se obtiene la dirección independientemente del formato  
  exacto de `ipconfig`.[  
    
   
  ## [1.3.1] — 2026-05-21  
   
  ](https://semver.org/ "https://semver.org/")  
**Corregido**  
- get_current_ip() en Windows: el parser de ipconfig rompía el bucle  
   
   en la línea vacía que el comando inserta inmediatamente después del nombre  
   
   del adaptador, antes de sus propiedades, por lo que la IP nunca se leía.  
   
   Añadida bandera found_property que pospone el corte de bloque hasta  
   
   después de haber procesado al menos una propiedad del adaptador.[  
   
   **## [1.3.0] — 2026-05-20**  
   
    
   
     
 **Cambiado**](https://semver.org/ "https://semver.org/")  
- Refactorización completa a arquitectura modular. El monolito ipswitcher.py  
   
    
   
    se divide en paquete src/ con responsabilidad única por módulo:  
   
    
   
    - constants.py  : metadatos, rutas y flags de subproceso.  
   
    
   
    - i18n.py       : cadenas UI y función t().  
   
    
   
    - profiles.py   : carga y aplanado del JSON de perfiles.  
   
    
   
    - network.py    : detección de adaptadores, apply_profile, set_dhcp.  
   
    
   
    - privileges.py : check_privileges, relaunch_as_admin.  
   
    
   
    - cli.py        : parser de argumentos, cli_list, cli_apply.  
   
    
   
    - gui/styles.py : paleta COLORS y configure_styles().  
   
    
   
    - gui/app.py    : clase IPSwitcherGUI.  
   
    
   
    - **main**.py   : punto de entrada (python -m src).  
- Scripts de compilación movidos a scripts/.  
- Assets movidos a assets/.  
- Versión de Python en CI/CD actualizada a 3.12.  
   
    
   
     
 **Sin cambios funcionales**  
- Comportamiento, interfaz y perfiles JSON idénticos a 1.2.4.[  
   
    
   
   **## [1.2.4] — 2026-05-1**    **8**  
   
    
   
     
   
    
   
   **### Corregido**](https://semver.org/ "https://semver.org/")  
- _update_current_ip() en Windows: sustituido netsh interface ip show address  
   
    
   
     
   
    
   
     (frágil, varía con el idioma del SO) por ipconfig, cuya salida es más  
   
    
   
     
   
    
   
     consistente y parseable por nombre de adaptador.  
- _refresh_adapters() en Windows: se lanzaba un proceso PowerShell por cada  
   
    
   
     
   
    
   
     adaptador al consultar el hardware, causando parpadeo de consola en cada  
   
    
   
     
   
    
   
     pulsación de "Actualizar". Añadida get_all_adapter_hardware() que realiza  
   
    
   
     
   
    
   
     una única consulta WMI con ConvertTo-Json y distribuye los resultados como  
   
    
   
     
   
    
   
     caché; get_adapter_hardware() acepta ese caché como parámetro opcional.[  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
    **## [1.2.3] — 2026-05-17**  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
    **### Corregido**](https://semver.org/ "https://semver.org/")  
- _update_current_ip(): en Windows la IP no se mostraba porque netsh varía  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
      el prefijo de línea según el idioma del SO ("IP Address:" en en-US,  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
      "Dirección IP:" en es-ES). Ahora se detectan ambos prefijos.  
- Ventana de consola parpadeante en Windows al pulsar "Actualizar": todos los  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
      subprocess.run() carecían del flag CREATE_NO_WINDOW. Añadida constante  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
      _POPEN_FLAGS que aplica dicho flag en Windows y queda vacía en Linux;  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
      propagada a los siete puntos de llamada de la aplicación.  
   
    
   
     
   
    
   
    [  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
     **## [1.2.2] — 2026-05-17**  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
       
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
     **### Corregido**](https://semver.org/ "https://semver.org/")  
- _update_current_ip(): en Windows usaba ip -o addr (comando exclusivo de  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
       
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
       Linux). Añadida rama Windows que consulta la IP mediante  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
       
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
       netsh interface ip show address.  
- get_adapter_hardware(): retornaba siempre cadena vacía en Windows. Añadida  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
       
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
       rama Windows que consulta el nombre del hardware mediante PowerShell/WMI  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
       
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
       (Win32_NetworkAdapter).  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
     **[1.2.1] — 2026-05-17**  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
     **Corregido**  
- _relaunch_as_admin() en Linux: cuando el ejecutable está compilado con PyInstaller (sys.frozen = True), sys.executable ya ES el binario autónomo. Se pasaba también sys.argv[0] (la ruta al binario) como argumento adicional, lo que hacía que argparse lo recibiese como argumento no reconocido y abortase con error. Ahora se distingue correctamente entre modo frozen y modo script:  
- **Frozen**: target = [ruta_ejecutable]  
- **Script**: target = [python, ruta_script]  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
     **[1.2.0] — 2026-05-13**  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
     **Añadido**  
- Botones **DHCP adaptador** y        **DHCP todos** en la GUI: permiten pasar uno o todos los adaptadores a configuración automática por DHCP sin necesidad de abrir un terminal.  
- Función set_dhcp(): configura DHCP en Linux mediante dhclient o dhcpcd (con fallback y mensaje claro si ninguno está disponible), y en Windows mediante netsh interface ip set address source=dhcp.  
- Función get_adapter_hardware(): consulta el modelo del hardware de cada adaptador vía udevadm (Linux) y lo muestra junto al nombre en el desplegable de adaptadores.  
- Label **IP Actual** en la cabecera: muestra la IP actualmente asignada al adaptador seleccionado y se refresca automáticamente tras aplicar un perfil o DHCP.  
- Argumento CLI --version registrado en el parser.  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
     **Cambiado**  
- El campo IP-Destino del JSON ya no se aplica como gateway; se muestra como campo informativo ("IP Destino") en el panel de detalle. El gateway se deja siempre vacío al aplicar, evitando rutas incorrectas.  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
     **[1.1.2] — 2026-05-14**  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
     **Corregido**  
- Caracteres con tilde ilegibles en el desplegable (Listbox interno del Combobox): la fuente se especifica ahora como tupla ("DejaVu Sans", 10) en lugar de string, lo que resuelve el fallo de codificación UTF-8 en Ubuntu 24.04.  
- El nombre del adaptador en conflicto se limpia correctamente eliminando el sufijo : que devuelve ip -o addr show.  
- Al detectar conflicto de IP en otro adaptador, la comprobación se realiza antes de cualquier flush, dejando el adaptador destino intacto.  
- Si la IP seleccionada ya estaba asignada al mismo adaptador destino, la función retorna sin hacer nada en lugar de hacer flush y reasignar.  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
     **[1.1.0] — 2026-05-13**  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
     **Corregido**  
- Fuente cambiada de Consolas a DejaVu Sans Mono para mostrar correctamente caracteres con tilde y símbolos Unicode en Linux.  
- IP-Destino del JSON ya no se usa como Gateway (ver 1.2.0 para detalle).  
- Detección de IP en conflicto antes de aplicar configuración en Linux.  
- Diálogo de error visible si ips.json no existe o está corrupto, en lugar de cierre silencioso.  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
     **[1.0.0] — 2026-05-01**  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
     **Añadido**  
- Versión inicial pública.  
- Detección automática de adaptadores de red (Linux y Windows).  
- Carga de perfiles desde ips.json con estructura jerárquica Línea → Máquina → Equipo.  
- GUI Tkinter tema oscuro (fondo #1a1d2e, accent cian #00d4ff, violeta #7c3aed).  
- Modo CLI: --list, --adapter, --profile, --gui, --lang, --verbose, --version.  
- Internacionalización automática español / inglés según locale del SO.  
- Aplicación de IP en Linux con iproute2 y en Windows con netsh.  
- Verificación de privilegios root/admin con indicador visual en cabecera.  
- Reintento de elevación de privilegios con pkexec / sudo (Linux) y UAC (Windows).  
- Pipeline CI/CD con GitHub Actions: portable Linux, .deb, portable Windows 10/11 y GitHub Release automático al hacer push de tag v*.  
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
       
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
        
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
       
   
    
   
     
   
    
   
      
   
    
   
     
   
    
   
         
