# Build from the repository root so this image can also COPY the
# factorypulse-mcp package it depends on (the FactoryPulse API client is
# shared between the two services rather than duplicated):
#
#   docker build -f factorypulse-assistant/Dockerfile -t factorypulse-assistant .
#
FROM python:3.12-slim

WORKDIR /app

COPY factorypulse-mcp ./factorypulse-mcp
COPY factorypulse-assistant/pyproject.toml ./factorypulse-assistant/
COPY factorypulse-assistant/factorypulse_assistant ./factorypulse-assistant/factorypulse_assistant

RUN pip install --no-cache-dir ./factorypulse-mcp \
    && pip install --no-cache-dir ./factorypulse-assistant

EXPOSE 8001

CMD ["uvicorn", "factorypulse_assistant.main:app", "--host", "0.0.0.0", "--port", "8001"]
