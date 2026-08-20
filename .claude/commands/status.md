Verifica el estado completo del sistema AromaBot y reporta un resumen ejecutivo.

Pasos:

1. **Railway/Backend** — Llama `GET https://web-production-f4795.up.railway.app/health` y muestra el resultado
2. **Inventario Supabase** — Llama `GET https://web-production-f4795.up.railway.app/inventario` y confirma que retorna datos válidos
3. **WhatsApp** — Reporta el estado actual de la SIM nueva y la instancia AromaBot en Evolution API (`https://evolution-api-production-34616.up.railway.app`)
4. **Pendientes del proyecto** — Lista las tareas del estado actual en CLAUDE.md sección 8 que aún están sin checkmark

Para cada componente usa: ✅ funcionando / ⚠️ degradado / ❌ caído / ⏳ pendiente

Termina con: "Próxima acción recomendada: [una sola acción concreta]"
