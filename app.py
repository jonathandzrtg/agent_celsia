"""
Interfaz de Agente RAG con Streamlit y LangGraph
El Agente tiene acceso a una herramienta de búsqueda RAG (ChromaDB)
y una herramienta para obtener un número de teléfono.
"""

import streamlit as st
import warnings

# --- Importaciones Clave de LangChain ---
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama # ChatOllama es necesario para Agentes
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from langchain.tools import tool # El decorador para crear herramientas
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver 

# Ignorar advertencias (opcional, para limpiar la consola)
warnings.filterwarnings("ignore", category=UserWarning)


# --- HERRAMIENTA 1: Función de Python Simple ---
# Usamos el decorador @tool para que el agente pueda "ver" esta función
@tool
def get_telefono_celsia():
    """Funcion para obtener el telefono de celsia. 
    Usar SÓLO si el usuario pide explícitamente el número de teléfono."""
    return "3102226655"

@tool
def get_direccion_celsia():
    """Funcion para obtener la direccion de celsia. 
    Usar SÓLO si el usuario pide explícitamente la dirección."""
    return "Calle 1 Casa 1 avenida siempre viva"


# --- Configuración de Estado de Streamlit (Session State) ---

# Checkpointer: Guarda el estado de la conversación (memoria) del agente
if "checkpointer" not in st.session_state:
    st.session_state.checkpointer = InMemorySaver()

# Thread ID: Un ID fijo para que la conversación sea continua
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "1" 

# Historial de mensajes para mostrar en la UI de Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = []


# --- CONFIGURACIÓN DE LA PÁGINA de Streamlit ---
st.set_page_config(
    page_title="Celsia Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titulo
st.markdown("<h1 style='text_align: center;'>🤖 Agente Celsia llama 3.2 3B</h1>", unsafe_allow_html=True)
st.write("En que puedo ayudarte hoy?")


# --- FUNCIÓN PRINCIPAL DE CARGA (Cacheada) ---
# @st.cache_resource asegura que esto solo se ejecute una vez
@st.cache_resource
def cargar_agente_y_rag():
    """
    Esta función carga todos los componentes (VectorDB, LLM, RAG chain)
    y construye el Agente final.
    """
    
    with st.spinner("⏳ Iniciando sistemas... (esto puede tardar un momento)"):
        
        # --- 1. Configuración del LLM ---
        # Usamos ChatOllama para que el agente pueda tener conversaciones
        llm = ChatOllama(
            model="qwen3:4b",
            base_url="http://localhost:11434",
            temperature=0.3 # Temperatura baja para que el agente sea más predecible
        )

        # --- 2. Configuración de Embeddings y Vectorstore (Retriever) ---
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://localhost:11434"
        )
        
        vectorstore = Chroma(
            persist_directory="./chromadb_storage",
            embedding_function=embeddings,
            collection_name="rag_collection"
        )
        
        # El 'retriever' es la parte que busca en la base de datos
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3} # Traer los 3 fragmentos más relevantes
        )
        
        # --- 3. Definición de la Cadena RAG ---
        # Este es el "cerebro" de nuestra herramienta de búsqueda.
        
        prompt_rag = PromptTemplate(
            template="""**[INSTRUCCIONES CLAVE ZERO-SHOT Y LIMITACIÓN DE FUENTE]**
Tu ÚNICA tarea es responder a la **PREGUNTA** del usuario, utilizando EXCLUSIVAMENTE la información que se encuentra en el **CONTEXTO** proporcionado a continuación.

**REGLAS ESTRICTAS para evitar alucinaciones:**
1.  **SI** la respuesta a la PREGUNTA se encuentra explícita o implícitamente en el **CONTEXTO**, genera una respuesta completa y profesional.
2.  **SI** no puedes encontrar la respuesta en el **CONTEXTO**, o si la información es insuficiente, debes responder **ÚNICAMENTE** con la siguiente frase predefinida: "Lamento no poder ofrecer una respuesta precisa basada en la información disponible. Por favor, consulta los canales oficiales de CELSIA o llama a la línea de servicio al cliente."
3.  **NUNCA** utilices tu conocimiento general o información que no esté en el **CONTEXTO**. **NUNCA** inventes tarifas, fechas o procesos.
        
Contexto:
{context}

Pregunta: {question}

Respuesta:""",
            input_variables=["context", "question"]
        )
        
        def formato_docs(docs):
            return "\n\n".join([doc.page_content for doc in docs])
        
        # Definimos la cadena RAG completa
        rag_chain = (
            {"context": retriever | formato_docs, "question": RunnablePassthrough()}
            | prompt_rag
            | llm # El mismo LLM puede usarse para la cadena RAG
            | StrOutputParser() # Nos aseguramos que la salida sea un string
        )

        # --- 4. HERRAMIENTA 2: La Cadena RAG como Herramienta ---
        # Aquí convertimos nuestra 'rag_chain' en una herramienta que el agente puede usar
        @tool
        def BuscadorDocumentosCelsia(pregunta: str) -> str:
            """
            Herramienta para buscar información en la base de datos de Celsia.
            """
            return rag_chain.invoke(pregunta)

        # --- 5. Creación del Agente ---
        
        # Lista de herramientas que el agente puede elegir
        tools = [get_direccion_celsia, get_telefono_celsia, BuscadorDocumentosCelsia]
        
        # Prompt del sistema: Las instrucciones maestras para el Agente
        system_prompt_agent = """Eres un asistente virtual de Celsia.
Tu trabajo es ayudar a los usuarios con sus preguntas. Responde siempre en español.
Tienes dos herramientas a tu disposición:

1.  `get_telefono_celsia`: Úsala SÓLO si el usuario pide el número de teléfono.
2.  `get_direccion_celsia`: Úsala SÓLO si el usuario pide la dirección.
3.  `BuscadorDocumentosCelsia`: Úsala para responder CUALQUIER OTRA pregunta sobre Celsia, ya que busca en la base de datos oficial.

Primero, analiza la pregunta del usuario. Luego, elige la herramienta correcta para responder."""
        
        # Creamos el Agente
        agent_graph = create_agent(
            llm, # El LLM que tomará las decisiones
            tools=tools, # La lista de herramientas que puede usar
            system_prompt=system_prompt_agent,
            checkpointer=st.session_state.checkpointer,
        )
        
        # Devolvemos el agente (ya no la 'rag_chain') y el retriever (para depurar)
        return agent_graph, retriever, vectorstore

# --- Carga Inicial ---
# Llamamos a la función. Streamlit la cacheará.
try:
    agent_graph, retriever, vectorstore = cargar_agente_y_rag()
    st.success("✅ Agente y base de datos cargados correctamente")
except Exception as e:
    st.error(f"Error al cargar el agente: {e}")
    st.stop() # Detiene la ejecución si hay un error crítico


# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración")
    try:
        st.info(f"📊 Documentos en la BD: {vectorstore._collection.count()}")
    except Exception as e:
        st.warning("No se pudo contar los documentos de ChromaDB.")
    
    if st.button("🗑️ Limpiar historial"):
        st.session_state.messages = []
        # Limpiamos también la memoria del agente
        st.session_state.checkpointer = InMemorySaver()
        st.rerun() # Recarga la página
    
    st.divider()
    st.subheader("ℹ️ Información")
    st.write("""
    - **Modelo LLM**: Llama 3.2 3B
    - **Embeddings**: nomic-embed-text
    - **Base de datos**: ChromaDB
    - **Framework**: LangGraph (Agente)
    """)

# --- Lógica del Chat ---

# Mostrar historial de mensajes (de st.session_state)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada del usuario
pregunta = st.chat_input("Escribe tu pregunta...")

if pregunta:
    # 1. Mostrar el mensaje del usuario en la UI
    st.session_state.messages.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)
    
    # 2. Generar respuesta del Agente
    with st.chat_message("assistant"):
        with st.spinner("⏳ Pensando..."):
            
            # Configuración para el hilo de memoria de LangGraph
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            
            # El input para el agente es un diccionario con la lista de mensajes
            input_data = {"messages": [HumanMessage(content=pregunta)]}
            
            # 3. Invocamos el Agente
            # 'respuesta_dict' es el objeto de estado final de LangGraph
            respuesta_dict = agent_graph.invoke(input_data, config=config)
            
            # 4. Extraemos la respuesta final del agente
            # La respuesta útil está en el último mensaje de la lista 'messages'
            respuesta_final_str = ""
            if "messages" in respuesta_dict and respuesta_dict["messages"]:
                last_message = respuesta_dict["messages"][-1]
                if isinstance(last_message, AIMessage):
                    respuesta_final_str = last_message.content
                else:
                    respuesta_final_str = "Error: El agente no produjo una respuesta final."
            else:
                respuesta_final_str = "Error: El agente no devolvió ningún mensaje."
            
            # 5. Mostrar la respuesta en la UI
            st.markdown(respuesta_final_str)
            
            # 6. Guardar la respuesta en el historial de Streamlit
            st.session_state.messages.append({
                "role": "assistant",
                "content": respuesta_final_str
            })
            
            # 7. (Opcional) Mostrar documentos para depuración
            with st.expander("📚 Documentos recuperados (Solo para referencia)"):
                # Mostramos lo que el retriever habría encontrado
                docs = retriever.invoke(pregunta)
                if docs:
                    for i, doc in enumerate(docs, 1):
                        source = doc.metadata.get('source', 'Fuente desconocida')
                        st.write(f"**[{i}] {source}**")
                        st.info(doc.page_content)
                else:
                    st.write("No se recuperaron documentos para esta consulta.")
