import os
import warnings
from dotenv import load_dotenv

# LangChain / LangGraph Imports
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END
from langchain_core.agents import AgentFinish, AgentAction # Keep these if needed by LangGraph's internal workings for error handling/etc.
from typing import TypedDict, Annotated, List, Any
import operator

# Import tools from the new location
from src.tools.celsia_tools import (
    get_telefono_celsia,
    get_direccion_celsia,
    get_social_media_celsia,
    get_pqr_celsia,
    get_pago_de_factura_celsia,
    generar_factura_simulada,
    verificar_estado_servicio,
    calcular_instalacion_solar,
    reportar_dano_servicio,
    consultar_estado_reporte
)

# Import AgentState from the state module
from src.agent.state import AgentState

# Ignore warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Load environment variables (ensure they are loaded if core.py is run independently, though main.py should load them)
load_dotenv()

# Global instances for agent and memory (CHECKPOINTER managed here)
CHECKPOINTER = InMemorySaver()

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
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
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