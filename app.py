import asyncio
import os
from typing import List

from agents import Agent, Runner
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is required")

log_agent = Agent(
    name="Log Investigator",
    instructions=(
        "Analyze only the log evidence provided. Separate observed facts "
        "from hypotheses. Cite short evidence snippets where possible. "
        "Never invent log entries or claim causation without evidence."
    ),
)

deployment_agent = Agent(
    name="Deployment Investigator",
    instructions=(
        "Analyze only the deployment evidence provided. Identify changes "
        "that may be temporally related to the incident. Distinguish "
        "correlation from causation and never invent events."
    ),
)

synthesis_agent = Agent(
    name="Incident Analyst",
    instructions=(
        "Combine the investigation reports into a concise incident report. "
        "Include observed facts, plausible root cause, supporting evidence, "
        "contradictions, missing information, and verification steps. "
        "Do not present an unverified hypothesis as a confirmed root cause."
    ),
)

app = FastAPI(
    title="Agent Swarms: Incident Investigator",
    description="A minimal multi-agent orchestration example.",
    version="0.1.0",
)


class IncidentRequest(BaseModel):
    incident: str = Field(min_length=5, max_length=2000)
    logs: str = Field(min_length=1, max_length=12000)
    deployments: str = Field(min_length=1, max_length=12000)


class IncidentResponse(BaseModel):
    report: str


async def investigate(request: IncidentRequest) -> str:
    log_task = f"Incident: {request.incident}\nLog evidence:\n{request.logs}"
    deployment_task = (
        f"Incident: {request.incident}\n"
        f"Deployment evidence:\n{request.deployments}"
    )

    # These investigations are independent, so run them concurrently.
    log_result, deployment_result = await asyncio.gather(
        Runner.run(log_agent, log_task),
        Runner.run(deployment_agent, deployment_task),
    )

    synthesis_input = f"""
Incident:
{request.incident}

Log investigator findings:
{log_result.final_output}

Deployment investigator findings:
{deployment_result.final_output}

Return a report with:
1. Observed facts
2. Most plausible explanation (label it a hypothesis if unconfirmed)
3. Supporting and contradictory evidence
4. Missing information
5. Recommended verification steps
"""
    final_result = await Runner.run(synthesis_agent, synthesis_input)
    return final_result.final_output


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/investigate", response_model=IncidentResponse)
async def investigate_endpoint(request: IncidentRequest):
    try:
        report = await asyncio.wait_for(investigate(request), timeout=90)
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=504, detail="Investigation timed out"
        ) from exc
    except Exception as exc:
        # In production, log the exception with a trace/correlation ID.
        raise HTTPException(
            status_code=502, detail="Agent investigation failed"
        ) from exc

    return IncidentResponse(report=report)
