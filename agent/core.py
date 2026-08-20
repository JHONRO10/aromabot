from typing import TypedDict, Annotated, Literal

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage

from agent.llm import llm
from agent.prompts import SYSTEM_PROMPT
from agent.tools import (
    consultar_inventario, calcular_valor_inventario, registrar_venta,
    registrar_fabricacion, registrar_compra_insumos, reporte_utilidades, mensaje_motivacional,
)

tools_list = [
    consultar_inventario, calcular_valor_inventario, registrar_venta,
    registrar_fabricacion, registrar_compra_insumos, reporte_utilidades, mensaje_motivacional,
]

_llm_con_tools = llm.bind_tools(tools_list)
_tools_map     = {t.name: t for t in tools_list}


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def _nodo_agente(state: AgentState):
    msgs = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    return {"messages": [_llm_con_tools.invoke(msgs)]}


def _nodo_tools(state: AgentState):
    ultimo     = state["messages"][-1]
    resultados = []
    for tc in ultimo.tool_calls:
        try:
            resultado = _tools_map[tc["name"]].invoke(tc["args"])
        except Exception as e:
            resultado = f"❌ Error ejecutando {tc['name']}: {str(e)}"
        resultados.append(ToolMessage(content=str(resultado), tool_call_id=tc["id"]))
    return {"messages": resultados}


def _debe_continuar(state: AgentState) -> Literal["tools", "fin"]:
    ultimo = state["messages"][-1]
    if hasattr(ultimo, "tool_calls") and ultimo.tool_calls:
        return "tools"
    return "fin"


_grafo = StateGraph(AgentState)
_grafo.add_node("agente", _nodo_agente)
_grafo.add_node("tools",  _nodo_tools)
_grafo.set_entry_point("agente")
_grafo.add_conditional_edges("agente", _debe_continuar, {"tools": "tools", "fin": END})
_grafo.add_edge("tools", "agente")
bot = _grafo.compile()


def invoke_agent(mensaje: str) -> str:
    output = bot.invoke({"messages": [HumanMessage(content=mensaje)]})
    return output["messages"][-1].content
