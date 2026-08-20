Quiero implementar la siguiente feature para AromaBot: $ARGUMENTS

**FASE 1 — Diseño (obligatorio antes de código)**

Presenta 3 enfoques diferentes, cada uno con:
- Descripción en 2 líneas
- Ventaja principal
- Desventaja / riesgo
- Complejidad: baja / media / alta
- Impacto en el deploy actual en Railway

Espera respuesta antes de continuar. No escribir código en esta fase.

**FASE 2 — Implementación (solo tras aprobación)**

Una vez elegido el enfoque:
1. Define la interfaz: endpoints nuevos, schemas Pydantic, firma de herramientas
2. Implementa el mínimo funcional — sin abstracciones no pedidas
3. Verifica que los endpoints existentes siguen funcionando (`/health`, `/chat`, `/inventario`)
4. Actualiza `docs/01_arquitectura_general.md` si se agregaron endpoints
5. Actualiza `docs/05_patrones_y_decisiones.md` con la decisión tomada

Convenciones a respetar:
- No hardcodear precios ni utilidades — están en `DISTRIBUIDORES`
- No cambiar el puerto a fijo — usar `os.getenv("PORT", 8000)`
- No subir `.env` a GitHub
