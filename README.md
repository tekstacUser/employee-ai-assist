# Employee AI Assistant — On-Premise LLMOps Assessment

## 1. Project Contract

This repository is the **single source of truth** for the assessment. Every
sub-section of Coding Question 1 (and later coding questions) refers back to
the scenario, architecture, and naming conventions defined here. Do not rename
services, files, models, or tier labels — graders and the `cq1/` templates
assume the names below.

### 1.1 Scenario

You are the LLMOps engineer for a mid-size company's internal **Employee AI
Assistant** — a chat tool employees use to ask HR, IT, and company-policy
questions. For compliance reasons **no data may leave the company network**:
the entire stack (models, gateway, observability, app) runs inside a single
Linux VM via Docker Compose. There is no cloud provider, no external API, and
no internet-hosted model endpoint anywhere in the request path.

### 1.2 Architecture (fixed — do not change topology)

```
                ┌─────────────┐
  Employee  ──► │    Nginx    │  (reverse proxy, :8080)
                └──────┬──────┘
                       │
            ┌──────────┴───────────┐
            ▼                      ▼
     ┌─────────────┐        ┌─────────────┐
     │  Frontend    │        │  Backend     │  FastAPI, :8000
     │  (static)    │        │  (FastAPI)   │
     └─────────────┘        └──────┬───────┘
                                    │ OpenAI-compatible calls
                                    ▼
                          ┌──────────────────┐
                          │  LiteLLM Proxy    │  :4000
                          │  (routing layer)  │
                          └─────────┬─────────┘
                     success_callback│  fallback / load-balance
                     ┌───────────────┼───────────────┐
                     ▼               ▼               ▼
              ┌────────────┐  ┌────────────┐  ┌────────────┐
              │  Ollama     │  │  Ollama     │  │ PostgreSQL │
              │  llama3.2:3b │  │ qwen2.5:1.5b│  │ (app+auth) │
              └────────────┘  └────────────┘  └────────────┘
                     │
                     ▼
              ┌────────────┐     ┌────────────┐
              │  LangFuse   │ ──► │   Redis     │ (LangFuse cache/queue)
              │ (observ.)   │     └────────────┘
              └────────────┘
```

### 1.3 Services & Ports

| Service | Image / Build | Port (host) | Purpose |
|---|---|---|---|
| `nginx` | `nginx:alpine` | 8080 | Reverse proxy, single entry point |
| `frontend` | `./frontend` | (internal 80) | Static chat UI |
| `backend` | `./backend` | (internal 8000) | FastAPI app, calls LiteLLM |
| `litellm` | `ghcr.io/berriai/litellm` | 4000 | Routing, fallback, cost tracking |
| `ollama` | `ollama/ollama` | 11434 | Local model server (Llama 3.1 8B, Mistral) |
| `langfuse` | `langfuse/langfuse` | 3000 | LLM observability, traces, alerts |
| `postgres` | `postgres:16-alpine` | 5432 | LangFuse + app data store |
| `redis` | `redis:7-alpine` | 6379 | LangFuse cache / queue |

### 1.4 Routing Tiers (referenced throughout `cq1/`)

| Tier | Intended use | Model |
|---|---|---|
| **Simple** | FAQ-style, short lookups (e.g. "What's the WiFi password reset URL?") | `ollama/qwen2.5:1.5b` |
| **Standard** | Typical HR/IT questions needing some reasoning | `ollama/llama3.2:3b` |
| **Complex** | Multi-step policy interpretation, escalations | `ollama/llama3.2:3b` (worked example — see `litellm/config.yaml`) |

> **Note on model sizes:** this stack currently uses smaller models
> (`llama3.2:3b`, `qwen2.5:1.5b`) so it runs on modest VMs (8GB RAM /
> 3 vCPU). If you later run this on a larger VM (16GB+ RAM, 4+ vCPU), you
> can swap in `llama3.1:8b` and `mistral` by updating the two `model:`
> lines in `litellm/config.yaml` and re-pulling — no other files need to
> change.

### 1.5 Business Units (for cost/budget gaps)

`hr`, `it`, `finance` — each gets its own LiteLLM virtual key, budget, and
rpm limit (see `cq1/cost-model.md`).

### 1.6 Quick Start

```bash
cp .env.example .env
docker compose up -d
# Pull models into the running Ollama container (first run only, ~10 min):
docker exec -it ollama ollama pull llama3.2:3b
docker exec -it ollama ollama pull qwen2.5:1.5b
```

Then visit `http://localhost:8080` (chat UI), `http://localhost:4000` (LiteLLM
admin), and `http://localhost:3000` (LangFuse).

### 1.7 What Is Already Built vs. What You Must Complete

This repo is a **working skeleton**. The deployment topology, containers,
networking, backend, and frontend all run out of the box. What's missing is
the **LLMOps configuration layer** — routing rules, cost controls,
observability alerts, and the DR runbook — which is the subject of Coding
Question 1. Every gap is marked `# TODO (Gap N — see cq1/...)` in the
relevant file. Do not edit files outside the marked gaps unless a gap
explicitly asks you to add a new block.

### 1.8 Assessment Entry Point

Start with `cq1/topology.md` and `litellm/config.yaml`. The full gap list,
mark allocation, and adversarial DR scenarios are in `cq1/` — treat that
folder as the assessment brief; this README is architecture reference only.

Time budget: **50 minutes** for all of Coding Question 1 (35 marks total).
