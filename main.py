from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

import warnings
import os
from dotenv import load_dotenv

# --- LangChain Imports ---
# Imports moved to src/agent/core.py
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_chroma import Chroma
# from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage # Still needed for API interaction

# Tools are imported within src/agent/core.py, but need to be accessible for core.py
# If tools are not directly used in main.py, this import can be removed, or simplified.
# For now, let's keep it as it simplifies moving the block.
# from src.tools.celsia_tools import (
#     get_telefono_celsia, get_social_media_celsia, get_pqr_celsia,
#     get_direccion_celsia, get_pago_de_factura_celsia, generar_factura_simulada,
#     verificar_estado_servicio, calcular_instalacion_solar, reportar_dano_servicio,
#     consultar_estado_reporte
# )

# Import agent components from src.agent.core
from src.agent.core import load_agent_and_rag_components, CHECKPOINTER
# Import AgentState from the state module
from src.agent.state import AgentState # Still needed for type hinting if AgentState is used in FastAPI models


# Remove redundant imports as they are now in src/agent/state.py or src/agent/core.py
# from langchain_core.agents import AgentFinish, AgentAction
# from typing import TypedDict, Annotated, List
# import operator


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

# Global instance for agent
AGENT_GRAPH = None

# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    global AGENT_GRAPH
    if AGENT_GRAPH is None: # Add this check
        try:
            # Load agent components with default parameters
            AGENT_GRAPH = load_agent_and_rag_components(
                temperature=float(os.getenv("LLM_TEMPERATURE", 0.5)),
                top_k=int(os.getenv("LLM_TOP_K", 40)),
                top_p=float(os.getenv("LLM_TOP_P", 0.9)),
                retriever_k=int(os.getenv("RETRIEVER_K", 5))
            )
            print("✅ Agent components loaded successfully.")
            if os.getenv("LANGCHAIN_TRACING_V2") == "true":
                print("✅ LangSmith tracing is enabled for project:", os.getenv("LANGCHAIN_PROJECT", "default"))
            else:
                print("🔕 LangSmith tracing is not enabled (set LANGCHAIN_TRACING_V2=true in .env).")
        except Exception as e:
            print(f"❌ Error loading agent components: {e}")
            print(f"DEBUG: Exception details: {repr(e)}") # Added debug print
            raise HTTPException(status_code=500, detail=f"Failed to load agent: {repr(e)}")
    else: # If AGENT_GRAPH is already set (e.g. by a test fixture)
        print("✅ Agent components already loaded (skipped startup_event loading).")

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
        response_dict = AGENT_GRAPH.invoke(
            {"messages": [HumanMessage(content=request.user_message)]},
            config=config
        )
        
        # Extract the final response from the agent
        final_response_str = "No response from agent."
        if "messages" in response_dict and response_dict["messages"]:
            for msg in reversed(response_dict["messages"]):
                if isinstance(msg, AIMessage) and msg.content:
                    final_response_str = msg.content
                    break
            if final_response_str == "No response from agent.":
                final_response_str = "Lo siento, no pude generar una respuesta clara. Por favor, intenta de nuevo."

        return ChatResponse(response=final_response_str)
    except Exception as e:
        print(f"Error during agent invocation for session {request.session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during chat processing.")
