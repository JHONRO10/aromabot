# AromaBot — Arquitectura General

## ¿Qué es AromaBot?

AromaBot es un agente de inteligencia artificial que gestiona el negocio de Successful Aromas.
Funciona como un empleado digital que nunca duerme, no se equivoca con los números
y responde por WhatsApp desde el celular del dueño.

---

## Diagrama del sistema

```
TU CELULAR (WhatsApp)
        │
        ▼
Evolution API (Railway)     ← Gateway de WhatsApp
        │
        ▼
n8n Cloud (flujo de trabajo) ← Cerebro de automatización
        │
        ▼
AromaBot API (Railway)      ← El agente AI
  ├── LangGraph              ← Motor del agente
  ├── Groq (Llama 3.3)      ← Inteligencia artificial (gratis)
  └── Supabase               ← Base de datos en la nube
```

---

## Componentes y su función

### 1. AromaBot API (Railway)
- **Qué es:** Un servidor Python corriendo en la nube
- **URL producción:** https://web-production-f4795.up.railway.app
- **Endpoints clave:**
  - `GET /` → App web para registrar ventas desde el celular
  - `POST /chat` → Recibe un mensaje, responde con IA
  - `GET /inventario` → Devuelve el stock actual en JSON
  - `GET /health` → Verifica que el servidor está vivo
  - `GET /init-inventario` → Carga el inventario inicial (usar solo una vez)

### 2. LangGraph (agente AI)
- **Qué es:** El cerebro del bot. Decide qué herramienta usar según lo que le dices
- **Modelo:** Llama 3.3 70B via Groq (gratuito)
- **Herramientas disponibles:**
  - `consultar_inventario` → Ver stock
  - `registrar_venta` → Descontar inventario + calcular ganancia
  - `registrar_fabricacion` → Fabricar perfumes
  - `registrar_compra_insumos` → Agregar insumos
  - `reporte_utilidades` → Ver ganancias del mes
  - `mensaje_motivacional` → Motivar distribuidores

### 3. Supabase (base de datos)
- **Qué es:** La libreta digital donde se guarda todo
- **Tablas:**
  - `aroma_inventario` → Stock de cada producto (clave/valor)
  - `aroma_config` → Configuración y utilidades del mes
  - `aroma_pedidos` → Historial de todas las ventas

### 4. n8n (automatización)
- **Qué es:** El puente entre WhatsApp y AromaBot
- **Flujo activo:** AromaBot - WhatsApp MVP
- **Ruta webhook:** `/aromabot_whatsapp`

### 5. Evolution API (WhatsApp)
- **Qué es:** El conector que permite enviar y recibir mensajes de WhatsApp
- **URL:** https://evolution-api-production-34616.up.railway.app
- **Instancia ARIA:** ADH Coaching (número coaching)
- **Instancia AromaBot:** Successful Aromas (SIM nueva pendiente)

---

## Stack tecnológico

| Tecnología | Versión | Para qué |
|---|---|---|
| Python | 3.11+ | Lenguaje del backend |
| FastAPI | 0.115 | Servidor web y API REST |
| LangGraph | 0.3.5 | Motor del agente AI |
| LangChain Groq | 0.3.2 | Conexión al LLM gratuito |
| Supabase | 2.15 | Base de datos en la nube |
| Uvicorn | 0.34 | Servidor ASGI para producción |
| Railway | — | Hosting del backend |
| n8n Cloud | — | Automatización de flujos |

---

## Archivos del proyecto

```
aromabot/
├── aromabot_backend.py   ← TODO el backend (agente + API + UI)
├── requirements.txt      ← Dependencias Python
├── Procfile             ← Comando de arranque para Railway
├── .gitignore           ← Archivos excluidos de GitHub
├── CLAUDE.md            ← Instrucciones para Claude Code
└── docs/                ← Esta carpeta de documentación
    ├── 01_arquitectura_general.md
    ├── 02_base_de_datos.md
    ├── 03_flujos_n8n.md
    ├── 04_despliegue_railway.md
    └── 05_patrones_y_decisiones.md
```
