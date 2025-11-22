import pytest
from fastapi.testclient import TestClient

# Import the main module under an alias
import main as main_module 

# Import agent components from src.agent.core
from src.agent.core import load_agent_and_rag_components, CHECKPOINTER
# Import InMemorySaver explicitly as it's used in the test fixture
from langgraph.checkpoint.memory import InMemorySaver


# Create a TestClient instance for your FastAPI application
client = TestClient(main_module.app) # Use main_module.app here

# --- Pytest Fixtures ---
@pytest.fixture(scope="module", autouse=True)
def setup_agent_for_tests():
    """
    Fixture to ensure the agent is loaded before running tests.
    This directly calls load_agent_and_rag_components and handles exceptions.
    """
    print("\n--- Running setup_agent_for_tests fixture ---")
    
    # Reset checkpointer for isolated tests (using the imported InMemorySaver)
    global CHECKPOINTER
    CHECKPOINTER = InMemorySaver()
    
    try:
        # Directly call the agent loading function
        loaded_graph = load_agent_and_rag_components(
            temperature=0.5, top_k=40, top_p=0.9, retriever_k=5
        )
        main_module.AGENT_GRAPH = loaded_graph # Assign to main_module.AGENT_GRAPH
        print(f"DEBUG: Agent loaded successfully in fixture.")
    except Exception as e:
        print(f"ERROR: Agent loading failed in fixture: {e}")
        import traceback
        traceback.print_exc() # Print full traceback
        pytest.fail(f"Agent failed to load in fixture: {e}") # Force test failure
    
    # Ensure TestClient's startup event is also triggered (this will just run, AGENT_GRAPH is already set)
    # The client.get("/health") call here is to ensure the TestClient fully initializes,
    # but the actual AGENT_GRAPH is set directly above.
    client.get("/health") 

    yield 

    print("--- Running teardown for setup_agent_for_tests fixture ---")
    main_module.AGENT_GRAPH = None # Clear agent graph after tests to free memory


# --- Tests ---
def test_health_check_after_startup():
    """
    Test the /health endpoint after the startup event has loaded the agent.
    """
    response = client.get("/health")
    if response.status_code != 200:
        print(f"\nHealth check failed with status {response.status_code}. Detail: {response.json().get('detail', 'No detail provided.')}")
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
    
    if response.status_code != 200:
        print(f"\nSimple chat failed with status {response.status_code}. Detail: {response.json().get('detail', 'No detail provided.')}")
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

    if response.status_code != 200:
        print(f"\nTool invocation (telefono) failed with status {response.status_code}. Detail: {response.json().get('detail', 'No detail provided.')}")
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

    if response.status_code != 200:
        print(f"\nTool invocation (estado_servicio) failed with status {response.status_code}. Detail: {response.json().get('detail', 'No detail provided.')}")
    assert response.status_code == 200
    response_data = response.json()
    assert "response" in response_data
    assert isinstance(response_data["response"], str)
    assert "buenaventura" in response_data["response"].lower()
    assert ("interrupción programada" in response_data["response"].lower() or 
            "servicio normal" in response_data["response"].lower())


