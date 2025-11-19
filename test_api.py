from fastapi.testclient import TestClient
import pytest

# Import the main module to access its app instance and global variables
import main 

# Create a TestClient instance for your FastAPI application
# This automatically handles startup/shutdown events for the app
client = TestClient(main.app)

# --- Pytest Fixtures ---
@pytest.fixture(scope="module", autouse=True)
def setup_agent_for_tests():
    """
    Fixture to ensure the agent is loaded before running tests.
    This mimics the startup event of the FastAPI app.
    """
    # Ensure the AGENT_GRAPH is cleared before loading for tests
    main.AGENT_GRAPH = None 
    
    print("\n--- Running setup_agent_for_tests fixture ---")
    
    # Reset checkpointer for isolated tests
    main.CHECKPOINTER = main.InMemorySaver()
    
    # Calling the actual startup logic directly to ensure global AGENT_GRAPH is set for tests
    try:
        # FastAPI's TestClient usually handles startup events, but due to issues,
        # we explicitly ensure the AGENT_GRAPH is loaded.
        # This is a workaround if TestClient's startup doesn't fully trigger
        # blocking calls or complex setups.
        if main.AGENT_GRAPH is None: # Only load if not already loaded by TestClient startup
            # This line simulates the startup event logic
            loaded_graph = main.load_agent_and_rag_components(
                temperature=0.5, top_k=40, top_p=0.9, retriever_k=5
            )
            main.AGENT_GRAPH = loaded_graph # Assignment to the global AGENT_GRAPH
        
        # Ensure the client is fully started.
        client.get("/health") 
        
        print("AGENT_GRAPH is loaded for tests:", main.AGENT_GRAPH is not None)
        yield 
    finally:
        print("--- Running teardown for setup_agent_for_tests fixture ---")
        # Optional: Clean up resources if necessary after all tests in module
        main.AGENT_GRAPH = None # Clear agent graph after tests to free memory


# --- Tests ---
def test_health_check_after_startup():
    """
    Test the /health endpoint after the startup event has loaded the agent.
    """
    response = client.get("/health")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "ok"
    assert "Agent loaded." in response_data["message"]

def test_chat_endpoint_simple_message():
    """
    Test the /chat endpoint with a simple message and a session ID.
    """
    user_message = "Hola, ¿cómo estás?"
    session_id = "test_session_123"
    
    response = client.post(
        "/chat",
        json={"user_message": user_message, "session_id": session_id}
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert "response" in response_data
    assert isinstance(response_data["response"], str)
    assert len(response_data["response"]) > 0 # Expect a non-empty response
    # The response might vary, so a broad check is better for integration tests
    assert any(keyword in response_data["response"].lower() for keyword in ["hola", "bien", "puedo ayudarte", "celsia"])

def test_chat_endpoint_tool_invocation_telefono():
    """
    Test the /chat endpoint to ensure a tool is invoked correctly (e.g., get_telefono_celsia).
    """
    user_message = "¿Cuál es el número de teléfono de Celsia?"
    session_id = "test_session_telefono"

    response = client.post(
        "/chat",
        json={"user_message": user_message, "session_id": session_id}
    )

    assert response.status_code == 200
    response_data = response.json()
    assert "response" in response_data
    assert isinstance(response_data["response"], str)
    assert "01 8000 112 115" in response_data["response"] or "507) 832 7907" in response_data["response"]

def test_chat_endpoint_tool_invocation_estado_servicio():
    """
    Test the /chat endpoint to ensure a tool is invoked correctly (e.g., verificar_estado_servicio).
    This depends on the LLM correctly identifying the tool and parameters.
    """
    user_message = "¿Hay interrupciones de servicio en Buenaventura?"
    session_id = "test_session_buenaventura"

    response = client.post(
        "/chat",
        json={"user_message": user_message, "session_id": session_id}
    )

    assert response.status_code == 200
    response_data = response.json()
    assert "response" in response_data
    assert isinstance(response_data["response"], str)
    assert "buenaventura" in response_data["response"].lower()
    assert ("interrupción programada" in response_data["response"].lower() or 
            "servicio normal" in response_data["response"].lower())


