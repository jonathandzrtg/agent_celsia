# 📁 Estructura del Proyecto - Agente Celsia

## 🎯 Visión General

Este proyecto está compuesto por dos partes principales:
1. **Backend (API FastAPI)** - Motor del chatbot con LangGraph y RAG
2. **Frontend (HTML/CSS/JS)** - Interfaz de usuario web

---

## 📂 Estructura Completa de Carpetas

```
agent_celsia/
│
├── 📁 frontend/                    # ✨ INTERFAZ DE USUARIO (NUEVO)
│   ├── index.html                  # Página principal del chat
│   ├── styles.css                  # Estilos con paleta Celsia
│   ├── script.js                   # Lógica de integración con API
│   ├── README.md                   # Documentación del frontend
│   └── 📁 assets/                  # Recursos estáticos
│       └── celsia-logo.png         # Logo de Celsia (agregar aquí)
│
├── 📁 src/                         # Código fuente del backend
│   ├── __init__.py
│   │
│   ├── 📁 agent/                   # Lógica del agente LangGraph
│   │   ├── __init__.py
│   │   ├── core.py                 # Definición del agente y RAG
│   │   └── state.py                # Estado de la conversación
│   │
│   ├── 📁 data/                    # Gestión de datos
│   │   ├── __init__.py
│   │   ├── processing.py           # Procesamiento de documentos
│   │   └── vectorstore.py          # Manejo de ChromaDB
│   │
│   ├── 📁 models/                  # Modelos Pydantic
│   │   ├── __init__.py
│   │   └── api_models.py           # Modelos para la API
│   │
│   ├── 📁 tools/                   # Herramientas del agente
│   │   ├── __init__.py
│   │   └── celsia_tools.py         # Funciones/herramientas
│   │
│   └── 📁 utils/                   # Utilidades
│       ├── __init__.py
│       ├── config.py               # Configuración
│       └── errors.py               # Excepciones personalizadas
│
├── 📁 data/                        # Datos del proyecto
│   ├── 📁 source/                  # Documentos fuente
│   │   ├── celsia_processed_*_chunks.json
│   │   └── post_celsia.json
│   └── 📁 chromadb_storage/        # Base de datos vectorial (generada)
│
├── 📁 docs/                        # Documentación
│   ├── Arquitectura.drawio
│   ├── Arquitectura.drawio.png
│   └── n8n_guide.md                # Guía de integración con n8n
│
├── 📁 notebooks/                   # Jupyter Notebooks
│   ├── rag_celsia.ipynb
│   ├── 📁 transformation/
│   └── 📁 web_scraping/
│
├── 📁 scripts/                     # Scripts auxiliares
│   └── diagnostico_chromadb.py
│
├── 📁 .venv/                       # Entorno virtual Python
│
├── 📄 main.py                      # ⭐ Punto de entrada FastAPI
├── 📄 app.py                       # Versión Streamlit (legacy)
├── 📄 regenerate_chromadb.py       # Script para regenerar ChromaDB
├── 📄 test_api.py                  # Tests de la API
│
├── 📄 .env                         # Variables de entorno
├── 📄 requirements.txt             # Dependencias Python
├── 📄 pyproject.toml               # Configuración del proyecto
├── 📄 uv.lock                      # Lock de dependencias
│
├── 📄 README.md                    # 📖 Documentación principal
├── 📄 INICIO_RAPIDO.md            # 🚀 Guía de inicio rápido
└── 📄 ESTRUCTURA_PROYECTO.md      # 📁 Este archivo
```

---

## 🔄 Flujo de Datos

```
┌─────────────────┐
│   👤 Usuario    │
│  (Navegador)    │
└────────┬────────┘
         │
         │ HTTP Request
         ▼
┌─────────────────────────────────┐
│     🎨 FRONTEND                 │
│  (HTML/CSS/JavaScript)          │
│  - index.html                   │
│  - styles.css (Celsia colors)   │
│  - script.js (API integration)  │
└────────┬────────────────────────┘
         │
         │ POST /chat
         │ (JSON: {user_message, session_id})
         ▼
┌─────────────────────────────────┐
│     ⚙️ BACKEND API              │
│  (FastAPI - main.py)            │
│  - CORS Middleware              │
│  - Chat Endpoint                │
└────────┬────────────────────────┘
         │
         │ Invoke Agent
         ▼
┌─────────────────────────────────┐
│  🤖 LANGGRAPH AGENT             │
│  (src/agent/core.py)            │
│  - Function Calling             │
│  - State Management             │
│  - Tool Selection               │
└────┬───────────────┬────────────┘
     │               │
     │ RAG Tool      │ Other Tools
     ▼               ▼
┌─────────┐    ┌──────────────┐
│ ChromaDB│    │ Celsia Tools │
│ Vector  │    │ - Teléfono   │
│ Store   │    │ - Dirección  │
│         │    │ - PQR, etc.  │
└────┬────┘    └──────┬───────┘
     │                │
     └────────┬───────┘
              │
              ▼
         ┌─────────┐
         │ Ollama  │
         │ Qwen3:4b│
         └────┬────┘
              │
              ▼
         📤 Response
              │
              ▼
         🎨 Frontend
              │
              ▼
         👤 Usuario
```

---

## 🎨 Frontend - Detalle

### Archivos Principales

| Archivo | Propósito | Líneas |
|---------|-----------|--------|
| `index.html` | Estructura HTML del chat | ~92 |
| `styles.css` | Estilos con paleta Celsia | ~501 |
| `script.js` | Lógica JS, integración API | ~329 |
| `README.md` | Documentación completa | ~263 |

### Características Implementadas

✅ Chat en tiempo real  
✅ Indicador de "escribiendo..."  
✅ Historial persistente (localStorage)  
✅ Botón limpiar conversación  
✅ Contador de caracteres  
✅ Responsive design (mobile/tablet/desktop)  
✅ Manejo de errores  
✅ Paleta de colores Celsia  
✅ Auto-resize del textarea  
✅ Teclas rápidas (Enter/Shift+Enter)  

---

## ⚙️ Backend - Detalle

### Archivos Principales

| Archivo | Propósito |
|---------|-----------|
| `main.py` | API FastAPI, endpoints, CORS |
| `src/agent/core.py` | Agente LangGraph, RAG chain |
| `src/agent/state.py` | Estado de conversación |
| `src/tools/celsia_tools.py` | Herramientas personalizadas |
| `regenerate_chromadb.py` | Regeneración de vectores |

### Tecnologías Backend

- **FastAPI** - Framework web
- **LangGraph** - Orquestación del agente
- **LangChain** - Cadenas RAG
- **ChromaDB** - Base de datos vectorial
- **Ollama** - Modelo LLM (Qwen3:4b)
- **Google Generative AI** - Embeddings

---

## 🌈 Paleta de Colores Celsia

```css
/* Colores principales */
--celsia-orange: #ff7705    /* Naranja principal */
--celsia-grey: #59595b      /* Gris principal */
--celsia-white: #ffffff     /* Blanco/fondo */

/* Colores secundarios */
--celsia-orange-hover: #e66b04
--celsia-orange-light: #ff9944
--celsia-grey-light: #8a8a8c
--celsia-grey-lighter: #e5e5e5
```

---

## 🚀 Puntos de Entrada

### Para Desarrollo

```bash
# Backend
uvicorn main:app --reload --port 8000

# Frontend (servidor local)
cd frontend
python -m http.server 8080
```

### Para Producción

```bash
# Backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Frontend
# Servir con Nginx, Apache, o CDN
```

---

## 🔗 Endpoints API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Estado del servidor |
| GET | `/docs` | Documentación Swagger UI |
| POST | `/chat` | Endpoint principal del chat |

### Ejemplo de Request

```json
POST /chat
{
  "user_message": "¿Qué es Celsia?",
  "session_id": "celsia-chat-session"
}
```

### Ejemplo de Response

```json
{
  "response": "Celsia es una empresa colombiana del Grupo Argos dedicada a la generación, transmisión y comercialización de energía eléctrica..."
}
```

---

## 📦 Dependencias Principales

### Python (Backend)
- fastapi
- uvicorn
- langchain
- langgraph
- langchain-ollama
- langchain-google-genai
- chromadb
- python-dotenv

### JavaScript (Frontend)
- Vanilla JS (sin dependencias externas)
- Fetch API (nativo del navegador)
- LocalStorage API (nativo del navegador)

---

## 🔐 Variables de Entorno

```env
# LLM Configuration
OLLAMA_LLM_MODEL=qwen3:4b
OLLAMA_BASE_URL=http://localhost:11434

# Embeddings
GOOGLE_API_KEY=your_google_api_key

# Observability (opcional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=Celsia Chatbot
```

---

## 📊 Métricas del Proyecto

- **Archivos totales**: ~50+
- **Líneas de código (frontend)**: ~950
- **Líneas de código (backend)**: ~2000+
- **Tecnologías**: 10+
- **Endpoints API**: 3
- **Herramientas del agente**: 10+

---

## 🎯 Próximos Pasos Sugeridos

1. ✅ **Agregar logo de Celsia** en `frontend/assets/`
2. 📝 **Personalizar mensajes** de bienvenida según necesidades
3. 🎨 **Ajustar estilos** si es necesario
4. 🔒 **Configurar HTTPS** para producción
5. 📊 **Agregar analytics** (opcional)
6. 🧪 **Crear tests** para el frontend
7. 🚀 **Deploy** en servidor de producción

---

## 📖 Documentación Relacionada

- `README.md` - Documentación principal del proyecto
- `frontend/README.md` - Documentación específica del frontend
- `INICIO_RAPIDO.md` - Guía de inicio rápido
- `docs/n8n_guide.md` - Integración con n8n

---

**Última actualización**: 2025-11-21  
**Versión**: 1.0.0 (con Frontend)
