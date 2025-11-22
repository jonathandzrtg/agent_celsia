# 🚀 Inicio Rápido - Sistema Completo Chatbot Celsia

Esta guía te ayudará a poner en marcha el sistema completo (Backend + Frontend) en minutos.

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

1. **Python 3.8+** (con uv o pip)
2. **Ollama** con el modelo `qwen3:4b`
3. **Google API Key** para embeddings
4. **Navegador web moderno**

---

## ⚡ Pasos de Inicio Rápido

### 1️⃣ Configurar Variables de Entorno

Verifica que tu archivo `.env` contenga:

```env
# Modelo LLM
OLLAMA_LLM_MODEL=qwen3:4b
OLLAMA_BASE_URL=http://localhost:11434

# Google API Key para embeddings
GOOGLE_API_KEY=tu_clave_aqui

# LangSmith (Opcional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=tu_clave_langsmith
LANGCHAIN_PROJECT=Celsia Chatbot
```

### 2️⃣ Iniciar Ollama

En una terminal:

```bash
ollama serve
```

Verifica que el modelo esté descargado:

```bash
ollama list
# Si no está qwen3:4b, descárgalo:
ollama pull qwen3:4b
```

### 3️⃣ Iniciar el Backend (API FastAPI)

En una **nueva terminal**, desde la raíz del proyecto:

```bash
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# o
source .venv/bin/activate  # Linux/Mac

# Iniciar el servidor FastAPI
uvicorn main:app --host 0.0.0.0 --port 8000
```

Deberías ver:
```
✅ Agent components loaded successfully.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Verificar el API**: Abre http://localhost:8000/health en tu navegador.

### 4️⃣ Iniciar el Frontend

**Opción A: Abrir directamente (simple, pero puede tener problemas CORS)**

```bash
start frontend\index.html
```

O simplemente haz doble clic en `frontend/index.html`

**Opción B: Servidor HTTP local (recomendado)**

En una **tercera terminal**:

```bash
# Usando Python
cd frontend
python -m http.server 8080

# O si tienes Node.js con http-server
npx http-server -p 8080
```

Luego abre: http://localhost:8080

---

## ✅ Verificación

Una vez que todo esté ejecutándose:

1. ✅ **Ollama**: Terminal 1 ejecutando `ollama serve`
2. ✅ **Backend API**: Terminal 2 ejecutando `uvicorn` en http://localhost:8000
3. ✅ **Frontend**: Terminal 3 (opcional) ejecutando servidor HTTP en http://localhost:8080

### Probar el Sistema

1. Abre el frontend en tu navegador
2. Escribe un mensaje de prueba: "Hola, ¿qué es Celsia?"
3. Deberías ver el indicador de "escribiendo..." y luego una respuesta del bot

---

## 🐛 Solución Rápida de Problemas

### ❌ Error: "No se pudo conectar con el servidor"

**Causa**: El backend no está ejecutándose.

**Solución**: Verifica que el servidor FastAPI esté corriendo y accesible en http://localhost:8000/health

### ❌ Error CORS

**Causa**: Abriste el `index.html` directamente sin servidor HTTP.

**Solución**: Usa la Opción B (servidor HTTP local) del paso 4.

### ❌ Error: "Agent not loaded yet"

**Causa**: Problemas con Ollama, Google API Key o ChromaDB.

**Solución**:
1. Verifica que Ollama esté ejecutándose: `ollama list`
2. Verifica tu `GOOGLE_API_KEY` en `.env`
3. Verifica que existe la carpeta `chromadb_storage` (si no, ejecuta `python regenerate_chromadb.py`)

### ❌ El logo no aparece

**Causa**: Falta el archivo del logo.

**Solución**: Coloca `celsia-logo.png` en `frontend/assets/` (el sistema funcionará sin logo, solo no se mostrará)

---

## 🎯 URLs Importantes

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Backend API** | http://localhost:8000 | API FastAPI |
| **API Docs** | http://localhost:8000/docs | Swagger UI interactivo |
| **Health Check** | http://localhost:8000/health | Estado del servidor |
| **Frontend** | http://localhost:8080 | Interfaz del chatbot |
| **Ollama** | http://localhost:11434 | Servidor Ollama |

---

## 📝 Comandos Útiles

### Ver logs del backend
El servidor FastAPI muestra los logs directamente en la terminal donde lo iniciaste.

### Detener todo
1. Presiona `Ctrl+C` en cada terminal para detener los servicios
2. Cierra el navegador

### Limpiar historial del chat
- Desde el frontend: Click en el icono de papelera
- Desde el navegador: Borrar localStorage (F12 → Application → Local Storage)

### Regenerar base de datos vectorial
Si actualizaste los documentos fuente:

```bash
python regenerate_chromadb.py
```

---

## 🎨 Personalización Rápida

### Cambiar colores
Edita `frontend/styles.css` líneas 4-17 (variables CSS)

### Cambiar puerto del frontend
Modifica el puerto en el comando del servidor HTTP:
```bash
python -m http.server 9000  # Usa puerto 9000
```

Luego actualiza `frontend/script.js` línea 4 si es necesario.

### Cambiar puerto del backend
```bash
uvicorn main:app --port 8080
```

No olvides actualizar `frontend/script.js` línea 4 con la nueva URL.

---

## 📚 Documentación Adicional

- **Frontend**: Ver `frontend/README.md`
- **Backend**: Ver `README.md` principal
- **API**: http://localhost:8000/docs (cuando el servidor esté corriendo)

---

## 🎉 ¡Listo!

Ahora tienes el chatbot de Celsia funcionando completamente. Puedes:

- Hacer preguntas sobre Celsia
- Ver el historial de conversaciones
- Limpiar el chat
- Personalizar los colores y estilos

**¡Disfruta usando el Asistente Virtual de Celsia! 🚀⚡**
