# ============================================================
# AROMABOT BACKEND — Con Groq (GRATIS) + Supabase
# ============================================================

import os
import json
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from supabase import create_client, Client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

load_dotenv()

# ─── CLIENTES ────────────────────────────────────────────────────────────────
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3,
    max_tokens=1000
)

# ─── DATOS DE NEGOCIO ────────────────────────────────────────────────────────

DISTRIBUIDORES = {
    "steven":   {"nombre":"Steven Rojas",     "tel":"573213143902", "precio":5750,  "mi_util":384,   "util_rev":19250},
    "jairo":    {"nombre":"Jairo Jiménez",    "tel":"573161289921", "precio":6750,  "mi_util":1384,  "util_rev":18250},
    "jeferson": {"nombre":"Jeferson Saldaña", "tel":"573044372629", "precio":7250,  "mi_util":1884,  "util_rev":18250},
    "yo":       {"nombre":"Yo (Calle)",       "tel":"",             "precio":25000, "mi_util":19634, "util_rev":19634},
}

PERF_REF = {
    "euphoria":"euphoria",   "holiday":"euphoria",
    "delphy":"passionate",   "yara_candy":"passionate",
    "invicto":"succesfull",  "leblanc":"succesfull",
    "ultramale":"eternity",  "kind_of_party":"eternity",
}

# ─── SUPABASE ────────────────────────────────────────────────────────────────

def get_inventario() -> dict:
    try:
        res = supabase.table("aroma_inventario").select("*").execute()
        return {row["clave"]: row["valor"] for row in res.data}
    except Exception as e:
        return {"error": str(e)}

def set_inventario(clave: str, valor: float):
    supabase.table("aroma_inventario").upsert({"clave": clave, "valor": valor}).execute()

def get_config(clave: str) -> str:
    try:
        res = supabase.table("aroma_config").select("valor").eq("clave", clave).execute()
        return res.data[0]["valor"] if res.data else "0"
    except:
        return "0"

def set_config(clave: str, valor: str):
    supabase.table("aroma_config").upsert({"clave": clave, "valor": valor}).execute()

def registrar_pedido_db(distribuidor: str, productos: dict, total: int, utilidad: float):
    supabase.table("aroma_pedidos").insert({
        "distribuidor": distribuidor,
        "productos": productos,
        "total_perfumes": total,
        "mi_utilidad": utilidad
    }).execute()

# ─── LÓGICA DE DESCUENTO ─────────────────────────────────────────────────────

def descuento_venta(inv: dict, pedido: dict) -> dict:
    n = dict(inv)
    errores = []
    for perf, cant in pedido.items():
        c = int(cant)
        if c <= 0: continue
        ref = PERF_REF.get(perf)
        if not ref:
            errores.append(f"Perfume desconocido: {perf}")
            continue
        if n.get(f"perfumes_{perf}", 0) < c:
            errores.append(f"Sin stock {perf}: hay {n.get(f'perfumes_{perf}',0)}, piden {c}")
        if n.get(f"cajas_{ref}", 0) < c:
            errores.append(f"Sin cajas {ref}: hay {n.get(f'cajas_{ref}',0)}")
        if n.get(f"stickers_{ref}", 0) < c:
            errores.append(f"Sin stickers {ref}: hay {n.get(f'stickers_{ref}',0)}")
        if n.get("bolsas", 0) < c * 0.5:
            errores.append(f"Sin bolsas: hay {n.get('bolsas',0)}")
        if n.get("bonos", 0) < c * 0.5:
            errores.append(f"Sin bonos: hay {n.get('bonos',0)}")
    if errores:
        return {"ok": False, "errores": errores, "inv": inv}
    for perf, cant in pedido.items():
        c = int(cant)
        if c <= 0: continue
        ref = PERF_REF[perf]
        n[f"perfumes_{perf}"] = n.get(f"perfumes_{perf}", 0) - c
        n[f"cajas_{ref}"]     = n.get(f"cajas_{ref}", 0) - c
        n[f"stickers_{ref}"]  = n.get(f"stickers_{ref}", 0) - c
        n["bolsas"]           = n.get("bolsas", 0) - (c * 0.5)
        n["bonos"]            = n.get("bonos", 0) - (c * 0.5)
    return {"ok": True, "errores": [], "inv": n}


def descuento_fabricacion(inv: dict, produccion: dict) -> dict:
    n = dict(inv)
    total = sum(int(v) for v in produccion.values())
    errores = []
    if n.get("tarros_60ml", 0) < total:
        errores.append(f"Sin tarros: hay {n.get('tarros_60ml',0)}, necesitas {total}")
    if n.get("alcohol_ml", 0) < total * 40:
        errores.append(f"Sin alcohol: hay {n.get('alcohol_ml',0)}ml, necesitas {total*40}ml")
    if errores:
        return {"ok": False, "errores": errores, "inv": inv}
    for perf, cant in produccion.items():
        c = int(cant)
        if c <= 0: continue
        n["tarros_60ml"]      = n.get("tarros_60ml", 0) - c
        n["alcohol_ml"]       = n.get("alcohol_ml", 0) - (c * 40)
        n[f"perfumes_{perf}"] = n.get(f"perfumes_{perf}", 0) + c
    return {"ok": True, "errores": [], "inv": n}


# ─── HERRAMIENTAS ────────────────────────────────────────────────────────────

@tool
def consultar_inventario() -> str:
    """Consulta el inventario completo actual."""
    inv = get_inventario()
    if "error" in inv:
        return f"❌ Error: {inv['error']}"
    r = "📦 INVENTARIO ACTUAL:\n\n✨ PERFUMES:\n"
    for k, v in inv.items():
        if k.startswith("perfumes_"):
            nombre = k.replace("perfumes_","").replace("_"," ").title()
            alerta = " ⚠️" if v <= 5 else ""
            r += f"  {nombre}: {int(v)}{alerta}\n"
    r += "\n📦 CAJAS:\n"
    for k, v in inv.items():
        if k.startswith("cajas_"):
            nombre = k.replace("cajas_","").title()
            alerta = " ⚠️" if v <= 20 else ""
            r += f"  {nombre}: {int(v)}{alerta}\n"
    r += "\n🫙 INSUMOS:\n"
    for k in ["tarros_60ml","alcohol_ml","bolsas","bonos"]:
        r += f"  {k.replace('_',' ').title()}: {round(inv.get(k,0), 1)}\n"
    return r


@tool
def registrar_venta(distribuidor_id: str, productos_json: str) -> str:
    """Registra una venta y descuenta inventario automáticamente."""
    dist = DISTRIBUIDORES.get(distribuidor_id.lower())
    if not dist:
        return f"❌ Distribuidor no encontrado. Usa: steven, jairo, jeferson, yo"
    try:
        productos = json.loads(productos_json)
    except:
        return '❌ Formato incorrecto. Ejemplo: {"invicto": 5, "leblanc": 3}'
    inv_actual = get_inventario()
    resultado = descuento_venta(inv_actual, productos)
    if not resultado["ok"]:
        return "❌ Stock insuficiente:\n" + "\n".join(resultado["errores"])
    nuevo_inv = resultado["inv"]
    for clave, valor in nuevo_inv.items():
        if nuevo_inv.get(clave) != inv_actual.get(clave):
            set_inventario(clave, valor)
    total_perfs = sum(int(v) for v in productos.values())
    mi_utilidad = total_perfs * dist["mi_util"]
    nueva_util = float(get_config("utilidad_mes")) + mi_utilidad
    set_config("utilidad_mes", str(nueva_util))
    ventas_key = f"ventas_{distribuidor_id.lower()}"
    nuevas_ventas = float(get_config(ventas_key)) + total_perfs
    set_config(ventas_key, str(nuevas_ventas))
    registrar_pedido_db(dist["nombre"], productos, total_perfs, mi_utilidad)
    items = ", ".join(f"{v} {k.replace('_',' ').title()}" for k,v in productos.items())
    return f"""✅ Venta registrada — {dist['nombre']}
📦 {items}
💰 Mi ganancia: ${mi_utilidad:,.0f}
📊 Utilidad mes: ${nueva_util:,.0f}
✅ Cajas, stickers, bolsas y bonos descontados automáticamente"""


@tool
def registrar_fabricacion(productos_json: str) -> str:
    """Registra fabricación de perfumes. Descuenta tarros y alcohol."""
    try:
        produccion = json.loads(productos_json)
    except:
        return '❌ Formato incorrecto. Ejemplo: {"invicto": 20}'
    inv_actual = get_inventario()
    resultado = descuento_fabricacion(inv_actual, produccion)
    if not resultado["ok"]:
        return "❌ No se puede fabricar:\n" + "\n".join(resultado["errores"])
    nuevo_inv = resultado["inv"]
    for clave, valor in nuevo_inv.items():
        if nuevo_inv.get(clave) != inv_actual.get(clave):
            set_inventario(clave, valor)
    total = sum(int(v) for v in produccion.values())
    items = ", ".join(f"{v} {k.replace('_',' ').title()}" for k,v in produccion.items())
    return f"""✅ Fabricación registrada
🏭 {items}
🫙 Tarros descontados: -{total}
🧪 Alcohol descontado: -{total*40}ml
✨ Perfumes sumados al stock"""


@tool
def registrar_compra_insumos(insumos_json: str) -> str:
    """Registra compra de insumos y suma al inventario."""
    try:
        compras = json.loads(insumos_json)
    except:
        return "❌ Formato incorrecto."
    inv_actual = get_inventario()
    resumen = []
    for clave, cantidad in compras.items():
        anterior = inv_actual.get(clave, 0)
        nuevo = anterior + float(cantidad)
        set_inventario(clave, nuevo)
        nombre = clave.replace("_"," ").title()
        resumen.append(f"  {nombre}: {anterior} → {nuevo} (+{cantidad})")
    return "✅ Compra registrada:\n" + "\n".join(resumen)


@tool
def reporte_utilidades() -> str:
    """Genera reporte de utilidades del mes."""
    util_mes = float(get_config("utilidad_mes"))
    total_hoy = 0
    lineas = []
    for d_id, d_info in DISTRIBUIDORES.items():
        v = float(get_config(f"ventas_{d_id}"))
        util = v * d_info["mi_util"]
        total_hoy += util
        if v > 0:
            lineas.append(f"  {d_info['nombre']}: {int(v)} prf → ${util:,.0f}")
    r = f"""📊 REPORTE SUCCESSFUL AROMAS
💰 Utilidad acumulada mes: ${util_mes:,.0f}
🛒 Ganancia de hoy: ${total_hoy:,.0f}"""
    if lineas:
        r += "\n\nPor distribuidor hoy:\n" + "\n".join(lineas)
    return r


@tool
def mensaje_motivacional(distribuidor_id: str) -> str:
    """Genera mensaje motivacional sin números ni dinero."""
    dist = DISTRIBUIDORES.get(distribuidor_id.lower())
    if not dist:
        return "❌ Distribuidor no encontrado."
    prompt = f"""Genera un mensaje motivacional poderoso para {dist['nombre']} de Successful Aromas.
REGLAS: Sin números ni dinero. Solo consciencia, disciplina, identidad y propósito.
Máximo 5 líneas. Con emojis. Como mentor de vida, no jefe de ventas."""
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


# ─── SYSTEM PROMPT ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Eres AromaBot, el agente inteligente de operaciones de SUCCESSFUL AROMAS.
Tu propósito es gestionar el negocio con precisión, rapidez y claridad. Siempre hablas en español.

🛠️ USO DE HERRAMIENTAS — OBLIGATORIO:
• Stock/inventario → consultar_inventario()
• Registrar venta → registrar_venta(distribuidor_id, productos_json)
• Fabricar → registrar_fabricacion(productos_json)
• Comprar insumos → registrar_compra_insumos(insumos_json)
• Reporte/ganancias → reporte_utilidades()
• Motivar distribuidor → mensaje_motivacional(distribuidor_id)

REGLAS:
- NUNCA calcules inventario manualmente
- SIEMPRE muestra el resultado COMPLETO de la herramienta
- Si detectas stock ≤5 unidades, menciona la alerta
- Sé profesional, cercano y usa emojis

Distribuidores: steven, jairo, jeferson, yo
Perfumes: euphoria, holiday, delphy, yara_candy, invicto, leblanc, ultramale, kind_of_party"""

# ─── GRAFO LANGGRAPH ──────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

tools_list = [
    consultar_inventario, registrar_venta, registrar_fabricacion,
    registrar_compra_insumos, reporte_utilidades, mensaje_motivacional,
]

llm_con_tools = llm.bind_tools(tools_list)
tools_map = {t.name: t for t in tools_list}


def nodo_agente(state: AgentState):
    msgs = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_con_tools.invoke(msgs)
    return {"messages": [response]}


def nodo_tools(state: AgentState):
    ultimo = state["messages"][-1]
    resultados = []
    for tc in ultimo.tool_calls:
        resultado = tools_map[tc["name"]].invoke(tc["args"])
        resultados.append(ToolMessage(content=str(resultado), tool_call_id=tc["id"]))
    return {"messages": resultados}


def debe_continuar(state: AgentState) -> Literal["tools","fin"]:
    ultimo = state["messages"][-1]
    if hasattr(ultimo, "tool_calls") and ultimo.tool_calls:
        return "tools"
    return "fin"


grafo = StateGraph(AgentState)
grafo.add_node("agente", nodo_agente)
grafo.add_node("tools", nodo_tools)
grafo.set_entry_point("agente")
grafo.add_conditional_edges("agente", debe_continuar, {"tools":"tools","fin":END})
grafo.add_edge("tools", "agente")
aromas_bot = grafo.compile()


# ─── API FASTAPI ──────────────────────────────────────────────────────────────

app = FastAPI(title="AromaBot API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/", response_class=HTMLResponse)
async def frontend():
    return """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>Successful Aromas</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:#0d0d1a;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-height:100vh;padding-bottom:40px}
    header{text-align:center;padding:20px 16px 0}
    header h1{font-size:1.4rem;font-weight:700;background:linear-gradient(135deg,#a78bfa,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
    header p{font-size:.75rem;color:#64748b;margin-top:3px}
    .tabs{display:flex;background:#0d0d1a;border-bottom:1px solid #1e1e3f;position:sticky;top:0;z-index:10}
    .tab-btn{flex:1;padding:14px 4px;background:none;border:none;color:#64748b;font-size:.8rem;font-weight:600;cursor:pointer;border-bottom:2px solid transparent;transition:all .2s}
    .tab-btn.active{color:#a78bfa;border-bottom-color:#7c3aed}
    .tab-content{display:none;padding:16px}
    .tab-content.active{display:block}
    .card{background:#131326;border:1px solid #1e1e3f;border-radius:16px;padding:18px 16px;margin-bottom:14px}
    .card-title{font-size:.7rem;font-weight:600;letter-spacing:1.5px;color:#7c3aed;text-transform:uppercase;margin-bottom:12px}
    .big-number{font-size:2rem;font-weight:800;color:#a78bfa}
    .sub-label{font-size:.75rem;color:#64748b;margin-top:2px}
    .inv-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
    .inv-item{background:#1a1a35;border-radius:12px;padding:12px 10px;text-align:center}
    .inv-item .nombre{font-size:.72rem;color:#94a3b8;margin-bottom:6px;text-transform:capitalize}
    .inv-item .cantidad{font-size:1.4rem;font-weight:800}
    .verde .cantidad{color:#22c55e}
    .amarillo .cantidad{color:#f59e0b}
    .rojo .cantidad{color:#ef4444}
    .rojo{border:1px solid #ef4444}
    .dist-row{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #1e1e3f}
    .dist-row:last-child{border-bottom:none}
    .dist-nombre{font-size:.9rem;color:#e2e8f0}
    .dist-ventas{font-size:.85rem;color:#a78bfa;font-weight:700}
    .alerta{background:#2d0a0a;border:1px solid #ef4444;border-radius:10px;padding:10px 14px;margin-bottom:8px;font-size:.82rem;color:#fca5a5}
    select{width:100%;padding:14px 16px;background:#1e1e3f;border:1px solid #2d2d5e;border-radius:10px;color:#e2e8f0;font-size:1rem;appearance:none;-webkit-appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%237c3aed' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 14px center;outline:none}
    select:focus{border-color:#7c3aed}
    .perfume-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
    .perfume-item{background:#1a1a35;border:1px solid #2d2d5e;border-radius:12px;padding:12px 10px;text-align:center}
    .perfume-item .name{font-size:.82rem;font-weight:600;color:#c4b5fd;margin-bottom:10px}
    .counter{display:flex;align-items:center;justify-content:center;gap:8px}
    .counter button{width:36px;height:36px;border-radius:50%;border:none;background:#2d2d5e;color:#a78bfa;font-size:1.3rem;cursor:pointer;display:flex;align-items:center;justify-content:center;-webkit-tap-highlight-color:transparent}
    .counter button:active{background:#7c3aed}
    .counter input[type=number]{width:44px;height:36px;text-align:center;background:#0d0d1a;border:1px solid #2d2d5e;border-radius:8px;color:#e2e8f0;font-size:1.1rem;font-weight:700;-moz-appearance:textfield;outline:none}
    .counter input::-webkit-inner-spin-button,.counter input::-webkit-outer-spin-button{-webkit-appearance:none}
    .btn-primary{width:100%;padding:16px;background:linear-gradient(135deg,#7c3aed,#5b21b6);border:none;border-radius:12px;color:#fff;font-size:1.05rem;font-weight:700;cursor:pointer;margin-top:8px;-webkit-tap-highlight-color:transparent;transition:opacity .2s}
    .btn-primary:disabled{opacity:.5;cursor:not-allowed}
    .btn-primary:active:not(:disabled){opacity:.85}
    .msg-box{display:none;border-radius:14px;padding:18px 16px;margin-top:16px;font-size:.9rem;line-height:1.7;white-space:pre-wrap;word-break:break-word;border:1px solid #2d2d5e;background:#131326}
    .msg-box.ok{border-color:#22c55e;color:#86efac}
    .msg-box.err{border-color:#ef4444;color:#fca5a5}
    .spinner{display:none;text-align:center;padding:12px 0;color:#7c3aed;font-size:.9rem}
    #chat-input{width:100%;min-height:90px;padding:14px;background:#1e1e3f;border:1px solid #2d2d5e;border-radius:12px;color:#e2e8f0;font-size:.95rem;resize:none;outline:none;font-family:inherit}
    #chat-input:focus{border-color:#7c3aed}
    .refresh-hint{text-align:center;font-size:.7rem;color:#334155;margin-top:8px}
  </style>
</head>
<body>
<header>
  <h1>✨ Successful Aromas</h1>
  <p>Panel de control</p>
</header>

<div class="tabs">
  <button class="tab-btn active" onclick="showTab('ventas',this)">📦 Ventas</button>
  <button class="tab-btn" onclick="showTab('dashboard',this)">📊 Dashboard</button>
  <button class="tab-btn" onclick="showTab('chat',this)">💬 Chat</button>
</div>

<!-- TAB VENTAS -->
<div id="tab-ventas" class="tab-content active">
  <div class="card">
    <div class="card-title">Vendedor</div>
    <select id="distribuidor">
      <option value="steven">Steven</option>
      <option value="jairo">Jairo</option>
      <option value="jeferson">Jeferson</option>
      <option value="yo">Yo</option>
    </select>
  </div>
  <div class="card">
    <div class="card-title">Perfumes</div>
    <div class="perfume-grid">
      <div class="perfume-item"><div class="name">Euphoria</div><div class="counter"><button onclick="cambiar('euphoria',-1)">−</button><input type="number" id="euphoria" value="0" min="0" max="99"><button onclick="cambiar('euphoria',1)">+</button></div></div>
      <div class="perfume-item"><div class="name">Delphy</div><div class="counter"><button onclick="cambiar('delphy',-1)">−</button><input type="number" id="delphy" value="0" min="0" max="99"><button onclick="cambiar('delphy',1)">+</button></div></div>
      <div class="perfume-item"><div class="name">Yara Candy</div><div class="counter"><button onclick="cambiar('yara_candy',-1)">−</button><input type="number" id="yara_candy" value="0" min="0" max="99"><button onclick="cambiar('yara_candy',1)">+</button></div></div>
      <div class="perfume-item"><div class="name">Holiday</div><div class="counter"><button onclick="cambiar('holiday',-1)">−</button><input type="number" id="holiday" value="0" min="0" max="99"><button onclick="cambiar('holiday',1)">+</button></div></div>
      <div class="perfume-item"><div class="name">Invicto</div><div class="counter"><button onclick="cambiar('invicto',-1)">−</button><input type="number" id="invicto" value="0" min="0" max="99"><button onclick="cambiar('invicto',1)">+</button></div></div>
      <div class="perfume-item"><div class="name">Kind of Party</div><div class="counter"><button onclick="cambiar('kind_of_party',-1)">−</button><input type="number" id="kind_of_party" value="0" min="0" max="99"><button onclick="cambiar('kind_of_party',1)">+</button></div></div>
      <div class="perfume-item"><div class="name">Ultramale</div><div class="counter"><button onclick="cambiar('ultramale',-1)">−</button><input type="number" id="ultramale" value="0" min="0" max="99"><button onclick="cambiar('ultramale',1)">+</button></div></div>
      <div class="perfume-item"><div class="name">Leblanc</div><div class="counter"><button onclick="cambiar('leblanc',-1)">−</button><input type="number" id="leblanc" value="0" min="0" max="99"><button onclick="cambiar('leblanc',1)">+</button></div></div>
    </div>
  </div>
  <button class="btn-primary" id="btn-registrar" onclick="registrar()">REGISTRAR VENTA</button>
  <div class="spinner" id="spin-venta">⏳ Procesando...</div>
  <div class="msg-box" id="msg-venta"></div>
</div>

<!-- TAB DASHBOARD -->
<div id="tab-dashboard" class="tab-content">
  <div id="alertas-box"></div>
  <div class="card">
    <div class="card-title">💰 Utilidad del mes</div>
    <div class="big-number" id="util-mes">—</div>
    <div class="sub-label">Ganancia acumulada</div>
  </div>
  <div class="card">
    <div class="card-title">🛒 Ventas por distribuidor</div>
    <div class="dist-row"><span class="dist-nombre">Steven</span><span class="dist-ventas" id="v-steven">—</span></div>
    <div class="dist-row"><span class="dist-nombre">Jairo</span><span class="dist-ventas" id="v-jairo">—</span></div>
    <div class="dist-row"><span class="dist-nombre">Jeferson</span><span class="dist-ventas" id="v-jeferson">—</span></div>
    <div class="dist-row"><span class="dist-nombre">Yo (Calle)</span><span class="dist-ventas" id="v-yo">—</span></div>
  </div>
  <div class="card">
    <div class="card-title">📦 Perfumes en stock</div>
    <div class="inv-grid" id="inv-perfumes"></div>
  </div>
  <div class="card">
    <div class="card-title">🫙 Insumos</div>
    <div class="inv-grid" id="inv-insumos"></div>
  </div>
  <p class="refresh-hint" id="last-update"></p>
</div>

<!-- TAB CHAT -->
<div id="tab-chat" class="tab-content">
  <div class="card">
    <div class="card-title">💬 Habla con AromaBot</div>
    <textarea id="chat-input" placeholder="Ej: ¿Cuánto stock tengo? / Dame el reporte / Fabricamos 20 invicto"></textarea>
    <button class="btn-primary" id="btn-chat" onclick="enviarChat()">ENVIAR</button>
  </div>
  <div class="spinner" id="spin-chat">⏳ AromaBot pensando...</div>
  <div class="msg-box" id="msg-chat"></div>
</div>

<script>
  const PERFUMES = ['euphoria','delphy','yara_candy','holiday','invicto','kind_of_party','ultramale','leblanc'];

  function showTab(name, btn) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById('tab-' + name).classList.add('active');
    btn.classList.add('active');
    if (name === 'dashboard') loadDashboard();
  }

  // ── VENTAS ──
  function cambiar(id, delta) {
    const el = document.getElementById(id);
    el.value = Math.max(0, (parseInt(el.value) || 0) + delta);
  }

  async function registrar() {
    const dist = document.getElementById('distribuidor').value;
    const productos = {};
    PERFUMES.forEach(p => { const v = parseInt(document.getElementById(p).value)||0; if(v>0) productos[p]=v; });
    if (!Object.keys(productos).length) { showMsg('msg-venta', 'Debes ingresar al menos un perfume.', false); return; }
    setLoading('btn-registrar', 'spin-venta', true);
    try {
      const res = await fetch('/venta', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({distribuidor:dist,productos})});
      const data = await res.json();
      showMsg('msg-venta', data.respuesta || data.error, data.ok !== false);
      if (data.ok !== false) PERFUMES.forEach(p => document.getElementById(p).value = 0);
    } catch(e) { showMsg('msg-venta', 'Error de conexión: '+e.message, false); }
    finally { setLoading('btn-registrar', 'spin-venta', false); }
  }

  // ── DASHBOARD ──
  function semaforo(val) { return val > 20 ? 'verde' : val >= 10 ? 'amarillo' : 'rojo'; }
  function formatCOP(n) { return '$' + Math.round(n).toLocaleString('es-CO'); }

  async function loadDashboard() {
    try {
      const [inv, rep] = await Promise.all([
        fetch('/inventario').then(r=>r.json()),
        fetch('/reporte').then(r=>r.json())
      ]);
      document.getElementById('util-mes').textContent = formatCOP(rep.utilidad_mes);
      document.getElementById('v-steven').textContent   = rep.ventas_steven + ' prf';
      document.getElementById('v-jairo').textContent    = rep.ventas_jairo + ' prf';
      document.getElementById('v-jeferson').textContent = rep.ventas_jeferson + ' prf';
      document.getElementById('v-yo').textContent       = rep.ventas_yo + ' prf';

      const perfGrid = document.getElementById('inv-perfumes');
      perfGrid.innerHTML = '';
      const alertBox = document.getElementById('alertas-box');
      alertBox.innerHTML = '';
      Object.keys(inv).filter(k=>k.startsWith('perfumes_')).forEach(k => {
        const nombre = k.replace('perfumes_','').replace(/_/g,' ');
        const val = Math.round(inv[k]);
        const cls = semaforo(val);
        perfGrid.innerHTML += `<div class="inv-item ${cls}"><div class="nombre">${nombre}</div><div class="cantidad">${val}</div></div>`;
        if (val < 10) alertBox.innerHTML += `<div class="alerta">⚠️ Stock bajo: <strong>${nombre}</strong> — ${val} unidades</div>`;
      });

      const insGrid = document.getElementById('inv-insumos');
      insGrid.innerHTML = '';
      [{k:'tarros_60ml',l:'Tarros 60ml',min:50},{k:'bolsas',l:'Bolsas',min:50},{k:'bonos',l:'Bonos',min:50},{k:'alcohol_ml',l:'Alcohol (ml)',min:2000}].forEach(({k,l,min}) => {
        const val = Math.round(inv[k]||0);
        const cls = val > min*2 ? 'verde' : val > min ? 'amarillo' : 'rojo';
        insGrid.innerHTML += `<div class="inv-item ${cls}"><div class="nombre">${l}</div><div class="cantidad">${val.toLocaleString('es-CO')}</div></div>`;
      });

      document.getElementById('last-update').textContent = 'Actualizado: ' + new Date().toLocaleTimeString('es-CO');
    } catch(e) {
      document.getElementById('inv-perfumes').innerHTML = '<p style="color:#ef4444;padding:8px">Error cargando datos</p>';
    }
  }

  setInterval(() => {
    if (document.getElementById('tab-dashboard').classList.contains('active')) loadDashboard();
  }, 30000);

  // ── CHAT ──
  async function enviarChat() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;
    setLoading('btn-chat', 'spin-chat', true);
    try {
      const res = await fetch('/chat', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensaje:msg})});
      const data = await res.json();
      showMsg('msg-chat', data.respuesta || data.error, data.ok !== false);
    } catch(e) { showMsg('msg-chat', 'Error: '+e.message, false); }
    finally { setLoading('btn-chat', 'spin-chat', false); }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('chat-input').addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); enviarChat(); }
    });
  });

  // ── UTILS ──
  function showMsg(id, texto, ok) {
    const el = document.getElementById(id);
    el.textContent = texto; el.className = 'msg-box ' + (ok ? 'ok' : 'err'); el.style.display = 'block';
    el.scrollIntoView({behavior:'smooth',block:'nearest'});
  }

  function setLoading(btnId, spinId, loading) {
    document.getElementById(btnId).disabled = loading;
    document.getElementById(spinId).style.display = loading ? 'block' : 'none';
  }
</script>
</body>
</html>"""


# ─── ENDPOINTS ───────────────────────────────────────────────────────────────

@app.post("/venta")
async def venta_directa(body: dict):
    distribuidor = body.get("distribuidor", "")
    productos = body.get("productos", {})
    if not distribuidor or not productos:
        return {"respuesta": "❌ Faltan datos", "ok": False}
    try:
        resultado = registrar_venta.invoke({
            "distribuidor_id": distribuidor,
            "productos_json": json.dumps(productos)
        })
        return {"respuesta": resultado, "ok": True}
    except Exception as e:
        return {"respuesta": f"❌ Error: {str(e)}", "ok": False}


@app.post("/chat")
async def chat(body: dict):
    mensaje = body.get("mensaje", "")
    if not mensaje:
        return {"error": "Mensaje vacío"}
    try:
        output = aromas_bot.invoke({"messages": [HumanMessage(content=mensaje)]})
        return {"respuesta": output["messages"][-1].content, "ok": True}
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
    return {"status": "✅ Contadores del mes reseteados a cero"}


@app.get("/health")
async def health():
    return {"status": "✅ AromaBot activo", "modelo": "Llama 3.3 via Groq"}


@app.post("/ajustar-inventario")
async def ajustar_inventario(body: dict):
    if not body:
        return {"status": "❌ Body vacío", "ok": False}
    try:
        actualizados = []
        for clave, valor in body.items():
            set_inventario(clave, float(valor))
            actualizados.append(f"{clave}: {valor}")
        return {"status": "✅ Inventario ajustado", "items_actualizados": len(actualizados), "ok": True}
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


def responder(mensaje: str) -> str:
    output = aromas_bot.invoke({"messages": [HumanMessage(content=mensaje)]})
    return output["messages"][-1].content


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print("🚀 AromaBot arrancando...")
    print(f"📡 API en http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
