; =============================================================================
; installer_xp.nsi — NSIS Installer Script para IPSwitcherXP
; =============================================================================
;
; Genera: dist\windowsXP\IPSwitcherXP_1.0.0_Setup.exe
;
; Compilar con NSIS 2.46+:
;   makensis installer_xp.nsi
;
; Características del instalador:
;   - Asistente de instalación paso a paso
;   - Selección de directorio de instalación
;   - Acceso directo en Escritorio y Menú Inicio
;   - Registro en "Agregar o quitar programas"
;   - Desinstalador incluido
;   - Compatible con Windows XP / Vista / 7 / 10 / 11
; =============================================================================

Unicode true
SetCompressor /SOLID lzma

; ── Versiones y rutas ─────────────────────────────────────────────────────────
!define APP_NAME        "IPSwitcherXP"
!define APP_VERSION     "1.0.0"
!define APP_PUBLISHER   "IPSwitcher Project"
!define APP_URL         "https://github.com/WhiteHornet13/IPSwitcher"
!define APP_EXE         "IPSwitcherXP.exe"
!define APP_GUID        "{D4E2F9A0-1B3C-4E5F-8A7B-6C9D0E1F2A3B}"
!define INSTALL_DIR     "$PROGRAMFILES\${APP_PUBLISHER}\${APP_NAME}"
!define REG_UNINSTALL   "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"

; ── Configuración general del instalador ──────────────────────────────────────
Name                    "${APP_NAME} ${APP_VERSION}"
OutFile                 "dist\windowsXP\${APP_NAME}_${APP_VERSION}_Setup.exe"
InstallDir              "${INSTALL_DIR}"
InstallDirRegKey HKLM   "${REG_UNINSTALL}" "InstallLocation"
RequestExecutionLevel   admin
ShowInstDetails         show
ShowUninstDetails       show
BrandingText            "${APP_NAME} ${APP_VERSION} — ${APP_PUBLISHER}"

; ── Páginas del asistente (instalación) ───────────────────────────────────────
PageEx license
    LicenseData         "LICENSE"
    LicenseForceSelection checkbox
PageExEnd

PageEx directory
    DirVar              $INSTDIR
PageExEnd

PageEx instfiles
PageExEnd

; ── Páginas del asistente (desinstalación) ────────────────────────────────────
UninstPage uninstConfirm
UninstPage instfiles

; ── Macro: Verificar si ya está instalado ────────────────────────────────────
!macro CheckAlreadyInstalled
    ReadRegStr $R0 HKLM "${REG_UNINSTALL}" "UninstallString"
    StrCmp $R0 "" done_check
    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
        "${APP_NAME} ya está instalado.$\n$\nHaz clic en OK para desinstalar \
la versión anterior antes de continuar, o CANCELAR para salir." \
        IDOK do_uninstall IDCANCEL done_check
    do_uninstall:
        ExecWait '$R0 /S _?=$INSTDIR'
    done_check:
!macroend

; ── Sección principal de instalación ─────────────────────────────────────────
Section "Archivos principales" SecMain
    SectionIn RO    ; Sección obligatoria (no se puede desmarcar)

    !insertmacro CheckAlreadyInstalled

    SetOutPath "$INSTDIR"

    ; ── Copiar archivos desde la carpeta portable compilada con cx_Freeze ──
    ; cx_Freeze genera la carpeta dist\windowsXP\IPSwitcherXP\
    ; NSIS la empaqueta dentro del instalador.
    File /r "dist\windowsXP\IPSwitcherXP\*.*"

    ; ── Acceso directo en el Escritorio ───────────────────────────────────────
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" \
        "$INSTDIR\${APP_EXE}" \
        "" \
        "$INSTDIR\${APP_EXE}" \
        0 \
        SW_SHOWNORMAL \
        "" \
        "Cambiar la IP de adaptadores de red"

    ; ── Accesos directos en el Menú Inicio ───────────────────────────────────
    CreateDirectory "$SMPROGRAMS\${APP_PUBLISHER}"
    CreateShortCut "$SMPROGRAMS\${APP_PUBLISHER}\${APP_NAME}.lnk" \
        "$INSTDIR\${APP_EXE}" \
        "" \
        "$INSTDIR\${APP_EXE}"
    CreateShortCut "$SMPROGRAMS\${APP_PUBLISHER}\Desinstalar ${APP_NAME}.lnk" \
        "$INSTDIR\uninstall.exe"

    ; ── Registrar en Agregar/Quitar programas ─────────────────────────────────
    WriteRegStr   HKLM "${REG_UNINSTALL}" "DisplayName"          "${APP_NAME}"
    WriteRegStr   HKLM "${REG_UNINSTALL}" "DisplayVersion"       "${APP_VERSION}"
    WriteRegStr   HKLM "${REG_UNINSTALL}" "Publisher"            "${APP_PUBLISHER}"
    WriteRegStr   HKLM "${REG_UNINSTALL}" "URLInfoAbout"         "${APP_URL}"
    WriteRegStr   HKLM "${REG_UNINSTALL}" "URLUpdateInfo"        "${APP_URL}/releases"
    WriteRegStr   HKLM "${REG_UNINSTALL}" "InstallLocation"      "$INSTDIR"
    WriteRegStr   HKLM "${REG_UNINSTALL}" "UninstallString"      "$INSTDIR\uninstall.exe"
    WriteRegStr   HKLM "${REG_UNINSTALL}" "QuietUninstallString" "$INSTDIR\uninstall.exe /S"
    WriteRegDWORD HKLM "${REG_UNINSTALL}" "NoModify"             1
    WriteRegDWORD HKLM "${REG_UNINSTALL}" "NoRepair"             1
    WriteRegStr   HKLM "${REG_UNINSTALL}" "DisplayIcon"          "$INSTDIR\${APP_EXE}"

    ; ── Crear desinstalador ───────────────────────────────────────────────────
    WriteUninstaller "$INSTDIR\uninstall.exe"

SectionEnd

; ── Sección de desinstalación ─────────────────────────────────────────────────
Section "Uninstall"

    ; Confirmar antes de borrar
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "¿Deseas desinstalar ${APP_NAME} ${APP_VERSION}?" \
        IDYES do_uninstall IDNO abort_uninstall

    do_uninstall:
        ; Borrar todos los archivos y carpetas instaladas
        RMDir /r "$INSTDIR"

        ; Borrar accesos directos
        Delete "$DESKTOP\${APP_NAME}.lnk"
        Delete "$SMPROGRAMS\${APP_PUBLISHER}\${APP_NAME}.lnk"
        Delete "$SMPROGRAMS\${APP_PUBLISHER}\Desinstalar ${APP_NAME}.lnk"
        RMDir  "$SMPROGRAMS\${APP_PUBLISHER}"

        ; Borrar registros
        DeleteRegKey HKLM "${REG_UNINSTALL}"

        MessageBox MB_OK|MB_ICONINFORMATION "${APP_NAME} ha sido desinstalado correctamente."
        Goto done_uninstall

    abort_uninstall:
        Abort "Desinstalación cancelada."

    done_uninstall:

SectionEnd

; ── Funciones de callback ─────────────────────────────────────────────────────

; Se ejecuta al inicio del instalador
Function .onInit
    ; Verificar que se está ejecutando como Administrador
    UserInfo::GetAccountType
    Pop $0
    StrCmp $0 "Admin" is_admin
        MessageBox MB_ICONSTOP \
            "Se necesitan privilegios de Administrador para instalar ${APP_NAME}.$\n$\nEjecuta el instalador como Administrador."
        Abort
    is_admin:
FunctionEnd

; Se ejecuta al finalizar la instalación correctamente
Function .onInstSuccess
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "${APP_NAME} instalado correctamente.$\n$\n¿Deseas ejecutarlo ahora?" \
        IDYES launch_app IDNO done_launch
    launch_app:
        Exec "$INSTDIR\${APP_EXE}"
    done_launch:
FunctionEnd
