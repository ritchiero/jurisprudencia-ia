import time
import requests
import pytest

from src.coordination_system import create_coordinated_agentic_system
from src.external_tools import ExternalToolsManager


def test_basic_imports():
    from src.agentic_base import create_agentic_system, MessageBus
    from src.specialized_agents import AgenteOrquestador, AgenteInterpretacion
    assert create_agentic_system
    assert MessageBus
    assert AgenteOrquestador
    assert AgenteInterpretacion


def test_agentic_system_lifecycle():
    system, _ = create_coordinated_agentic_system()
    assert system.agent_registry.get_agent("interpretacion") is not None
    system.start()
    time.sleep(1)
    assert system.running
    system.stop()
    assert not system.running


def test_external_tools_perplexity():
    tools = ExternalToolsManager()
    result = tools.enhance_with_perplexity("marcas y caducidad")
    assert result["success"]
    stats = tools.get_cache_stats()
    assert "cached_items" in stats


def test_workflow_execution():
    system, orchestrator = create_coordinated_agentic_system()
    system.start()
    workflow_id = orchestrator.start_workflow(
        "jurisprudencia_search",
        {"user_query": "marcas", "session_id": "test"},
    )
    time.sleep(1)
    status = orchestrator.get_workflow_status(workflow_id)
    assert status is not None
    system.stop()


def test_api_endpoints():
    base_url = "http://localhost:5000"
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.skip("Server not running")
