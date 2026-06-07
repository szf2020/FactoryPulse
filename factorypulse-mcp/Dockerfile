FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY factorypulse_mcp ./factorypulse_mcp
RUN pip install --no-cache-dir .

# Containers can't be attached to a parent process's stdio, so HTTP-based
# transport is the sensible default here (stdio remains the default for
# local/Claude Desktop use — see config.py).
ENV MCP_TRANSPORT=streamable-http
EXPOSE 8000

CMD ["python", "-m", "factorypulse_mcp.server"]
