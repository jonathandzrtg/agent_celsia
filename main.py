from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

import warnings
import os
from dotenv import load_dotenv

# --- LangChain Imports ---
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from langchain.tools import tool # Needed for the dynamically created RAG tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END # Required for agent graph if not using create_agent helper

# Import tools from external file
from tools_celsia import (
    get_telefono_celsia,
    get_social_media_celsia,
    get_pqr_celsia,
    get_direccion_celsia,
    get_pago_de_factura_celsia,
    generar_factura_simulada,
    verificar_estado_servicio,
    calcular_instalacion_solar,
    reportar_dano_servicio,
    consultar_estado_reporte
)

# LangGraph's create_agent is a bit high-level; we'll recreate the graph logic for more control
# Import specific components for building the agent graph manually
from langchain_core.agents import AgentFinish, AgentAction
from typing import TypedDict, Annotated, List
import operator


# Ignore warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Load environment variables
load_dotenv()

# --- FastAPI App Setup ---
app = FastAPI(
    title="Celsia Chatbot API",
    description="API for the Celsia AI Chatbot, integrated with LangGraph and Function Calling.",
    version="1.0.0"
)

# Global instances for agent and memory
AGENT_GRAPH = None
CHECKPOINTER = InMemorySaver()

# --- Agent State Definition ---
class AgentState(TypedDict):
    # The list of messages passed between the agent and the tools
    messages: Annotated[List[Any], operator.add]
    # The 'next' field indicates where to route the control flow
    next: str

# --- Agent Definition ---
def load_agent_and_rag_components(
    temperature: float = 0.5,
    top_k: int = 40,
    top_p: float = 0.9,
    retriever_k: int = 5
):
    """
    This function loads all components (VectorDB, LLM, RAG chain)
    and constructs the final Agent.
    """
    
    # --- 1. LLM Configuration ---
    llm = ChatOllama(
        model=os.getenv("OLLAMA_LLM_MODEL", "qwen3:4b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=temperature,
        top_k=top_k,
        top_p=top_p
    )

    # --- 2. Embeddings and Vectorstore (Retriever) ---
    embeddings = OllamaEmbeddings(
        model=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    
    vectorstore = Chroma(
        persist_directory="./chromadb_storage",
        embedding_function=embeddings,
        collection_name="rag_collection"
    )
    
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": retriever_k,
            "fetch_k": retriever_k * 4,
            "lambda_mult": 0.5
        }
    )
    
    # --- 3. RAG Chain Definition ---
    prompt_rag = PromptTemplate(
        template="""**[ROL Y MISIÓN MAESTRA: ASISTENTE OFICIAL DE DOCUMENTOS CELSIA]**
Eres el **Buscador Oficial de Documentos de CELSIA**. Tu función es la de un **Agente RAG (Retrieval-Augmented Generation) de Zero-Shot**.
Tu fuente de conocimiento es **ÚNICAMENTE** el **CONTEXTO** proporcionado. Tu misión es extraer y presentar la información más relevante para la **PREGUNTA** con un 100% de **fidelidad a la fuente**.

**[PROTOCOLO ESTRICTO DE RESPUESTA Y ANTI-ALUCINACIÓN]**

Tu proceso de respuesta es inflexible:

1.  **ANÁLISIS DE AUTORIDAD (CONTEXTO):** Lee el **CONTEXTO**. Este es tu único universo de datos.
2.  **IDENTIFICACIÓN Y VERIFICACIÓN:** Localiza la información que responde a la **PREGUNTA**.
    * *Definición Implícita:* Una respuesta implícita es una conclusión lógica e irrefutable que puede ser deducida **directamente** de dos o más hechos presentes en el CONTEXTO (no una inferencia o adivinanza).
3.  **FORMULACIÓN Y SÍNTESIS:** Genera una respuesta cortés, profesional, **directa y concisa**, utilizando el lenguaje y los términos exactos del CONTEXTO.

**[REGLAS INQUEBRANTABLES (GUARDRAILS DE SEGURIDAD)]**

1.  **CONDICIÓN DE ÉXITO:** **SI** la respuesta puede ser verificada explícita o lógicamente (implícitamente) con la información del CONTEXTO, procede con la respuesta.
2.  **CONDICIÓN DE FALLO/CERO INFORMACIÓN:** **SI** la respuesta no existe, la información es contradictoria, insuficiente, ambigua, o no se puede verificar con certeza, debes responder **ÚNICAMENTE** con esta frase, sin preámbulos ni explicaciones adicionales:
    > "Lamento no poder ofrecer una respuesta precisa basada en la información disponible. Por favor, consulta los canales oficiales de CELSIA o llama a la línea de servicio al cliente."
3.  **PROHIBICIONES ABSOLUTAS:**
    * **NUNCA** utilices conocimiento general, fechas, tarifas, procesos, o cualquier dato que no figure en el CONTEXTO.
    * **NUNCA** intentes rellenar huecos o especular.
    * **NUNCA** reformules la frase de *fallback* (Regla 2).

**[VERIFICACIÓN FINAL (Self-Check)]**
Antes de entregar la respuesta, realiza una auto-corrección: ¿Cada afirmación en la respuesta se deriva **directamente** del CONTEXTO? Si la respuesta es No, activa la Condición de Fallo (Regla 2).

Contexto:
{context}

Pregunta: {question}

Respuesta:""",
        input_variables=["context", "question"]
    )
    
    def formato_docs(docs):
        return "\n\n".join([doc.page_content for doc in docs])
    
    rag_chain = (
        {"context": retriever | formato_docs, "question": RunnablePassthrough()}
        | prompt_rag
        | llm
        | StrOutputParser()
    )

    # --- 4. RAG Chain as a Tool ---
    @tool
    def BuscadorDocumentosCelsia(pregunta: str) -> str:
        """
        Herramienta para buscar información en la base de datos de Celsia.
        Útil para preguntas generales sobre Celsia, servicios, tarifas, procesos, etc.
        """
        return rag_chain.invoke(pregunta)

    # --- 5. Agent Creation (using LangGraph for more control) ---
    
    # Combine all tools
    tools = [
        get_telefono_celsia,
        get_direccion_celsia,
        get_social_media_celsia,
        get_pqr_celsia,
        get_pago_de_factura_celsia,
        generar_factura_simulada,
        verificar_estado_servicio,
        calcular_instalacion_solar,
        reportar_dano_servicio,
        consultar_estado_reporte,
        BuscadorDocumentosCelsia # The RAG tool
    ]

    # Bind tools to the LLM for function calling
    llm_with_tools = llm.bind_tools(tools)

    # Define the nodes of the graph
    def call_model(state: AgentState):
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
        # We return a list with the new message, so it is appended to the existing messages
        return {"messages": [response]}

    def call_tool(state: AgentState):
        last_message = state["messages"][-1]
        tool_outputs = []
        
        print(f"DEBUG: In call_tool. last_message type: {type(last_message)}")
        print(f"DEBUG: In call_tool. last_message content: {last_message.content}")
        print(f"DEBUG: In call_tool. last_message tool_calls: {last_message.tool_calls}")

        for tool_call in last_message.tool_calls:
            print(f"DEBUG: In call_tool. Processing tool_call: {tool_call}, type: {type(tool_call)}")
            try:
                # Ensure tool_call is an object with .name and .args attributes
                # If it's a dict, we need to convert it
                if isinstance(tool_call, dict):
                    tool_name = tool_call.get('name')
                    tool_args = tool_call.get('args', {})
                else:
                    tool_name = tool_call.name
                    tool_args = tool_call.args

                selected_tool = next(t for t in tools if t.name == tool_name)
                output = selected_tool.invoke(tool_args)
                tool_outputs.append(AIMessage(content=str(output), name=tool_name))
            except Exception as e:
                error_message = f"Error al usar la herramienta '{tool_name if 'tool_name' in locals() else 'unknown_tool'}': {e}. Por favor, intenta de nuevo o reformula tu pregunta."
                print(f"ERROR during tool invocation: {error_message}")
                tool_outputs.append(AIMessage(content=error_message, name=tool_name if 'tool_name' in locals() else 'unknown'))
        return {"messages": tool_outputs}

    # Define the graph
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", call_model)
    workflow.add_node("action", call_tool)

    workflow.set_entry_point("agent")

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        # If the LLM makes a tool call, then we route to the "action" node
        if last_message.tool_calls:
            return "action"
        # Otherwise, it's a normal response, so we end the graph
        return END

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"action": "action", END: END}
    )
    workflow.add_edge("action", "agent") # After calling a tool, go back to the agent

    # Compile the graph
    agent_graph = workflow.compile()
    
    return agent_graph

# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    global AGENT_GRAPH
    try:
        # Load agent components with default parameters
        # In a production setting, these parameters might come from config files or env vars
        AGENT_GRAPH = load_agent_and_rag_components(
            temperature=float(os.getenv("LLM_TEMPERATURE", 0.5)),
            top_k=int(os.getenv("LLM_TOP_K", 40)),
            top_p=float(os.getenv("LLM_TOP_P", 0.9)),
            retriever_k=int(os.getenv("RETRIEVER_K", 5))
        )
        print("✅ Agent components loaded successfully.")
    except Exception as e:
        print(f"❌ Error loading agent components: {e}")
        # Depending on criticality, you might want to raise and prevent startup
        raise HTTPException(status_code=500, detail=f"Failed to load agent: {e}")

class ChatRequest(BaseModel):
    user_message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    
@app.get("/health")
async def health_check():
    if AGENT_GRAPH:
        return {"status": "ok", "message": "Agent loaded."}
    else:
        raise HTTPException(status_code=503, detail="Agent not loaded yet.")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not AGENT_GRAPH:
        raise HTTPException(status_code=503, detail="Agent not initialized.")

    config = {"configurable": {"thread_id": request.session_id}}
    
    try:
        # Invoke the agent
        # The input to the graph is a list of messages.
        # We pass only the HumanMessage for the current turn.
        # The checkpointer will handle retrieving previous messages.
        response_dict = AGENT_GRAPH.invoke(
            {"messages": [HumanMessage(content=request.user_message)]},
            config=config
        )
        
        # Extract the final response from the agent
        final_response_str = "No response from agent."
        if "messages" in response_dict and response_dict["messages"]:
            # Iterate through messages in reverse to find the last AIMessage with actual content
            for msg in reversed(response_dict["messages"]):
                if isinstance(msg, AIMessage) and msg.content:
                    final_response_str = msg.content
                    break
            if final_response_str == "No response from agent.":
                # Fallback if no AIMessage with content found (e.g., only tool calls or empty responses)
                final_response_str = "Lo siento, no pude generar una respuesta clara. Por favor, intenta de nuevo."

        return ChatResponse(response=final_response_str)
    except Exception as e:
        print(f"Error during agent invocation for session {request.session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during chat processing.")


