# Global Refactor de Javascript a Arquitectura Modular (IIFE)

Este plan detalla cómo transformaremos el `index.html` (que actualmente tiene un script monolítico de múltiples líneas con variables globales solapadas) a una arquitectura altamente estructurada, profesional y modular basada en **IIFE** (Immediately Invoked Function Expressions), sin necesidad de usar bundlers como Webpack.

## User Review Required
> [!IMPORTANT]
> **Requerimiento Crítico a revisar**: Todo el HTML actual utiliza manejadores inline en el DOM (ej. `onclick="nav('schedule')"` u `onclick="loadUsuarios()"`). 
> Al encapsular las funciones dentro de IIFEs `(function() { ... })();`, estas dejarían de ser accesibles desde el HTML. 
>
> **Decisión Técnica:** Para **NO romper el HTML** y evitar cambios masivos y propensos a error en las vistas, las funciones que deben interactuar con el DOM directamente serán inyectadas en el objeto `window` explícitamente desde cada módulo. (Ej. `window.loadUsuarios = async function(...) { ... }`). 
> ¿Estás de acuerdo con este enfoque?

## Estructura de Módulos (Propuesta)

La arquitectura dividirá TODA la lógica existente con la siguiente topología estricta:

### 1. Módulo Core / Config `(Module 1)`
- **Propósito**: Alojar variables compartidas, constantes de enrutamiento y estado global limpio.
- **Expone**: `window.CONFIG.BASE_URL`, `window.CONFIG.API_DOC`, etc.

### 2. Módulo Auth `(Module 2)`
- **Propósito**: Lógica de JWT estricta y blindada.
- **Expone**: `window.getToken`, `window.logout`, `window.authFetch`.
- **Limpieza**: La variable interna previene loops de recursión y evita exponer vulnerabilidades al DOM.

### 3. Módulo App Engine & Navigation `(Module 3)`
- **Propósito**: Coordinar el encendido de la aplicación, transiciones visuales y ruteo centralizado.
- **Expone**: `window.initApp`, `window.showLogin`, `window.showApp`, `window.nav`, `window.toggleConfigMenu`.

### 4. Módulo RBAC Security `(Module 4)`
- **Propósito**: Aislar la evaluación de permisos.
- **Expone**: `window.applyRBAC`.

### 5. Módulo Login UI `(Module 5)`
- **Propósito**: Listeners aislados (no se expone a `window` pues inyecta eventos `addEventListener('submit')` en tiempo de carga, manteniendo el scope cerrado).

### 6. Módulo de Gestión de Sistema (Users / Roles) `(Module 6)`
- **Propósito**: UI y lógica completa del CRUD de usuarios.
- **Expone**: `window.loadUsuarios`, `window.openUsuarioModal`, `window.editUsuario`, `window.deleteUsuario`, `window.closeUsuarioModal`.

### 7. Módulos de la Lógica de Negocio (Legacy)
Serán encapsulados individualmente para prevenir la superposición de variables:
- **Módulo 7**: Docentes (Maestra, Conflictos, Upload).
- **Módulo 8**: XML & Horarios (Visor).
- **Módulo 9**: Reportes Planilla.
- **Módulo 10**: Incidencias y Observaciones.

## Estrategia de Ejecución
1. Escribiremos un script en Python robusto que extraiga el bloque JS completo.
2. Dividiremos lógicamente los miles de líneas extraídas asegurando que variables conflictivas como `currentMergeData`, `importPage`, `maestraPage` queden **encerradas e invisibles** unas de otras (solucionando el riesgo de colisiones globales).
3. Re-ensamblaremos e inyectaremos todo dentro del `index.html` sin tocar las estructuras HTML nativas.

## Open Questions
> [!WARNING]
> ¿Tienes planificado separar los templates de HTML (ej: cada modal en un archivo ajeno) a futuro, o deseas que por ahora solo refactoricemos estrictamente la porción `<script>` de `index.html` aislando todo su JS?

## Verification Plan

### Test visual
1. Refrescar la página (`index.html`) tras completar.
2. Comprobar en Developer Tools que el objeto global `window` solo contenga las variables estrictamente necesarias exportadas, sin basura residual como variables contadoras (`i`, `payload`, etc).
3. Asegurar flujo crítico: Entrar al login y cargar tabla de usuarios.
