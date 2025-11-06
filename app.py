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

# Importar tools desde archivo externo
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

# Ignorar advertencias (opcional, para limpiar la consola)
warnings.filterwarnings("ignore", category=UserWarning)

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

# Parámetros del LLM (configurables desde sidebar)
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.5
if "top_k" not in st.session_state:
    st.session_state.top_k = 40
if "top_p" not in st.session_state:
    st.session_state.top_p = 0.9

# Parámetros del Retriever
if "retriever_k" not in st.session_state:
    st.session_state.retriever_k = 5


# --- CONFIGURACIÓN DE LA PÁGINA de Streamlit ---
st.set_page_config(
    page_title="Celsia Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titulo
st.markdown("<h1 style='text_align: center;'>🤖 Agente Celsia Qwen3:4B</h1>", unsafe_allow_html=True)
st.write("En que puedo ayudarte hoy?")


# --- FUNCIÓN PRINCIPAL DE CARGA (Cacheada) ---
# Ya no usamos cache porque queremos que los parámetros sean dinámicos
def cargar_agente_y_rag(temperature=0.5, top_k=40, top_p=0.9, retriever_k=5):
    """
    Esta función carga todos los componentes (VectorDB, LLM, RAG chain)
    y construye el Agente final con parámetros configurables.
    """
    
    with st.spinner("⏳ Iniciando sistemas... (esto puede tardar un momento)"):
        
        # --- 1. Configuración del LLM ---
        # Usamos ChatOllama para que el agente pueda tener conversaciones
        llm = ChatOllama(
            model="qwen3:4b",
            base_url="http://localhost:11434",
            temperature=temperature,
            top_k=top_k,
            top_p=top_p
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
        # Usamos MMR (Maximum Marginal Relevance) para obtener mayor diversidad
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": retriever_k,  # Documentos finales a retornar
                "fetch_k": retriever_k * 4,  # Documentos iniciales a buscar (más pool para diversidad)
                "lambda_mult": 0.5  # Balance entre relevancia (1.0) y diversidad (0.0)
            }
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
        tools = [
            # Tools informativas
            get_telefono_celsia,
            get_direccion_celsia,
            get_social_media_celsia,
            get_pqr_celsia,
            get_pago_de_factura_celsia,
            # Tools funcionales
            generar_factura_simulada,
            verificar_estado_servicio,
            calcular_instalacion_solar,
            reportar_dano_servicio,
            consultar_estado_reporte,
            # Tool RAG
            BuscadorDocumentosCelsia
        ]
        
        # Prompt del sistema: Las instrucciones maestras para el Agente
        system_prompt_agent = """Eres un asistente virtual de Celsia.
Tu trabajo es ayudar a los usuarios con sus preguntas. Responde siempre en español.

**IMPORTANTE - Orden de prioridad para usar herramientas:**

1. **PRIMERO**: Analiza si la pregunta solicita información específica que puedes obtener con las herramientas directas:
   - `get_telefono_celsia`: Teléfono de Celsia
   - `get_direccion_celsia`: Direcciones de oficinas
   - `get_social_media_celsia`: Redes sociales
   - `get_pqr_celsia`: Sistema de PQR
   - `get_pago_de_factura_celsia`: Cómo pagar facturas
   - `generar_factura_simulada`: Si piden ver una factura con número de cuenta y mes
   - `verificar_estado_servicio`: Si preguntan por interrupciones en una ciudad
   - `calcular_instalacion_solar`: Si quieren cotizar paneles solares
   - `reportar_dano_servicio`: Si quieren reportar un daño o falla
   - `consultar_estado_reporte`: Si tienen un ticket y quieren consultarlo

2. **SEGUNDO**: Si la pregunta NO se puede responder con las tools anteriores, usa:
   - `BuscadorDocumentosCelsia`: Para preguntas generales sobre Celsia, servicios, tarifas, procesos, etc.

**Estrategia de respuesta:**
- Si usaste `get_telefono_celsia` o `get_direccion_celsia`, responde ÚNICAMENTE con esa información, no uses el buscador.
- Si usaste `BuscadorDocumentosCelsia`, basa tu respuesta ÚNICAMENTE en lo que la herramienta te devolvió.
- Si el BuscadorDocumentosCelsia no tiene información suficiente, indícale al usuario que contacte los canales oficiales.

Sé conciso y profesional."""
        
        # Creamos el Agente
        agent_graph = create_agent(
            llm, # El LLM que tomará las decisiones
            tools=tools, # La lista de herramientas que puede usar
            system_prompt=system_prompt_agent,
            checkpointer=st.session_state.checkpointer,
        )
        
        # Devolvemos el agente (ya no la 'rag_chain') y el retriever (para depurar)
        return agent_graph, retriever, vectorstore

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración")
    
    st.subheader("🎛️ Parámetros del LLM")
    
    # Slider de temperatura
    temperature = st.slider(
        "Temperatura",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.temperature,
        step=0.05,
        help="Controla la creatividad del modelo. Valores bajos (0.1-0.3) = más determinista. Valores altos (0.7-1.0) = más creativo."
    )
    st.session_state.temperature = temperature
    
    # Slider de top_k
    top_k = st.slider(
        "Top K",
        min_value=1,
        max_value=100,
        value=st.session_state.top_k,
        step=1,
        help="Limita las opciones a las K palabras más probables en cada paso."
    )
    st.session_state.top_k = top_k
    
    # Slider de top_p
    top_p = st.slider(
        "Top P (Nucleus Sampling)",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.top_p,
        step=0.05,
        help="Considera solo las palabras cuya probabilidad acumulada sea <= P."
    )
    st.session_state.top_p = top_p
    
    st.divider()
    st.subheader("🔍 Parámetros del Retriever")
    
    # Slider para k del retriever
    retriever_k = st.slider(
        "Cantidad de documentos (k)",
        min_value=1,
        max_value=10,
        value=st.session_state.retriever_k,
        step=1,
        help="Número de chunks de documentos a recuperar de la base de datos."
    )
    st.session_state.retriever_k = retriever_k

# --- Carga Inicial ---
# Llamamos a la función con los parámetros configurables
try:
    agent_graph, retriever, vectorstore = cargar_agente_y_rag(
        temperature=st.session_state.temperature,
        top_k=st.session_state.top_k,
        top_p=st.session_state.top_p,
        retriever_k=st.session_state.retriever_k
    )
    st.success("✅ Agente y base de datos cargados correctamente")
except Exception as e:
    st.error(f"Error al cargar el agente: {e}")
    st.stop() # Detiene la ejecución si hay un error crítico


# --- SIDEBAR (continuación) ---
with st.sidebar:
    st.divider()
    st.subheader("📊 Información del Sistema")
    try:
        st.info(f"📚 Documentos en la BD: {vectorstore._collection.count()}")
    except Exception as e:
        st.warning("No se pudo contar los documentos de ChromaDB.")
    
    st.write(f"""    
    - **Modelo LLM**: qwen3:4b
    - **Embeddings**: nomic-embed-text
    - **Base de datos**: ChromaDB
    - **Framework**: LangGraph (Agente)
    - **Búsqueda**: MMR (Max Marginal Relevance)
    """)
    
    st.divider()
    
    if st.button("🗑️ Limpiar historial"):
        st.session_state.messages = []
        # Limpiamos también la memoria del agente
        st.session_state.checkpointer = InMemorySaver()
        st.rerun() # Recarga la página

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
            
            # 5.1 Mostrar parámetros activos del LLM en un pequeño badge
            st.caption(f"🎛️ Parámetros: Temp={st.session_state.temperature} | Top-K={st.session_state.top_k} | Top-P={st.session_state.top_p} | Docs={st.session_state.retriever_k}")
            
            # 6. Guardar la respuesta en el historial de Streamlit
            st.session_state.messages.append({
                "role": "assistant",
                "content": respuesta_final_str
            })
            
            # 7. Mostrar información de debugging mejorada
            with st.expander("🔍 Debugging: Información del Agente"):
                # Mostrar qué herramientas usó el agente
                st.subheader("🛠️ Herramientas utilizadas")
                tool_calls = []
                for msg in respuesta_dict.get("messages", []):
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            tool_calls.append({
                                "tool": tool_call.get("name", "desconocido"),
                                "args": tool_call.get("args", {})
                            })
                
                if tool_calls:
                    for i, tc in enumerate(tool_calls, 1):
                        st.write(f"**{i}. {tc['tool']}**")
                        if tc['args']:
                            st.json(tc['args'])
                else:
                    st.write("No se usaron herramientas explícitas.")
                
                st.divider()
                
                # Mostrar documentos recuperados con scores de similaridad
                st.subheader("📚 Documentos recuperados del RAG")
                try:
                    # Usamos similarity_search_with_score para obtener los scores
                    docs_with_scores = vectorstore.similarity_search_with_score(pregunta, k=st.session_state.retriever_k)
                    
                    if docs_with_scores:
                        st.write(f"Se recuperaron {len(docs_with_scores)} documentos:")
                        for i, (doc, score) in enumerate(docs_with_scores, 1):
                            source = doc.metadata.get('source', 'Fuente desconocida')
                            # Score más bajo = más similar (distancia)
                            st.write(f"**[{i}] {source}** - Score: {score:.4f}")
                            st.info(doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content)
                    else:
                        st.write("No se recuperaron documentos para esta consulta.")
                except Exception as e:
                    st.error(f"Error al recuperar documentos con scores: {e}")
                    # Fallback a método sin scores
                    docs = retriever.invoke(pregunta)
                    if docs:
                        for i, doc in enumerate(docs, 1):
                            source = doc.metadata.get('source', 'Fuente desconocida')
                            st.write(f"**[{i}] {source}**")
                            st.info(doc.page_content)
                    else:
                        st.write("No se recuperaron documentos.")
