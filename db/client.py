import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_db: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def get_inventario() -> dict:
    try:
        res = _db.table("aroma_inventario").select("*").execute()
        return {row["clave"]: row["valor"] for row in res.data}
    except Exception as e:
        return {"error": str(e)}


def set_inventario(clave: str, valor: float):
    _db.table("aroma_inventario").upsert({"clave": clave, "valor": valor}).execute()


def get_config(clave: str) -> str:
    try:
        res = _db.table("aroma_config").select("valor").eq("clave", clave).execute()
        return res.data[0]["valor"] if res.data else "0"
    except Exception:
        return "0"


def set_config(clave: str, valor: str):
    _db.table("aroma_config").upsert({"clave": clave, "valor": valor}).execute()


def registrar_pedido(distribuidor: str, productos: dict, total: int, utilidad: float):
    _db.table("aroma_pedidos").insert({
        "distribuidor": distribuidor,
        "productos":    productos,
        "total_perfumes": total,
        "mi_utilidad":  utilidad,
    }).execute()
