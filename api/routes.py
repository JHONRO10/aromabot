import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from agent.tools import registrar_venta
from agent.core import invoke_agent
from db.client import get_inventario, get_config, set_inventario, set_config

app = FastAPI(title="AromaBot API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/", response_class=HTMLResponse)
async def frontend():
    with open("ui/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/chat")
async def chat(body: dict):
    mensaje = body.get("mensaje", "")
    if not mensaje:
        return {"error": "Mensaje vacío"}
    try:
        respuesta = invoke_agent(mensaje)
        return {"respuesta": respuesta, "ok": True}
    except Exception as e:
        return {"respuesta": f"❌ Error: {str(e)}", "ok": False}


@app.post("/venta")
async def venta_directa(body: dict):
    distribuidor = body.get("distribuidor", "")
    productos    = body.get("productos", {})
    if not distribuidor or not productos:
        return {"respuesta": "❌ Faltan datos", "ok": False}
    try:
        resultado = registrar_venta.invoke({
            "distribuidor_id": distribuidor,
            "productos_json":  json.dumps(productos),
        })
        return {"respuesta": resultado, "ok": True}
    except Exception as e:
        return {"respuesta": f"❌ Error: {str(e)}", "ok": False}


@app.get("/inventario")
async def get_inv():
    return get_inventario()


@app.get("/reporte")
async def get_reporte():
    return {
        "utilidad_mes":    float(get_config("utilidad_mes")),
        "ventas_steven":   float(get_config("ventas_steven")),
        "ventas_jairo":    float(get_config("ventas_jairo")),
        "ventas_jeferson": float(get_config("ventas_jeferson")),
        "ventas_yo":       float(get_config("ventas_yo")),
    }


@app.get("/reset-mes")
async def reset_mes():
    for clave in ["utilidad_mes", "ventas_steven", "ventas_jairo", "ventas_jeferson", "ventas_yo"]:
        set_config(clave, "0")
    return {"status": "✅ Contadores del mes reseteados"}


@app.get("/health")
async def health():
    return {"status": "✅ AromaBot activo", "modelo": "Llama 3.3 via Groq"}


@app.post("/ajustar-inventario")
async def ajustar_inventario(body: dict):
    if not body:
        return {"status": "❌ Body vacío", "ok": False}
    try:
        for clave, valor in body.items():
            set_inventario(clave, float(valor))
        return {"status": "✅ Inventario ajustado", "items": len(body), "ok": True}
    except Exception as e:
        return {"status": "❌ Error", "detalle": str(e), "ok": False}


@app.get("/init-inventario")
async def init_inventario():
    inventario_inicial = {
        "perfumes_invicto": 50, "perfumes_leblanc": 50, "perfumes_euphoria": 50,
        "perfumes_holiday": 50, "perfumes_delphy": 50, "perfumes_yara_candy": 50,
        "perfumes_ultramale": 50, "perfumes_kind_of_party": 50,
        "cajas_euphoria": 100, "cajas_passionate": 100, "cajas_succesfull": 100, "cajas_eternity": 100,
        "stickers_euphoria": 100, "stickers_passionate": 100, "stickers_succesfull": 100, "stickers_eternity": 100,
        "bolsas": 200, "bonos": 200, "tarros_60ml": 100, "alcohol_ml": 5000,
    }
    try:
        for clave, valor in inventario_inicial.items():
            set_inventario(clave, valor)
        return {"status": "✅ Inventario inicial cargado", "items": len(inventario_inicial)}
    except Exception as e:
        return {"status": "❌ Error", "detalle": str(e)}
