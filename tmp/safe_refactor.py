import re
import json
import shutil

file_path = r'd:\Desktop\MOD HOR\prototype\index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update HTML inline callers to pass 'this' if appropriate
content = content.replace('onchange="handleObsTypeChange()"', 'onchange="handleObsTypeChange(this)"')

# 2. Re-write handleObsTypeChange function
old_func = """                function handleObsTypeChange() {
                    const type = document.getElementById('obs-form-type').value;
                    const replContainer = document.getElementById('obs-replacement-fields');
                    if (!replContainer) return;

                    if (type === 'REEMPLAZO') {
                        replContainer.classList.remove('hidden');
                    } else {
                        replContainer.classList.add('hidden');
                    }
                }"""

new_func = """                function handleObsTypeChange(selectElem) {
                    let type = '';
                    if (selectElem && selectElem.value) { type = selectElem.value; }
                    else {
                        const el = document.getElementById('obs-form-type');
                        if (el) type = el.value;
                    }
                    const replContainer = document.getElementById('obs-replacement-fields');
                    if (!replContainer) return;
                    if (type === 'REEMPLAZO') { replContainer.classList.remove('hidden'); }
                    else { replContainer.classList.add('hidden'); }
                }"""
content = content.replace(old_func, new_func)

# 3. Read pre-computed handlers to export
exported_funcs = ["applyRBAC", "authFetch", "calculateDuration", "calculateDurationMinutes",
                  "changeHistoryPage", "changeImportPage", "changeMaestraPage", "changeRptPage",
                  "changeSinAsignarPage", "closeConfigModal", "closeMergeModal", "closeObsConfirmModal",
                  "closeObsRegisterModal", "closeOverwriteModal", "closeResetPwdModal", "closeSinAsignarModal",
                  "closeStatusModal", "closeTeacherModal", "closeUsuarioModal", "confirmOverwrite",
                  "confirmResetPassword", "confirmStatusChange", "deleteConfig", "deleteObservation",
                  "deleteUsuario", "editConfig", "editUsuario", "executeMerge", "exportSchedule",
                  "exportToExcel", "getToken", "handleObsTypeChange", "handleSedeChange", "handleStatusClick",
                  "hasPermission", "initApp", "loadConfig", "loadMaestra", "loadObsLogs", "loadObsTeacherList",
                  "loadRptCatalogs", "loadRptPlanilla", "loadSchedule", "loadSinAsignar", "loadUploadHistory",
                  "loadUsuarios", "logout", "nav", "openConfigModal", "openMergeModal", "openRegisterObsModal",
                  "openResetPwdModal", "openSinAsignarModal", "openTeacherModal", "openUsuarioModal",
                  "parseJwt", "promoteSinAsignar", "renderScheduleGrid", "resetUpload", "runReprocesarHistorico",
                  "saveConfig", "saveObservation", "saveRolePermissions", "saveSinAsignar", "saveTeacher",
                  "searchClassesForObs", "selectPrincipal", "setToken", "showApp", "showLogin", "simulateUpload",
                  "toggleConfigMenu", "toggleDocentesTab", "toggleObsBlockMode", "toggleObsTab",
                  "toggleSlotReplacement", "toggleUsuariosTab", "updateFileName", "uploadDocentesExcel",
                  "vincularAlias"]

app_handlers_code = "window.APP_HANDLERS = {\n"
for func in sorted(set(exported_funcs)):
    app_handlers_code += f"    {func},\n"
app_handlers_code += "};\nObject.assign(window, window.APP_HANDLERS);\n"

# Only replace the last occurrence of })(window); before // INITIALIZATION BOOTSTRAP
target_str = "            })(window);\n\n            // ==========================================\n            // INITIALIZATION BOOTSTRAP"

replacement_str = f"                {app_handlers_code}\n" + target_str

if target_str in content:
    content = content.replace(target_str, replacement_str)

validation_script = """
            // ==========================================
            // SMART RUNTIME VALIDATOR
            // ==========================================
            document.addEventListener('DOMContentLoaded', () => {
                console.log("🔍 [Auditoría] Detectando handlers inline en el HTML...");
                const allElements = document.querySelectorAll('*');
                const usedHandlers = new Set();
                allElements.forEach(el => {
                    Array.from(el.attributes).forEach(attr => {
                        if (attr.name.startsWith('on')) {
                            const match = attr.value.match(/^\s*([a-zA-Z0-9_]+)\s*\(/);
                            if (match) usedHandlers.add(match[1]);
                        }
                    });
                });
                let missingCount = 0; let okCount = 0;
                console.group("🛡️ Resultados de Validación de Scope UI");
                usedHandlers.forEach(fn => {
                    if (typeof window[fn] !== "function") {
                        console.error(`❌ Handler faltante en runtime: ${fn}`);
                        missingCount++;
                    } else if (!window.APP_HANDLERS || !window.APP_HANDLERS[fn]) {
                        console.warn(`⚠️ Handler existente pero NO registrado: ${fn}`);
                        okCount++;
                    } else { okCount++; }
                });
                if (missingCount === 0) console.log(`✅ Todos los ${okCount} handlers inline están correctamente definidos.`);
                else console.error(`🚨 PELIGRO: Se detectaron ${missingCount} handlers rotos.`);
                console.groupEnd();
            });
"""

# Append validation script to the very end before </script>
content = content.replace("        </script>\n</body>\n</html>", f"{validation_script}\n        </script>\n</body>\n</html>")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Safe update applied successfully.")
