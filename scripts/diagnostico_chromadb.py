"""
Script de Diagnóstico de ChromaDB
Analiza la diversidad de los chunks y los embeddings
"""

import pandas as pd
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from collections import Counter
import numpy as np

# Configuración
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

vectorstore = Chroma(
    persist_directory="./chromadb_storage",
    embedding_function=embeddings,
    collection_name="rag_collection"
)

print("=" * 80)
print("DIAGNÓSTICO DE LA BASE DE DATOS VECTORIAL")
print("=" * 80)

# 1. Información básica
total_docs = vectorstore._collection.count()
print(f"\n📊 Total de documentos: {total_docs}")

# 2. Probar diferentes consultas
preguntas_prueba = [
    "¿Qué es Celsia?",
    "¿Cómo funciona la facturación?",
    "¿Qué servicios ofrece Celsia?",
    "¿Cuáles son las tarifas de energía?",
    "¿Qué es la energía solar?",
    "¿Cómo puedo pagar mi factura?",
    "¿Dónde está ubicada Celsia?",
    "¿Qué proyectos tiene Celsia?",
]

print("\n" + "=" * 80)
print("🔍 ANÁLISIS DE RECUPERACIÓN DE DOCUMENTOS")
print("=" * 80)

# Diccionario para contar cuántas veces aparece cada chunk
chunk_frequency = Counter()

for pregunta in preguntas_prueba:
    print(f"\n❓ Pregunta: {pregunta}")
    
    # Buscar con scores
    docs_with_scores = vectorstore.similarity_search_with_score(pregunta, k=5)
    
    print("   Top 3 documentos:")
    for i, (doc, score) in enumerate(docs_with_scores[:3], 1):
        source = doc.metadata.get('source', 'unknown')
        chunk_frequency[source] += 1
        content_preview = doc.page_content[:100].replace('\n', ' ')
        print(f"   [{i}] {source} - Score: {score:.4f}")
        print(f"       '{content_preview}...'")

print("\n" + "=" * 80)
print("📈 CHUNKS MÁS FRECUENTEMENTE RECUPERADOS")
print("=" * 80)

print(f"\nDe {len(chunk_frequency)} chunks únicos recuperados:")
for chunk, count in chunk_frequency.most_common(10):
    print(f"  {chunk}: {count} veces")

# 3. Análisis de diversidad de embeddings
print("\n" + "=" * 80)
print("🧬 ANÁLISIS DE DIVERSIDAD DE EMBEDDINGS")
print("=" * 80)

# Obtener algunos embeddings de muestra
sample_queries = preguntas_prueba[:5]
embeddings_list = []

for query in sample_queries:
    emb = embeddings.embed_query(query)
    embeddings_list.append(emb)

# Calcular similitud coseno entre pares
from numpy.linalg import norm

def cosine_similarity(a, b):
    return np.dot(a, b) / (norm(a) * norm(b))

print("\nSimilitud entre embeddings de diferentes preguntas:")
for i in range(len(embeddings_list)):
    for j in range(i + 1, len(embeddings_list)):
        sim = cosine_similarity(embeddings_list[i], embeddings_list[j])
        print(f"  '{sample_queries[i][:40]}...' vs")
        print(f"  '{sample_queries[j][:40]}...'")
        print(f"  → Similitud: {sim:.4f}\n")

# 4. Verificar si hay chunks duplicados o muy similares
print("=" * 80)
print("🔎 VERIFICANDO CHUNKS DUPLICADOS")
print("=" * 80)

# Cargar los CSVs originales
try:
    df1 = pd.read_csv("./data/chunks/celsia_processed_20251015_223656_chunks.csv")
    df2 = pd.read_csv("./data/chunks/post_celsia_chunks.csv")
    
    df1 = df1[['Contenido_Completo']].rename(columns={'Contenido_Completo': 'chunk'})
    df2 = df2[['chunk']]
    df = pd.concat([df1, df2])
    
    # Verificar duplicados exactos
    duplicados_exactos = df.duplicated(subset=['chunk']).sum()
    print(f"\n📋 Chunks duplicados exactos: {duplicados_exactos}")
    
    # Verificar chunks muy cortos (posible problema)
    chunks_cortos = df[df['chunk'].str.len() < 50]
    print(f"📋 Chunks muy cortos (<50 chars): {len(chunks_cortos)}")
    
    if len(chunks_cortos) > 0:
        print("\nEjemplos de chunks cortos:")
        for idx, row in chunks_cortos.head(5).iterrows():
            print(f"  - '{row['chunk']}'")
    
    # Estadísticas de longitud
    print(f"\n📏 Estadísticas de longitud de chunks:")
    print(f"  Min: {df['chunk'].str.len().min()} chars")
    print(f"  Max: {df['chunk'].str.len().max()} chars")
    print(f"  Media: {df['chunk'].str.len().mean():.0f} chars")
    print(f"  Mediana: {df['chunk'].str.len().median():.0f} chars")
    
except Exception as e:
    print(f"⚠️ Error al cargar CSVs: {e}")

print("\n" + "=" * 80)
print("✅ DIAGNÓSTICO COMPLETADO")
print("=" * 80)
