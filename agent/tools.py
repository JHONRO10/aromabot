import json
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

from data.negocio import DISTRIBUIDORES, PERF_REF, COSTOS

def _util_por_perfume(dist: dict) -> int:
    return dist["precio"] - COSTOS["perfume"]
from db.client import get_inventario, set_inventario, get_config, set_config, registrar_pedido


def _descuento_venta(inv: dict, pedido: dict) -> dict:
    n = dict(inv)
    errores = []
    for perf, cant in pedido.items():
        c = int(cant)
        if c <= 0:
            continue
        ref = PERF_REF.get(perf)
        if not ref:
            errores.append(f"Perfume desconocido: {perf}")
            continue
        if n.get(f"perfumes_{perf}", 0) < c:
            errores.append(f"Sin stock {perf}: hay {n.get(f'perfumes_{perf}', 0)}, piden {c}")
        if n.get(f"cajas_{ref}", 0) < c:
            errores.append(f"Sin cajas {ref}: hay {n.get(f'cajas_{ref}', 0)}")
        if n.get(f"stickers_{ref}", 0) < c:
            errores.append(f"Sin stickers {ref}: hay {n.get(f'stickers_{ref}', 0)}")
        if n.get("bolsas", 0) < c * 0.5:
            errores.append(f"Sin bolsas: hay {n.get('bolsas', 0)}")
        if n.get("bonos", 0) < c * 0.5:
            errores.append(f"Sin bonos: hay {n.get('bonos', 0)}")
    if errores:
        return {"ok": False, "errores": errores, "inv": inv}
    for perf, cant in pedido.items():
        c = int(cant)
        if c <= 0:
            continue
        ref = PERF_REF[perf]
        n[f"perfumes_{perf}"] = n.get(f"perfumes_{perf}", 0) - c
        n[f"cajas_{ref}"]     = n.get(f"cajas_{ref}", 0) - c
        n[f"stickers_{ref}"]  = n.get(f"stickers_{ref}", 0) - c
        n["bolsas"]           = n.get("bolsas", 0) - (c * 0.5)
        n["bonos"]            = n.get("bonos", 0) - (c * 0.5)
    return {"ok": True, "errores": [], "inv": n}


def _descuento_fabricacion(inv: dict, produccion: dict) -> dict:
    n = dict(inv)
    total = sum(int(v) for v in produccion.values())
    errores = []
    if n.get("tarros_60ml", 0) < total:
        errores.append(f"Sin tarros: hay {n.get('tarros_60ml', 0)}, necesitas {total}")
    if n.get("alcohol_ml", 0) < total * 40:
        errores.append(f"Sin alcohol: hay {n.get('alcohol_ml', 0)}ml, necesitas {total * 40}ml")
    if errores:
        return {"ok": False, "errores": errores, "inv": inv}
    for perf, cant in produccion.items():
        c = int(cant)
        if c <= 0:
            continue
        n["tarros_60ml"]      = n.get("tarros_60ml", 0) - c
        n["alcohol_ml"]       = n.get("alcohol_ml", 0) - (c * 40)
        n[f"perfumes_{perf}"] = n.get(f"perfumes_{perf}", 0) + c
    return {"ok": True, "errores": [], "inv": n}


@tool
def consultar_inventario() -> str:
    """Consulta el inventario completo con cantidades de stock y alertas de nivel bajo."""
    inv = get_inventario()
    if "error" in inv:
        return f"❌ Error conectando con Supabase: {inv['error']}"
    r = "📦 INVENTARIO ACTUAL:\n\n✨ PERFUMES:\n"
    for k, v in inv.items():
        if k.startswith("perfumes_"):
            nombre = k.replace("perfumes_", "").replace("_", " ").title()
            val = int(v)
            alerta = " 🔴" if val <= 5 else (" 🟡" if val <= 15 else "")
            r += f"  {nombre}: {val}{alerta}\n"
    r += "\n📦 CAJAS:\n"
    for k, v in inv.items():
        if k.startswith("cajas_"):
            nombre = k.replace("cajas_", "").title()
            val = int(v)
            alerta = " 🔴" if val < 20 else (" 🟡" if val < 50 else "")
            r += f"  {nombre}: {val}{alerta}\n"
    r += "\n🫙 INSUMOS:\n"
    for k in ["tarros_60ml", "alcohol_ml", "bolsas", "bonos"]:
        r += f"  {k.replace('_', ' ').title()}: {round(inv.get(k, 0), 1)}\n"
    return r


@tool
def calcular_valor_inventario() -> str:
    """Calcula el valor total en pesos colombianos del inventario según costos de producción."""
    inv = get_inventario()
    if "error" in inv:
        return f"❌ Error: {inv['error']}"

    val_perfumes = 0
    lineas_perf = []
    for k, v in inv.items():
        if k.startswith("perfumes_"):
            nombre = k.replace("perfumes_", "").replace("_", " ").title()
            val = int(v) * COSTOS["perfume"]
            val_perfumes += val
            lineas_perf.append(f"  {nombre}: {int(v)} u × ${COSTOS['perfume']:,} = ${val:,.0f}")

    val_cajas     = sum(v * COSTOS["cajas"]    for k, v in inv.items() if k.startswith("cajas_"))
    val_stickers  = sum(v * COSTOS["stickers"] for k, v in inv.items() if k.startswith("stickers_"))

    tarros  = inv.get("tarros_60ml", 0)
    alcohol = inv.get("alcohol_ml", 0)
    bolsas  = inv.get("bolsas", 0)
    bonos   = inv.get("bonos", 0)
    val_tarros  = tarros  * COSTOS["tarros_60ml"]
    val_alcohol = alcohol * COSTOS["alcohol_ml"]
    val_bolsas  = bolsas  * COSTOS["bolsas"]
    val_bonos   = bonos   * COSTOS["bonos"]

    total = val_perfumes + val_cajas + val_stickers + val_tarros + val_alcohol + val_bolsas + val_bonos

    perf_lines = "\n".join(lineas_perf)
    return f"""💰 VALOR DEL INVENTARIO EN PESOS

✨ Perfumes terminados: ${val_perfumes:,.0f}
{perf_lines}

📦 Cajas & Stickers: ${val_cajas + val_stickers:,.0f}
  Cajas ({sum(int(v) for k,v in inv.items() if k.startswith('cajas_'))} u × ${COSTOS['cajas']:,}): ${val_cajas:,.0f}
  Stickers ({sum(int(v) for k,v in inv.items() if k.startswith('stickers_'))} u × ${COSTOS['stickers']:,}): ${val_stickers:,.0f}

🫙 Insumos:
  Tarros ({int(tarros)} u × ${COSTOS['tarros_60ml']:,}): ${val_tarros:,.0f}
  Alcohol ({int(alcohol)} ml × ${COSTOS['alcohol_ml']:,}/ml): ${val_alcohol:,.0f}
  Bolsas ({int(bolsas)} u × ${COSTOS['bolsas']:,}): ${val_bolsas:,.0f}
  Bonos ({int(bonos)} u × ${COSTOS['bonos']:,}): ${val_bonos:,.0f}

━━━━━━━━━━━━━━━━━━━━━━━━
💎 TOTAL INVENTARIO: ${total:,.0f}"""


@tool
def registrar_venta(distribuidor_id: str, productos_json: str) -> str:
    """Registra una venta y descuenta inventario automáticamente. productos_json debe ser JSON con perfume: cantidad."""
    dist = DISTRIBUIDORES.get(distribuidor_id.lower())
    if not dist:
        return "❌ Distribuidor no encontrado. Usa: steven, jairo, jeferson, yo"
    try:
        productos = json.loads(productos_json)
    except Exception:
        return '❌ Formato incorrecto. Ejemplo: {"invicto": 5, "leblanc": 3}'
    inv_actual = get_inventario()
    resultado = _descuento_venta(inv_actual, productos)
    if not resultado["ok"]:
        return "❌ Stock insuficiente:\n" + "\n".join(resultado["errores"])
    nuevo_inv = resultado["inv"]
    for clave, valor in nuevo_inv.items():
        if nuevo_inv.get(clave) != inv_actual.get(clave):
            set_inventario(clave, valor)
    total_perfs = sum(int(v) for v in productos.values())
    mi_utilidad = total_perfs * _util_por_perfume(dist)
    nueva_util  = float(get_config("utilidad_mes")) + mi_utilidad
    set_config("utilidad_mes", str(nueva_util))
    ventas_key = f"ventas_{distribuidor_id.lower()}"
    set_config(ventas_key, str(float(get_config(ventas_key)) + total_perfs))
    registrar_pedido(dist["nombre"], productos, total_perfs, mi_utilidad)
    items = ", ".join(f"{v} {k.replace('_', ' ').title()}" for k, v in productos.items())
    return f"""✅ Venta registrada — {dist['nombre']}
📦 {items}
💰 Mi ganancia: ${mi_utilidad:,.0f}
📊 Utilidad mes: ${nueva_util:,.0f}
✅ Cajas, stickers, bolsas y bonos descontados"""


@tool
def registrar_fabricacion(productos_json: str) -> str:
    """Registra fabricación de perfumes. Descuenta tarros y alcohol, suma perfumes al stock."""
    try:
        produccion = json.loads(productos_json)
    except Exception:
        return '❌ Formato incorrecto. Ejemplo: {"invicto": 20}'
    inv_actual = get_inventario()
    resultado  = _descuento_fabricacion(inv_actual, produccion)
    if not resultado["ok"]:
        return "❌ No se puede fabricar:\n" + "\n".join(resultado["errores"])
    nuevo_inv = resultado["inv"]
    for clave, valor in nuevo_inv.items():
        if nuevo_inv.get(clave) != inv_actual.get(clave):
            set_inventario(clave, valor)
    total = sum(int(v) for v in produccion.values())
    items = ", ".join(f"{v} {k.replace('_', ' ').title()}" for k, v in produccion.items())
    return f"""✅ Fabricación registrada
🏭 {items}
🫙 Tarros descontados: -{total}
🧪 Alcohol descontado: -{total * 40}ml
✨ Perfumes sumados al stock"""


@tool
def registrar_compra_insumos(insumos_json: str) -> str:
    """Registra una compra de insumos y los suma al inventario actual."""
    try:
        compras = json.loads(insumos_json)
    except Exception:
        return "❌ Formato incorrecto."
    inv_actual = get_inventario()
    resumen = []
    for clave, cantidad in compras.items():
        anterior = inv_actual.get(clave, 0)
        nuevo    = anterior + float(cantidad)
        set_inventario(clave, nuevo)
        nombre = clave.replace("_", " ").title()
        resumen.append(f"  {nombre}: {anterior} → {nuevo} (+{cantidad})")
    return "✅ Compra registrada:\n" + "\n".join(resumen)


@tool
def reporte_utilidades() -> str:
    """Genera reporte financiero del mes: utilidades, ventas por distribuidor y margen porcentual."""
    util_mes     = float(get_config("utilidad_mes"))
    lineas       = []
    ingreso_total = 0
    for d_id, d_info in DISTRIBUIDORES.items():
        if d_id == "yo":
            continue
        v = float(get_config(f"ventas_{d_id}"))
        if v > 0:
            util_unit     = _util_por_perfume(d_info)
            util          = v * util_unit
            ingreso_bruto = v * d_info["precio"]
            margen        = (util_unit / d_info["precio"]) * 100
            ingreso_total += ingreso_bruto
            lineas.append(
                f"  {d_info['nombre']}: {int(v)} prf | bruto ${ingreso_bruto:,.0f} | util ${util:,.0f} ({margen:.0f}%)"
            )
    margen_total = (util_mes / ingreso_total * 100) if ingreso_total > 0 else 0
    r = f"""📊 REPORTE SUCCESSFUL AROMAS
💰 Utilidad acumulada mes: ${util_mes:,.0f}
📦 Ingreso bruto total:    ${ingreso_total:,.0f}
📈 Margen promedio:        {margen_total:.1f}%"""
    if lineas:
        r += "\n\nDetalle por distribuidor:\n" + "\n".join(lineas)
    return r


@tool
def mensaje_motivacional(distribuidor_id: str) -> str:
    """Genera un mensaje motivacional personalizado para el distribuidor. Sin números ni dinero."""
    dist = DISTRIBUIDORES.get(distribuidor_id.lower())
    if not dist:
        return "❌ Distribuidor no encontrado. Usa: steven, jairo, jeferson, yo"
    prompt = (
        f"Genera un mensaje motivacional poderoso para {dist['nombre']} de Successful Aromas. "
        "REGLAS ESTRICTAS: Sin mencionar números, dinero ni ventas. "
        "Solo sobre consciencia, disciplina, identidad y propósito. "
        "Máximo 5 líneas. Con emojis. Tono de mentor de vida, no de jefe de ventas."
    )
    try:
        from agent.llm import llm
        response = llm.invoke([HumanMessage(content=prompt)])
        return f"💌 Mensaje para {dist['nombre']}:\n\n{response.content}"
    except Exception:
        return (
            f"💌 Mensaje para {dist['nombre']}:\n\n"
            "🔥 La grandeza no se anuncia — se construye en silencio con disciplina diaria.\n"
            "⚡ Cada acción que das hoy es una promesa a la versión que quieres ser mañana.\n"
            "🌟 Successful Aromas no es solo un negocio, es la prueba de que tus sueños tienen valor real.\n"
            "💎 Sigue adelante. Los resultados son el eco de tu constancia.\n"
            "🚀 ¡Hoy es otro día para construir tu legado!"
        )
