**Changelog — IPSwitcher**  
Todos los cambios notables de este proyecto se documentan en este archivo.  
   
 Formato basado en [Keep a Changelog.](https://keepachangelog.com/es/1.0.0/ "https://keepachangelog.com/es/1.0.0/")  
**[1.** **1** **.0] — 202** **6** **-0** **5** **-** **13**  
**Corregido**  
   
-  Fuente cambiada de `Consolas` a `DejaVu Sans Mono` para mostrar correctamente caracteres con tilde y símbolos Unicode en Linux.  
- IP-Destino` del JSON ya no se usa como Gateway. Ahora se muestra como campo informativo ("IP Destino") y el Gateway se deja siempre vacío, evitando rutas incorrectas al aplicar la configuración.  
- En Linux, se detecta si la IP seleccionada ya está asignada a otro adaptador antes de intentar aplicarla, mostrando un mensaje claro con el nombre del adaptador en conflicto.  
- Cuando el archivo `ips.json` no existe o está corrupto, la aplicación muestra un diálogo de error visible en lugar de cerrarse silenciosamente.  

## [1.1.2] — 2026-05-14

### Corregido

- Caracteres con tilde ilegibles en el desplegable (Listbox interno del Combobox):
  la fuente del Listbox se especifica ahora como tupla `("DejaVu Sans", 10)` en lugar
  de string con prioridad, lo que resuelve el fallo de codificación UTF-8 en Ubuntu 24.04.
- El nombre del adaptador que ya tiene la IP en conflicto se limpia correctamente
  eliminando el sufijo `:` que devuelve `ip -o addr show`, de modo que el mensaje
  de error muestra el nombre real de la interfaz.
- Al detectar que la IP ya está en uso en otro adaptador, el adaptador destino ya no
  pierde su configuración IP: la comprobación de conflicto se realiza antes de cualquier
  modificación y se interrumpe sin ejecutar el `flush`.
- Si la IP seleccionada ya estaba asignada al mismo adaptador destino, la función
  retorna sin hacer nada en lugar de hacer flush y reasignar innecesariamente.
