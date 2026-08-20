Vamos a diseñar la arquitectura multiagente para AromaBot.

Objetivo o contexto adicional: $ARGUMENTS

Sigue el protocolo de diseño multiagente del CLAUDE.md sección 13. NO escribir código hasta que el diseño esté aprobado.

**Entregable 1 — Mapa de responsabilidades**
Lista cada agente propuesto:
- Nombre del agente
- Qué mensajes maneja (ejemplos concretos de frases de usuario)
- Qué NO maneja (límites claros)
- Qué herramientas/tools necesita

Verificar que no hay overlap entre agentes.

**Entregable 2 — Protocolo de comunicación**
- Cómo el orquestador enruta mensajes a subagentes
- Mecanismo técnico: LangGraph `send()` API, subgraphs, o llamadas secuenciales
- Cómo se consolida la respuesta final

**Entregable 3 — Estado compartido**
- Qué datos comparte el orquestador con subagentes
- Qué estado es local por agente (no compartido)
- Cómo Supabase sirve de fuente de verdad entre agentes

**Entregable 4 — Diagrama en texto**
Flujo completo de un mensaje típico de WhatsApp hasta la respuesta.

**Entregable 5 — Riesgos y mitigaciones**
Qué puede fallar, cómo detectarlo, cómo recuperarse.

Contexto técnico del proyecto: LangGraph + Groq Llama 3.3 70B + Supabase + FastAPI en Railway + n8n + Evolution API.
