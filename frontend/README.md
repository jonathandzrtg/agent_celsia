# 🎨 Frontend - Chatbot Celsia

Interfaz de usuario web para el chatbot inteligente de Celsia, desarrollada con HTML, CSS y JavaScript vanilla.

---

## ✨ Características

- 💬 **Chat en tiempo real** con el asistente virtual de Celsia
- 🎨 **Diseño responsive** adaptable a dispositivos móviles y desktop
- 🎨 **Paleta de colores oficial** de Celsia (Naranja #ff7705, Gris #59595b, Fondo blanco)
- 💾 **Historial persistente** mediante localStorage
- ⌨️ **Indicador de escritura** mientras el bot procesa la respuesta
- 🗑️ **Función de limpiar conversación**
- ♿ **Accesible** con semántica HTML adecuada
- 📱 **Totalmente responsive** (móvil, tablet, desktop)

---

## 📁 Estructura de Archivos

```
frontend/
├── index.html          # Página principal del chat
├── styles.css          # Estilos con paleta Celsia
├── script.js           # Lógica de integración con API
├── assets/             # Recursos estáticos
│   └── celsia-logo.png # Logo de Celsia (agregar aquí)
└── README.md           # Esta documentación
```

---

## 🚀 Instalación y Uso

### Requisitos Previos

1. **API Backend ejecutándose**: El frontend necesita que el API de FastAPI esté corriendo en `http://localhost:8000`
2. **Navegador web moderno**: Chrome, Firefox, Safari, Edge (versiones recientes)
3. **Logo de Celsia**: Coloca el archivo `celsia-logo.png` en la carpeta `assets/` (opcional, si no existe se ocultará automáticamente)

### Opción 1: Abrir directamente (Método Simple)

1. Abre el archivo `index.html` directamente en tu navegador web:
   ```bash
   # Windows (PowerShell)
   start frontend\index.html
   
   # O simplemente haz doble clic en index.html
   ```

⚠️ **Nota sobre CORS**: Si experimentas problemas de CORS al abrir directamente el archivo, usa la Opción 2.

### Opción 2: Servidor Local (Método Recomendado)

Para evitar problemas de CORS, ejecuta un servidor HTTP local:

**Usando Python 3:**
```bash
# Navega a la carpeta frontend
cd frontend

# Python 3
python -m http.server 8080

# O si tienes Python 2
python -m SimpleHTTPServer 8080
```

**Usando Node.js (http-server):**
```bash
# Instala http-server globalmente (solo una vez)
npm install -g http-server

# Ejecuta el servidor
cd frontend
http-server -p 8080
```

**Usando PHP:**
```bash
cd frontend
php -S localhost:8080
```

Luego abre tu navegador en: `http://localhost:8080`

---

## 🔧 Configuración

### Cambiar URL del API

Si tu API corre en un puerto o host diferente, edita `script.js`:

```javascript
// Línea 4 en script.js
const API_URL = 'http://localhost:8000/chat';  // Cambia esta URL
```

### Agregar el Logo de Celsia

1. Coloca tu imagen del logo en la carpeta `assets/`
2. Renómbrala a `celsia-logo.png` (o actualiza la referencia en `index.html` línea 15)
3. Formato recomendado: PNG con fondo transparente, tamaño aproximado 200x200px

---

## 🎯 Uso del Chatbot

1. **Iniciar una conversación**: Escribe tu mensaje en el área de texto y presiona Enter o haz clic en el botón de enviar
2. **Nueva línea**: Usa Shift + Enter para agregar saltos de línea en tu mensaje
3. **Ver historial**: El historial se guarda automáticamente en localStorage y persiste entre sesiones
4. **Limpiar conversación**: Haz clic en el icono de papelera en la esquina superior derecha
5. **Indicador de escritura**: Los puntos animados indican que el bot está procesando tu mensaje

### Ejemplos de Preguntas

- "¿Cuál es el teléfono de contacto de Celsia?"
- "¿Cómo puedo pagar mi factura?"
- "¿Dónde están ubicadas las oficinas de Celsia?"
- "¿Qué servicios de energía solar ofrecen?"
- "¿Cuáles son los programas de sostenibilidad?"

---

## 🎨 Personalización

### Colores

Los colores de Celsia están definidos como variables CSS en `styles.css` (líneas 4-17):

```css
:root {
    --celsia-orange: #ff7705;        /* Naranja principal */
    --celsia-orange-hover: #e66b04;  /* Naranja hover */
    --celsia-grey: #59595b;          /* Gris principal */
    --celsia-white: #ffffff;         /* Blanco */
}
```

Para cambiar los colores, modifica estas variables.

### Límite de Caracteres

El límite actual es de 1000 caracteres por mensaje. Para cambiarlo:

1. Edita `index.html` línea 76: `maxlength="1000"`
2. Edita el contador en la misma línea del código

---

## 🐛 Solución de Problemas

### Error: "No se pudo conectar con el servidor"

**Causa**: El API de FastAPI no está corriendo o la URL es incorrecta.

**Solución**:
1. Verifica que el API esté corriendo:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
2. Verifica que puedas acceder a `http://localhost:8000/health` en tu navegador
3. Revisa la URL en `script.js`

### Error de CORS

**Causa**: Restricciones de seguridad del navegador al abrir archivos locales.

**Solución**:
1. Usa un servidor HTTP local (ver Opción 2 en Instalación)
2. O agrega configuración CORS en el backend FastAPI (en `main.py`):

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### El historial no se guarda

**Causa**: localStorage bloqueado o navegación privada.

**Solución**:
- No uses modo incógnito/privado
- Verifica los permisos de localStorage en la configuración del navegador

### El logo no aparece

**Causa**: Archivo no encontrado o ruta incorrecta.

**Solución**:
- Verifica que `celsia-logo.png` esté en la carpeta `assets/`
- El logo se oculta automáticamente si no existe (comportamiento por diseño)

---

## 📱 Responsive Design

El chatbot es completamente responsive con breakpoints en:

- **Desktop**: > 768px (diseño completo)
- **Tablet**: 481px - 768px (ajustes de espaciado)
- **Mobile**: ≤ 480px (optimizado para pantallas pequeñas)

---

## 🔒 Seguridad y Privacidad

- **Sesión única**: Todos los usuarios comparten el mismo `session_id` para simplificar la implementación
- **Almacenamiento local**: El historial se guarda solo en el navegador del usuario (localStorage)
- **Sin autenticación**: Esta versión no incluye sistema de usuarios ni autenticación
- **Datos en tránsito**: Las comunicaciones con el API se realizan por HTTP (considera HTTPS para producción)

---

## 🚀 Despliegue en Producción

Para desplegar este frontend en producción:

1. **Cambiar la URL del API** a la URL de producción
2. **Habilitar HTTPS** tanto en frontend como backend
3. **Configurar CORS** adecuadamente en el backend
4. **Optimizar assets**: Minificar CSS/JS, comprimir imágenes
5. **Servir desde un servidor web**: Nginx, Apache, o CDN
6. **Agregar analytics** si es necesario (Google Analytics, etc.)

### Ejemplo con Nginx

```nginx
server {
    listen 80;
    server_name tu-dominio.com;
    
    root /ruta/a/frontend;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 📄 Licencia

Este proyecto es parte del Agente Celsia desarrollado por el Grupo 1.

---

## 👥 Soporte

Para reportar problemas o solicitar nuevas funcionalidades, contacta al equipo de desarrollo.

**¡Disfruta usando el Asistente Virtual de Celsia! 🚀⚡**
