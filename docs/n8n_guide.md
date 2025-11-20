# Guía para el compañero: Configuración del Workflow de n8n para Agente Celsia con WhatsApp

El objetivo de este documento es proporcionar los pasos detallados para construir un workflow en n8n que reciba mensajes de WhatsApp, los envíe a la API de FastAPI del agente Celsia y devuelva la respuesta a WhatsApp.

**Pre-requisitos:**

1.  **Agente FastAPI funcionando:** El agente Celsia FastAPI debe estar corriendo y accesible a través de una URL pública.
    *   **Si es local (para pruebas/desarrollo):** Usar `ngrok` para exponer el servicio. El equipo de desarrollo te proporcionará la URL de `ngrok` (ej. `https://xxxx-xxxx-xxxx-ngrok-free.app/`).
    *   **Si está en un servidor:** El equipo de desarrollo te proporcionará la URL del endpoint `/chat` del servicio (ej. `https://api.tuservicio.com/chat`).
2.  **Configuración de WhatsApp Business API (WABA):** Ya sea el `Meta Cloud API` de Facebook (recomendado) o un `Twilio WhatsApp Sandbox` (más sencillo para pruebas). Necesitarás las credenciales y el **Webhook URL** para que WhatsApp envíe mensajes a n8n.

---

#### **Paso 1: Crear un nuevo Workflow en n8n**

1.  Abre tu instancia de n8n.
2.  Haz clic en `Workflows` en el menú lateral y luego en `New Workflow`.

#### **Paso 2: Nodo 1 - Webhook (Receptor de mensajes de WhatsApp)**

Este nodo es el punto de entrada para los mensajes de WhatsApp.

1.  Arrastra y suelta un nodo `Webhook` al canvas.
2.  **Configuración del Webhook:**
    *   **Authentication:** `None` (o la que se necesite según la configuración de tu WABA).
    *   **HTTP Method:** `POST`.
    *   **Respond automatically:** `Yes` (para evitar timeouts de WhatsApp).
    *   **JSON structure:** Deja en blanco o proporciona un ejemplo si tienes uno.
    *   Copia la **Webhook URL** que n8n te proporciona (tanto la `Test URL` como la `Production URL`). **Esta es la URL que debes configurar en Meta Cloud API o Twilio para que WhatsApp envíe los mensajes.**

3.  **Captura el mensaje de prueba:**
    *   Guarda el workflow.
    *   Activa el nodo `Webhook` (haz clic en `Execute Workflow` o `Test Workflow`).
    *   Desde tu teléfono, envía un mensaje al número de WhatsApp configurado con tu WABA (Meta o Twilio).
    *   El nodo `Webhook` en n8n debería capturar la entrada y mostrarla en la vista `JSON`. Analiza la estructura JSON para identificar dónde se encuentran el texto del mensaje (`user_message`) y el ID de la sesión (normalmente el número de teléfono del usuario `from`).

    *   **Ejemplo para Meta Cloud API (común):**
        *   `user_message`: `{{ $json.body.entry[0].changes[0].value.messages[0].text.body }}`
        *   `session_id`: `{{ $json.body.entry[0].changes[0].value.messages[0].from }}`
    *   **Ejemplo para Twilio (común):**
        *   `user_message`: `{{ $json.body.Body }}`
        *   `session_id`: `{{ $json.body.From }}` (puede que necesites limpiar el prefijo `whatsapp:+` con una función de n8n si tu agente espera solo el número).

#### **Paso 3: Nodo 2 - HTTP Request (Llamada al Agente FastAPI)**

Este nodo enviará el mensaje del usuario a tu agente FastAPI.

1.  Arrastra y suelta un nodo `HTTP Request` y conéctalo al nodo `Webhook`.
2.  **Configuración del HTTP Request:**
    *   **Authentication:** `None` (o `Header Auth` si tu API de FastAPI requiere una clave API).
    *   **Request Method:** `POST`.
    *   **URL:** Pega la URL **pública** de tu agente FastAPI, seguida de `/chat`.
        *   Ej: `https://xxxx-xxxx-xxxx-ngrok-free.app/chat`
        *   Ej: `https://api.tuservicio.com/chat`
    *   **Headers:**
        *   `Content-Type`: `application/json`
    *   **Body:**
        *   **Body Content Type:** `JSON`.
        *   Crea la estructura JSON esperada por el endpoint `/chat` de FastAPI:
            ```json
            {
              "user_message": "...", // Usa la expresión de n8n capturada del Webhook (ej. {{ $json.body.entry[0].changes[0].value.messages[0].text.body }})
              "session_id": "..."    // Usa la expresión de n8n para el ID de sesión (ej. {{ $json.body.entry[0].changes[0].value.messages[0].from }})
            }
            ```
        *   **Importante:** Asegúrate de que los nombres de los campos (`user_message`, `session_id`) coincidan exactamente con el `ChatRequest` Pydantic model definido en `main.py` de FastAPI.
    *   **Response:**
        *   **Response Format:** `JSON`.
        *   **JSON Parse:** `Always`.

3.  **Prueba la llamada a la API:**
    *   Con el nodo `Webhook` aún activo con la captura de tu mensaje de WhatsApp, ejecuta el nodo `HTTP Request` para asegurarte de que se conecta correctamente a FastAPI y devuelve una respuesta válida del agente.

#### **Paso 4: Nodo 3 - WhatsApp (Envío de la respuesta a WhatsApp)**

Este nodo devolverá la respuesta del agente al usuario de WhatsApp.

1.  Arrastra y suelta un nodo `WhatsApp` y conéctalo al nodo `HTTP Request`.
2.  **Configuración del WhatsApp Node:**
    *   **Credentials:** Configura tus credenciales de Meta o Twilio. Esto solo se hace una vez.
    *   **Phone Number ID:** Ingresa el ID de número de teléfono de tu Meta Cloud API o el número de Twilio.
    *   **To:** `{{ $json.body.entry[0].changes[0].value.messages[0].from }}` (Esta expresión debe ser la misma que usaste para `session_id` en el nodo `Webhook`).
    *   **Message Type:** `Text`.
    *   **Message:** `{{ $json.response.response }}`
        *   **Nota:** `$json.response` es la respuesta JSON completa de tu API de FastAPI. `response` es la clave donde tu agente devuelve el texto final.

3.  **Guarda y Activa el Workflow:**
    *   Guarda tu workflow y asegúrate de que esté `Active`.

---

#### **Consideraciones Adicionales para tu compañero:**

*   **Transformación de Datos:** A veces, los datos de WhatsApp (especialmente el `session_id` o `from` number) pueden venir con prefijos (ej. `whatsapp:+123456789`). Si tu agente solo espera el número limpio, puedes añadir un nodo `Code` o `Set` en n8n para limpiar estos datos antes de enviarlos a FastAPI.
*   **Manejo de Errores en n8n:** n8n tiene excelente manejo de errores. Se recomienda añadir un nodo `Error Trigger` después de los nodos `HTTP Request` y `WhatsApp` para capturar cualquier fallo y enviar un mensaje genérico al usuario (ej. "Lo siento, hubo un problema técnico") en lugar de dejar la conversación en silencio.
*   **Mensajes enriquecidos:** Si en el futuro el agente FastAPI genera respuestas más allá de texto plano (imágenes, botones, etc.), el nodo `WhatsApp` en n8n deberá configurarse para manejar esos tipos de mensajes. La API de FastAPI deberá devolver un JSON con la estructura que n8n espera para esos tipos.
*   **Persistencia de la Sesión:** n8n, al llamar a tu API de FastAPI con un `session_id`, ya está aprovechando la gestión de memoria del agente. Tu colega no necesita hacer nada adicional para esto en n8n.

---
