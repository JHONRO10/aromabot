# AromaBot — Patrones técnicos y decisiones de diseño

Este documento explica POR QUÉ se tomaron ciertas decisiones técnicas.
Es la memoria del proyecto para futuros desarrollos.

---

## Patrón: Seed de base de datos (init-inventario)

**Problema:** La tabla `aroma_inventario` en Supabase estaba vacía.
AromaBot buscaba stock y encontraba 0 en todo, rechazando cada venta.

**Solución:** Endpoint `GET /init-inventario` que hace upsert de todos
los valores iniciales del negocio en una sola llamada.

**Por qué upsert y no insert:**
- `insert` falla si la clave ya existe
- `upsert` crea si no existe, actualiza si ya existe
- Se puede llamar múltiples veces sin romper nada

**Cuándo usar este patrón:**
- Al hacer deploy inicial en un servidor nuevo
- Cuando la base de datos se corrompe o se resetea
- Al migrar a un nuevo proyecto de Supabase

---

## Patrón: Agente AI con herramientas (Tool-Use)

**Concepto:** En lugar de programar cada caso posible, el agente AI
decide qué herramienta usar según el mensaje del usuario.

```
Usuario: "vendí 5 invicto a jairo"
    ↓
Agente analiza el mensaje
    ↓
Decide: usar registrar_venta(distribuidor_id="jairo", productos_json='{"invicto": 5}')
    ↓
La herramienta ejecuta la lógica de negocio
    ↓
Supabase se actualiza
    ↓
Agente responde con el resultado
```

**Por qué LangGraph y no solo ChatGPT:**
LangGraph maneja el ciclo agente→herramienta→agente en bucle,
permitiendo múltiples pasos y corrección de errores automática.

---

## Patrón: Arquitectura de puente (n8n como middleware)

**Por qué n8n en el medio y no conectar WhatsApp directo:**
- WhatsApp → AromaBot directo requiere manejar webhooks complejos en Python
- n8n abstrae esa complejidad
- Permite agregar lógica (filtros, condiciones) sin tocar el código Python
- Permite agregar más automatizaciones (alertas, reportes) sin cambiar el backend

---

## Patrón: Variables de entorno para credenciales

**Regla de oro:** Ninguna clave secreta va en el código.

```python
# MAL — nunca así
supabase = create_client("https://abc.supabase.co", "eyJhb...")

# BIEN — siempre así
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)
```

**Por qué:** GitHub escanea los repos en busca de claves.
Si encuentra una, bloquea el push (esto le pasó al proyecto en el día 1).

---

## Decisión: Groq en lugar de OpenAI

**Por qué Groq:**
- Completamente gratuito en el tier actual
- Llama 3.3 70B es comparable a GPT-4o en tareas de negocio
- Sin tarjeta de crédito requerida para empezar

**Cuándo migrar a OpenAI:**
- Si el volumen de mensajes supera el límite gratuito de Groq
- Si se necesitan capacidades multimodales (imágenes)
- Si se requiere mayor consistencia en respuestas complejas

---

## Decisión: FastAPI para servir también el frontend

**Por qué no separar frontend y backend:**
- Para el MVP es más simple — un solo deploy en Railway
- La UI web es básica (HTML/JS puro, sin framework)
- Reduce costos (un solo servicio en Railway)

**Cuándo separar:**
- Si la UI crece y necesita React/Next.js
- Si se requieren múltiples frontends (web + mobile app)

---

## Lecciones aprendidas

| Problema | Causa | Solución |
|---|---|---|
| Push bloqueado en GitHub | .env con claves en el historial git | Borrar .git, nuevo init, .gitignore correcto |
| "perfumes no existen" | Supabase vacío, sin stock inicial | Endpoint /init-inventario |
| Railway no acepta puerto fijo | Usa variable $PORT dinámica | `os.getenv("PORT", 8000)` |
| Rama "master" vs "main" | Git moderno usa main, el repo era viejo | `git push origin master` |
