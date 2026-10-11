# Agent Swarms

A practical starter project showing how to orchestrate multiple AI agents for a production-incident investigation.

The example uses **FastAPI** and the **OpenAI Agents SDK**. Two specialist agents independently analyze log and deployment evidence, then a synthesis agent combines their findings into one report.

> This is an educational starter, not a production incident-management system. It analyzes evidence supplied in the API request; it does not connect to real observability or deployment platforms.

## Architecture

![Agent swarm workflow](diagrams/agent-swarm-overview.png)

![Production deployment architecture](diagrams/deployment-architecture.png)

### Why multiple agents?

- **Log Investigator** focuses on errors and patterns in log evidence.
- **Deployment Investigator** reviews the supplied release/change evidence.
- **Incident Analyst** synthesizes both outputs and distinguishes evidence from hypotheses.
- **FastAPI** exposes a simple HTTP endpoint.

The log and deployment investigations run concurrently because neither depends on the other's output. The synthesis stage starts after both finish.

## Requirements

- Python 3.11+ (the Docker image uses Python 3.12)
- An OpenAI API key
- Internet access for model requests

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key"  # PowerShell: $env:OPENAI_API_KEY="your-api-key"
uvicorn app:app --reload
```

Open `http://localhost:8000/docs` to try the API.

## Example request

```bash
curl -X POST http://localhost:8000/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "incident": "API latency increased after a release",
    "logs": "Request timeouts increased at 14:12 UTC.",
    "deployments": "Release 482 completed at 14:00 UTC."
  }'
```

Example response shape:

```json
{
  "report": "Observed facts ... Plausible explanation ... Verification steps ..."
}
```

The model output will vary. A release occurring before an incident is a clue, not proof that the release caused it.

## Run tests

```bash
pytest -q
```

The tests cover the health endpoint and request validation. They do not call the model API.

## Run with Docker

```bash
docker build -t agent-swarms .
docker run --rm -p 8000:8000 -e OPENAI_API_KEY=your-api-key agent-swarms
```

Do not bake secrets into the image. Pass them through your deployment platform's secret manager.

## API

### `GET /health`

Returns a lightweight health response.

### `POST /investigate`

Request body:

```json
{
  "incident": "API latency increased after a release",
  "logs": "Relevant log excerpts go here",
  "deployments": "Relevant release/change records go here"
}
```

Input fields are length-limited. The request has a 90-second investigation timeout.

## Production checklist

Before production use, add:

- **Real integrations:** read-only tools for log search, metrics, traces, and deployment history.
- **Evidence provenance:** return links or IDs for the source records behind every claim.
- **Authentication and authorization:** protect the API and enforce tenant boundaries.
- **Tool permissions:** keep investigation read-only by default; require approval for remediation.
- **Timeouts and retries:** define per-tool budgets, bounded retries, cancellation, and partial-failure behavior.
- **Queue-backed workers:** use a queue for long-running tasks instead of holding HTTP requests open.
- **Observability:** trace agent runs, model calls, tool calls, latency, failures, and token/cost usage.
- **Evaluation:** compare against a single-agent baseline using a fixed incident dataset.
- **Prompt-injection defenses:** treat retrieved logs and documents as untrusted data.
- **Data governance:** redact secrets and sensitive data from prompts and logs.
- **Dependency management:** pin tested dependency versions and scan images/dependencies.

## Suggested next steps

1. Replace request-provided evidence with controlled read-only tools.
2. Define a structured finding schema with evidence references.
3. Add a verification step that checks conclusions against source records.
4. Add regression evaluations for root-cause accuracy and evidence grounding.
5. Introduce a queue and persistent workflow state only when workload requires it.

## References

- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [OpenAI Agents SDK: Multi-agent orchestration](https://openai.github.io/openai-agents-python/multi_agent/)
- [OpenAI Agents SDK: Tracing](https://openai.github.io/openai-agents-python/tracing/)
- [Anthropic: How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Anthropic: Building effective AI agents](https://resources.anthropic.com/building-effective-ai-agents)

## License

Add a license file before publishing if you want to specify reuse and distribution terms.
