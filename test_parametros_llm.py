"""
Script para Probar el Efecto de los Parámetros del LLM
Verifica que temperatura, top_k y top_p realmente afecten las respuestas
"""

from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

print("=" * 80)
print("🧪 PRUEBA DE PARÁMETROS DEL LLM")
print("=" * 80)

# Configurar embeddings y retriever
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

vectorstore = Chroma(
    persist_directory="./chromadb_storage",
    embedding_function=embeddings,
    collection_name="rag_collection"
)

retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 5, "fetch_k": 20, "lambda_mult": 0.5}
)

# Prompt simple
prompt = PromptTemplate(
    template="""Basándote en el siguiente contexto, responde la pregunta de forma clara y concisa.

Contexto: {context}

Pregunta: {question}

Respuesta:""",
    input_variables=["context", "question"]
)

def formato_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])

# Pregunta de prueba
pregunta = "¿Qué es Celsia y qué servicios ofrece?"

print(f"\n❓ Pregunta de prueba: {pregunta}\n")

# ===== TEST 1: TEMPERATURA =====
print("=" * 80)
print("🌡️ TEST 1: EFECTO DE LA TEMPERATURA")
print("=" * 80)
print("Temperatura baja (0.1) = Respuestas más deterministas y repetitivas")
print("Temperatura alta (0.9) = Respuestas más creativas y variadas")

temperaturas = [0.1, 0.5, 0.9]

for temp in temperaturas:
    print(f"\n{'─' * 80}")
    print(f"🔥 Temperatura: {temp}")
    print(f"{'─' * 80}")
    
    llm = ChatOllama(
        model="qwen3:4b",
        base_url="http://localhost:11434",
        temperature=temp,
        top_k=40,
        top_p=0.9
    )
    
    rag_chain = (
        {"context": retriever | formato_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # Hacer 3 invocaciones para ver variabilidad
    print("\nRespuestas (3 intentos):")
    for i in range(3):
        respuesta = rag_chain.invoke(pregunta)
        print(f"\n  [{i+1}] {respuesta[:150]}...")

# ===== TEST 2: TOP-K =====
print("\n" + "=" * 80)
print("🔢 TEST 2: EFECTO DE TOP-K")
print("=" * 80)
print("Top-k bajo (5) = Solo considera las 5 palabras más probables")
print("Top-k alto (80) = Considera más opciones, más variedad")

top_ks = [5, 40, 80]

for top_k in top_ks:
    print(f"\n{'─' * 80}")
    print(f"🎯 Top-K: {top_k}")
    print(f"{'─' * 80}")
    
    llm = ChatOllama(
        model="qwen3:4b",
        base_url="http://localhost:11434",
        temperature=0.7,  # Temperatura media para ver efecto
        top_k=top_k,
        top_p=0.9
    )
    
    rag_chain = (
        {"context": retriever | formato_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print("\nRespuestas (2 intentos):")
    for i in range(2):
        respuesta = rag_chain.invoke(pregunta)
        print(f"\n  [{i+1}] {respuesta[:150]}...")

# ===== TEST 3: TOP-P =====
print("\n" + "=" * 80)
print("📊 TEST 3: EFECTO DE TOP-P (Nucleus Sampling)")
print("=" * 80)
print("Top-p bajo (0.3) = Solo palabras con alta probabilidad acumulada")
print("Top-p alto (0.95) = Permite más diversidad en selección")

top_ps = [0.3, 0.7, 0.95]

for top_p in top_ps:
    print(f"\n{'─' * 80}")
    print(f"🎲 Top-P: {top_p}")
    print(f"{'─' * 80}")
    
    llm = ChatOllama(
        model="qwen3:4b",
        base_url="http://localhost:11434",
        temperature=0.7,
        top_k=40,
        top_p=top_p
    )
    
    rag_chain = (
        {"context": retriever | formato_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print("\nRespuestas (2 intentos):")
    for i in range(2):
        respuesta = rag_chain.invoke(pregunta)
        print(f"\n  [{i+1}] {respuesta[:150]}...")

# ===== RESUMEN =====
print("\n" + "=" * 80)
print("📋 RESUMEN: CÓMO INTERPRETAR LOS RESULTADOS")
print("=" * 80)

print("""
✅ Los parámetros ESTÁN funcionando si observas:

1. TEMPERATURA:
   - Temp baja (0.1): Las 3 respuestas son casi idénticas
   - Temp alta (0.9): Las 3 respuestas varían considerablemente

2. TOP-K:
   - Top-k bajo (5): Vocabulario más limitado, frases más predecibles
   - Top-k alto (80): Vocabulario más amplio, mayor variedad léxica

3. TOP-P:
   - Top-p bajo (0.3): Respuestas más conservadoras
   - Top-p alto (0.95): Respuestas más exploratorias

❌ Los parámetros NO están funcionando si:
   - Todas las respuestas son idénticas sin importar los valores
   - No hay diferencia entre temperatura 0.1 y 0.9
   - Las variaciones son aleatorias y no siguen el patrón esperado

💡 NOTA: Con temperatura=0.0, el modelo es completamente determinista,
   por lo que top-k y top-p tienen poco efecto.
""")

print("=" * 80)
print("✅ PRUEBA COMPLETADA")
print("=" * 80)
