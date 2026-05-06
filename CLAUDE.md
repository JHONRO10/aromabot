# CLAUDE.md — AromaBot · Successful Aromas

Este archivo da contexto completo a Claude Code al trabajar en este proyecto.

---

## 1. Identidad del proyecto

**Nombre:** AromaBot  
**Negocio:** Successful Aromas — perfumería colombiana  
**Propietario:** Jhon Rojas  
**Propósito:** Agente AI que gestiona inventario, ventas, fabricación y utilidades por WhatsApp. Controlado desde el celular sin demandar tiempo manual.

**Prioridades del negocio (en orden):**
1. Control de inventario automático — que fluya solo
2. Utilidades reales por distribuidor — saber exactamente cuánto se gana
3. Control desde WhatsApp — mínimo esfuerzo del dueño

---

## 2. Stack técnico

| Capa | Tecnología | Propósito |
|---|---|---|
| Agente AI | LangGraph + Groq (Llama 3.3 70B) | Cerebro del bot, gratuito |
| API | FastAPI + Uvicorn | Expone /chat, /inventario, /health |
| Base de datos | Supabase (PostgreSQL) | Inventario, pedidos, configuración |
| Deploy | Railway | Backend en la nube accesible por n8n |
| Automatización | n8n Cloud | Flujos WhatsApp, alertas, reportes |
| WhatsApp | Evolution API (Railway) | Gateway de mensajes |

**Archivo principal:** `aromabot_backend.py`  
**Puerto:** variable de entorno `PORT` (Railway lo asigna automáticamente)

### Variables de entorno requeridas

```bash
GROQ_API_KEY=      # modelo gratuito de Groq
SUPABASE_URL=      # URL del proyecto Supabase
SUPABASE_KEY=      # anon key de Supabase
PORT=              # Railway lo asigna solo, no hardcodear
```

### Comandos de desarrollo

```bash
# Instalar dependencias
pip install -r requirements.txt

# Correr localmente
python aromabot_backend.py
# → http://localhost:8000

# Endpoints clave
GET  /          → UI web para registrar ventas
GET  /health    → verificar que el bot está vivo
GET  /inventario → inventario completo en JSON
POST /chat      → { "mensaje": "texto" } → { "respuesta": "texto" }
```

---

## 3. Datos del negocio (hardcodeados en el backend)

### Distribuidores

| ID | Nombre | Teléfono | Precio venta | Mi utilidad |
|---|---|---|---|---|
| steven | Steven Rojas | 573213143902 | $5.750 | $384 |
| jairo | Jairo Jiménez | 573161289921 | $6.750 | $1.384 |
| jeferson | Jeferson Saldaña | 573044372629 | $7.250 | $1.884 |
| yo | Yo (Calle) | — | $25.000 | $19.634 |

### Perfumes y referencias de caja/sticker

| Perfume | Referencia |
|---|---|
| euphoria, holiday | euphoria |
| delphy, yara_candy | passionate |
| invicto, leblanc | succesfull |
| ultramale, kind_of_party | eternity |

### Regla de fabricación
- Cada perfume consume: 1 tarro 60ml + 40ml de alcohol
- Suma perfumes terminados al stock

### Regla de venta
- Cada perfume vendido descuenta: perfume + caja + sticker + 0.5 bolsa + 0.5 bono

---

## 4. Tablas Supabase

| Tabla | Contenido |
|---|---|
| `aroma_inventario` | clave/valor: stock de perfumes, cajas, stickers, tarros, alcohol, bolsas, bonos |
| `aroma_config` | clave/valor: utilidad_mes, ventas_steven, ventas_jairo, ventas_jeferson, ventas_yo |
| `aroma_pedidos` | historial de ventas: distribuidor, productos, total, utilidad |

---

## 5. Herramientas del agente AI

1. `consultar_inventario` — lee `aroma_inventario` completo
2. `registrar_venta(distribuidor_id, productos_json)` — descuenta inventario + calcula utilidad
3. `registrar_fabricacion(productos_json)` — descuenta tarros/alcohol, suma perfumes
4. `registrar_compra_insumos(insumos_json)` — suma insumos al inventario
5. `reporte_utilidades` — resumen financiero del mes desde `aroma_config`
6. `mensaje_motivacional(distribuidor_id)` — genera mensaje con Groq, sin mencionar dinero

---

## 6. Infraestructura n8n

**Instancia Evolution API:** `https://evolution-api-production-34616.up.railway.app`  
**API Key Evolution:** `AriaCRM2026`  
**Instancia ARIA (ADH Coaching):** conectada al número de coaching  
**Instancia AromaBot:** número nuevo (SIM pendiente de compra)

### Flujo n8n AromaBot

```
WhatsApp → Webhook (/aromabot_whatsapp) → Filtro (no soy yo / no grupo)
→ HTTP POST /chat a Railway → Respuesta → Evolution API → WhatsApp
```

---

## 7. Reglas para Claude Code

### Nunca hacer
- Nunca hardcodear precios o utilidades — están en `DISTRIBUIDORES` del backend
- Nunca calcular inventario manualmente — el código tiene la lógica
- Nunca subir `.env` a GitHub — está en `.gitignore`
- Nunca cambiar el puerto a 8000 fijo — usar `os.getenv("PORT", 8000)`

### Siempre hacer
- Mejorar el prompt del usuario antes de responder
- Explicar cada cambio técnico de dos formas: (1) como developer profesional, (2) como explicación para un niño de 10 años
- Documentar cada patrón nuevo en `docs/05_patrones_y_decisiones.md`
- Crear `requirements.txt` y `Procfile` si se agregan dependencias
- Verificar que Railway tenga las 3 variables de entorno al hacer deploy
- Probar `/health` después de cada deploy para confirmar que funciona
- Cuando se crea un endpoint nuevo, agregarlo a `docs/01_arquitectura_general.md`

### Flujo de trabajo preferido
1. Explicar el plan antes de escribir código
2. Hacer cambios mínimos — no refactorizar lo que funciona
3. Si se agrega una herramienta nueva al agente: agregarla a `tools_list` y al `SYSTEM_PROMPT`
4. Probar localmente antes de hacer push

---

## 8. Estado actual del proyecto (Mayo 2026)

- [x] Backend Python completo y funcional
- [x] Subido a GitHub: `https://github.com/JHONRO10/aromabot`
- [x] Deploy en Railway: https://web-production-f4795.up.railway.app
- [ ] Conexión WhatsApp — pendiente SIM nueva
- [ ] Flujo n8n activo — pendiente URL de Railway
- [ ] Alertas automáticas de stock — siguiente fase
- [ ] Reporte diario automático — siguiente fase
