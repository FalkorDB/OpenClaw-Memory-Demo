# 🧠 Mem0 + OpenClaw + FalkorDB Demo

Persistent **graph-structured memory** for AI coding assistants — powered by [Mem0](https://github.com/mem0ai/mem0) and [FalkorDB](https://falkordb.com).

Inspired by the [Mem0 × OpenClaw blog post](https://mem0.ai/blog/mem0-memory-for-openclaw) and built on the [mem0-falkordb plugin](https://github.com/FalkorDB/mem0-falkordb).

```
┌─────────────────┐     ┌──────────┐     ┌────────────────────────┐
│  Coding Agent    │────▶│   Mem0   │────▶│       FalkorDB         │
│  (OpenClaw-like) │◀────│  Memory  │◀────│  Graph Store per User  │
└─────────────────┘     └──────────┘     │  ┌────────┐ ┌───────┐  │
                                         │  │mem0_   │ │mem0_  │  │
  Auto-Recall: inject relevant           │  │ alice  │ │ bob   │  │
  memories every turn                    │  └────────┘ └───────┘  │
                                         └────────────────────────┘
  Auto-Capture: extract and store
  new facts after each response
```

## ✨ What This Demo Shows

| Feature | Description |
|---------|-------------|
| **Graph-structured memory** | Entities and relationships, not flat key-value pairs |
| **Per-user graph isolation** | Each developer gets their own FalkorDB graph — no `WHERE user_id=X` needed |
| **Memory evolution** | Preferences update intelligently (REST → GraphQL migration) |
| **Cross-session persistence** | Memory survives agent restarts and context compaction |
| **Interactive chat** | A coding assistant that remembers your tech stack and project context |

---

## 🚀 Quick Start (30 seconds)

### 1. Start FalkorDB

```bash
docker compose up -d
```

FalkorDB Browser is available at [http://localhost:3000](http://localhost:3000).

Or without Docker Compose:
```bash
docker run --rm -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest
```

### 2. Install dependencies

```bash
uv sync
```

Or with pip:
```bash
pip install mem0ai mem0-falkordb openai falkordb rich python-dotenv
```

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env` and set your **real** OpenAI API key:
```env
OPENAI_API_KEY=sk-proj-...
```

### 4. Run!

**Scripted demo** (5 automated scenes — great for presentations):
```bash
uv run python demo.py
```

**Interactive chatbot** (talk to a coding assistant with persistent memory):
```bash
uv run python chat.py
```

**Inspect graphs** (visualize the FalkorDB knowledge graph):
```bash
uv run python inspect_graphs.py
```

---

## 📂 Project Structure

```
├── config.py            # Shared config — reads .env, builds Mem0 config
├── demo.py              # Scripted demo — 5 automated scenes
├── chat.py              # Interactive coding assistant chatbot
├── inspect_graphs.py    # FalkorDB graph visualizer
├── docker-compose.yml   # One-command FalkorDB startup
├── .env.example         # Template for environment variables
└── pyproject.toml       # Python dependencies (uv-compatible)
```

---

## 🎬 Scripted Demo Scenes

Run `uv run python demo.py` to see all 5 scenes:

### Scene 1: Developer Onboarding 👩‍💻
Onboards 3 developers with distinct tech profiles:
- **Alice** — Python/Django backend, PostgreSQL, REST APIs, type hints + mypy
- **Bob** — TypeScript/React/Next.js full-stack, MongoDB, Tailwind CSS
- **Carol** — ML engineer, PyTorch + Hugging Face, Jupyter, AWS SageMaker

### Scene 2: Context-Aware Code Assistance 🔍
Queries each developer's memories — "what database?" gives different answers per user. Shows graph stats (nodes, relationships) for each isolated graph.

### Scene 3: Memory Evolution 🔄
Alice migrates from REST to GraphQL. Old preferences update intelligently — no duplication.

### Scene 4: Per-User Isolation Proof 🔒
Searches for "PyTorch" in Alice's graph → nothing. In Carol's graph → found. Architectural isolation, not filtering.

### Scene 5: Cross-Session Persistence 🔄
Creates a new Memory instance (simulates restart). Queries still return results — memory lives in FalkorDB, not in the context window.

---

## 💬 Interactive Chat Commands

Run `uv run python chat.py` and use these commands:

| Command | Description |
|---------|-------------|
| `/memories` | List all stored memories for current user |
| `/search <query>` | Semantic search across memories |
| `/forget <id>` | Delete a specific memory |
| `/graph` | Show FalkorDB graph stats (nodes & relationships) |
| `/user <id>` | Switch to a different developer persona |
| `/clear` | Clear chat session (memories persist) |
| `/help` | Show available commands |
| `/quit` | Exit the chatbot |

---

## ☁️ FalkorDB Cloud

To use [FalkorDB Cloud](https://app.falkordb.cloud) instead of Docker:

```env
FALKORDB_MODE=cloud
FALKORDB_HOST=your-instance.falkordb.cloud
FALKORDB_PORT=6379
FALKORDB_USERNAME=default
FALKORDB_PASSWORD=your-password
```

---

## 🔑 Key Takeaways

- **One graph per user** — leverages FalkorDB's native multi-graph support
- **No `WHERE user_id=X` everywhere** — isolation is architectural
- **Relationships captured** — not just flat facts, but entity connections
- **Drop a user = drop a graph** — `DELETE GRAPH mem0_alice`
- **Memory survives restarts** — stored in FalkorDB, not in the LLM context window

---

## 📚 Resources

- [Mem0 × OpenClaw Blog Post](https://mem0.ai/blog/mem0-memory-for-openclaw)
- [FalkorDB + Mem0 Docs](https://docs.falkordb.com/agentic-memory/mem0.html)
- [mem0-falkordb Plugin](https://github.com/FalkorDB/mem0-falkordb)
- [Mem0 Documentation](https://docs.mem0.ai)
- [FalkorDB Cloud (Free Tier)](https://app.falkordb.cloud)

---

## License

MIT
