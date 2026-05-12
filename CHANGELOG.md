**Changelog — IPSwitcher**  
Todos los cambios notables de este proyecto se documentan en este archivo.  
   
 Formato basado en [Keep a Changelog.](https://keepachangelog.com/es/1.0.0/ "https://keepachangelog.com/es/1.0.0/")  
**[1.** **1** **.0] — 202** **6** **-0** **5** **-** **13**  
**Corregido**  
   
-  Fuente cambiada de `Consolas` a `DejaVu Sans Mono` para mostrar correctamente caracteres con tilde y símbolos Unicode en Linux.  
- IP-Destino` del JSON ya no se usa como Gateway. Ahora se muestra como campo informativo ("IP Destino") y el Gateway se deja siempre vacío, evitando rutas incorrectas al aplicar la configuración.  
- En Linux, se detecta si la IP seleccionada ya está asignada a otro adaptador antes de intentar aplicarla, mostrando un mensaje claro con el nombre del adaptador en conflicto.  
- Cuando el archivo `ips.json` no existe o está corrupto, la aplicación muestra un diálogo de error visible en lugar de cerrarse silenciosamente.  
