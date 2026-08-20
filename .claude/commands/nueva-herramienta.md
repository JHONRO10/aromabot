Voy a agregar una nueva herramienta al agente AromaBot.

Descripción de la herramienta: $ARGUMENTS

Sigue este proceso exacto:

**Paso 1 — Diseño (mostrar antes de codificar)**
- Nombre en snake_case (verbo_objeto): ej. `alertar_stock_bajo`
- Input: qué parámetros recibe
- Output: qué string devuelve al agente
- Cuándo la usa el agente: frase exacta que irá en el SYSTEM_PROMPT
- Qué tabla(s) de Supabase lee o escribe

**Paso 2 — Implementación**
- Función Python con decorador `@tool`
- Docstring claro (el agente lo lee para decidir cuándo usarla)
- try/except con mensaje de error descriptivo
- Todas las queries a Supabase dentro de la función, no en helpers externos

**Paso 3 — Registro**
- Agregar la función a `tools_list` en el backend
- Actualizar el `SYSTEM_PROMPT` con la descripción de cuándo usar esta herramienta

**Paso 4 — Documentación**
- Agregar el patrón a `docs/05_patrones_y_decisiones.md` con: problema que resuelve, decisión tomada, alternativas descartadas

No continuar al siguiente paso sin confirmar el anterior.
