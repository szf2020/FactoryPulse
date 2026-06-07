"""
Exercises the HTTP surface of the assistant: POST /ask delegates to the agent
and shapes its answer as JSON. The real agent (and its Anthropic/FactoryPulse
collaborators) is swapped for a fake via FastAPI's dependency override — no
network, API key or live FactoryPulse instance needed.
"""
import pytest
from fastapi.testclient import TestClient

from factorypulse_assistant.main import app, get_agent


class FakeAgent:
    def __init__(self, answer="DB-01's global OEE over the last 24h is 80%."):
        self.answer = answer
        self.questions = []

    async def ask(self, question):
        self.questions.append(question)
        return self.answer


@pytest.fixture
def client():
    fake_agent = FakeAgent()
    app.dependency_overrides[get_agent] = lambda: fake_agent
    try:
        with TestClient(app) as test_client:
            test_client.fake_agent = fake_agent
            yield test_client
    finally:
        app.dependency_overrides.pop(get_agent, None)


def test_ask_returns_the_agents_answer(client):
    response = client.post("/ask", json={"question": "What's DB-01's OEE today?"})

    assert response.status_code == 200
    assert response.json() == {"answer": "DB-01's global OEE over the last 24h is 80%."}
    assert client.fake_agent.questions == ["What's DB-01's OEE today?"]


def test_ask_rejects_blank_questions(client):
    response = client.post("/ask", json={"question": ""})

    assert response.status_code == 422
    assert client.fake_agent.questions == []


def test_ask_rejects_missing_question_field(client):
    response = client.post("/ask", json={})

    assert response.status_code == 422
    assert client.fake_agent.questions == []
