"""
Script para Regenerar ChromaDB con Datos Limpios
Elimina chunks problemáticos y regenera la base de datos vectorial
"""

import pandas as pd
import shutil
import os
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import re

print("=" * 80)
print("🔄 REGENERACIÓN DE BASE DE DATOS VECTORIAL")
print("=" * 80)

# ===== PASO 1: CARGAR DATOS ORIGINALES =====
print("\n📂 Paso 1: Cargando datos originales...")

df1 = pd.read_csv("./data/chunks/celsia_processed_20251015_223656_chunks.csv")
df2 = pd.read_csv("./data/chunks/post_celsia_chunks.csv")

df1 = df1[['Contenido_Completo']].rename(columns={'Contenido_Completo': 'chunk'})
df2 = df2[['chunk']]
df = pd.concat([df1, df2], ignore_index=True)

print(f"✅ Se cargaron {len(df)} chunks totales")

# ===== PASO 2: LIMPIAR DATOS =====
print("\n🧹 Paso 2: Limpiando datos...")

# Función de limpieza mejorada
def limpiar_texto_para_rag(texto):
    if pd.isna(texto) or not isinstance(texto, str):
        return ""
    
    # a) Eliminar emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F900-\U0001F9FF"
        "\U00002702-\U000027B0"
        "]+", flags=re.UNICODE)
    texto = emoji_pattern.sub(r'', texto)
    
    # Eliminar caracteres especiales manteniendo puntuación básica
    texto = re.sub(r'[^a-zA-Z0-9\sñáéíóúüÑÁÉÍÓÚÜ.,;:¿?¡!()-]', '', texto)
    
    # Eliminar patrones repetitivos
    patron_frase_completa = r'\bEdición\s*\d+\s*Tolima\b\.?'
    texto = re.sub(patron_frase_completa, '', texto, flags=re.IGNORECASE)
    
    # Eliminar palabras sueltas problemáticas
    palabras_sueltas_a_eliminar = ['hashtag', 'undefined']
    patron_palabras_sueltas = r'\b(' + '|'.join(palabras_sueltas_a_eliminar) + r')\b'
    texto = re.sub(patron_palabras_sueltas, '', texto, flags=re.IGNORECASE)

    # Limpieza final: eliminar espacios extra
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    return texto

# Aplicar limpieza
df['chunk_limpio'] = df['chunk'].apply(limpiar_texto_para_rag)

# ===== PASO 3: FILTRAR CHUNKS PROBLEMÁTICOS =====
print("\n🔍 Paso 3: Filtrando chunks problemáticos...")

inicial = len(df)

# 1. Eliminar chunks vacíos o muy cortos (< 30 caracteres)
df = df[df['chunk_limpio'].str.len() >= 30]
print(f"  - Eliminados {inicial - len(df)} chunks muy cortos (<30 chars)")

# 2. Eliminar duplicados exactos
inicial = len(df)
df = df.drop_duplicates(subset=['chunk_limpio'])
print(f"  - Eliminados {inicial - len(df)} chunks duplicados")

# 3. Eliminar chunks que solo tienen palabras repetitivas o sin sentido
def es_chunk_valido(texto):
    # Verificar que tenga al menos 3 palabras diferentes
    palabras = texto.split()
    if len(set(palabras)) < 3:
        return False
    # Verificar que tenga al menos una palabra de más de 4 letras
    if not any(len(p) > 4 for p in palabras):
        return False
    return True

inicial = len(df)
df = df[df['chunk_limpio'].apply(es_chunk_valido)]
print(f"  - Eliminados {inicial - len(df)} chunks sin contenido significativo")

print(f"\n✅ Total de chunks limpios: {len(df)}")

# Estadísticas finales
print(f"\n📊 Estadísticas de longitud después de limpieza:")
print(f"  Min: {df['chunk_limpio'].str.len().min()} chars")
print(f"  Max: {df['chunk_limpio'].str.len().max()} chars")
print(f"  Media: {df['chunk_limpio'].str.len().mean():.0f} chars")
print(f"  Mediana: {df['chunk_limpio'].str.len().median():.0f} chars")

# ===== PASO 4: ELIMINAR CHROMADB ANTIGUA =====
print("\n🗑️ Paso 4: Eliminando base de datos anterior...")

chromadb_path = "./chromadb_storage"
if os.path.exists(chromadb_path):
    try:
        shutil.rmtree(chromadb_path)
        print(f"✅ Directorio {chromadb_path} eliminado")
    except Exception as e:
        print(f"⚠️ Error al eliminar: {e}")
        print("   Cierra cualquier proceso que esté usando ChromaDB y reintenta")
        exit(1)
else:
    print(f"ℹ️ No existe base de datos anterior")

# ===== PASO 5: CREAR DOCUMENTOS =====
print("\n📄 Paso 5: Creando documentos para LangChain...")

documentos = []
for i, row in df.iterrows():
    doc = Document(
        page_content=row['chunk_limpio'],
        metadata={
            "source": f"chunk_{i}",
            "length": len(row['chunk_limpio'])
        }
    )
    documentos.append(doc)

print(f"✅ Se crearon {len(documentos)} documentos")

# ===== PASO 6: CONFIGURAR EMBEDDINGS =====
print("\n🔢 Paso 6: Configurando embeddings...")

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

print("✅ Embeddings configurados")

# ===== PASO 7: CREAR Y PERSISTIR VECTORSTORE =====
print("\n💾 Paso 7: Creando nueva base de datos vectorial...")
print("   (Esto puede tardar varios minutos dependiendo del tamaño)")

try:
    vectorstore = Chroma.from_documents(
        documents=documentos,
        embedding=embeddings,
        persist_directory=chromadb_path,
        collection_name="rag_collection"
    )
    print(f"✅ ChromaDB creado exitosamente en {chromadb_path}")
except Exception as e:
    print(f"❌ Error al crear ChromaDB: {e}")
    exit(1)

# ===== PASO 8: VERIFICACIÓN =====
print("\n🔍 Paso 8: Verificando la nueva base de datos...")

# Verificar conteo
total_docs = vectorstore._collection.count()
print(f"✅ Documentos en la nueva BD: {total_docs}")

# Probar algunas consultas
preguntas_prueba = [
    "¿Qué es Celsia?",
    "¿Cómo funciona la facturación?",
    "¿Qué es la energía solar?",
]

print("\n📝 Probando recuperación de documentos:")
chunks_recuperados = set()

for pregunta in preguntas_prueba:
    docs = vectorstore.similarity_search_with_score(pregunta, k=3)
    print(f"\n  ❓ {pregunta}")
    for i, (doc, score) in enumerate(docs, 1):
        source = doc.metadata.get('source', 'unknown')
        chunks_recuperados.add(source)
        content_preview = doc.page_content[:80].replace('\n', ' ')
        print(f"     [{i}] {source} - Score: {score:.2f}")
        print(f"         '{content_preview}...'")

print(f"\n✅ Se recuperaron {len(chunks_recuperados)} chunks únicos de 3 consultas")

if len(chunks_recuperados) > 3:
    print("🎉 ¡Excelente! La base de datos ahora tiene más diversidad")
else:
    print("⚠️ Aún hay poca diversidad. Puede ser necesario revisar los datos originales")

# ===== PASO 9: GUARDAR DATOS LIMPIOS (OPCIONAL) =====
print("\n💾 Paso 9: Guardando chunks limpios para referencia...")

df_export = df[['chunk_limpio']].rename(columns={'chunk_limpio': 'chunk'})
df_export.to_csv("./data/chunks/chunks_limpios.csv", index=False)
print("✅ Chunks limpios guardados en ./data/chunks/chunks_limpios.csv")

print("\n" + "=" * 80)
print("✅ REGENERACIÓN COMPLETADA EXITOSAMENTE")
print("=" * 80)
print("\n💡 Siguiente paso: Ejecuta 'streamlit run app.py' y prueba el agente")
