# AI DevOps Commander — Next Steps Roadmap

> **Purpose**: Comprehensive task list with copy-paste Claude Code prompts for each feature.
> **Primary LLM**: Gemini 2.5 Pro (`GEMINI_API_KEY` already configured)
> **Project Goal**: College/University evaluation — impress evaluators with real AI, polished UX, and production-grade architecture.
> **Generated**: 2026-04-06

---

## How to Use This Document

Each task below includes:

1. **What & Why** — what you're building and why it matters for evaluation
2. **Files Affected** — exact paths that will be created or modified
3. **Claude Code Prompt** — copy-paste into Claude Code terminal to execute
4. **Verification** — how to confirm it worked
5. **Estimated Effort** — rough time to complete

> **Tip**: Work through phases in order. Each phase builds on the previous one.

---

## Phase 1: Real LLM Integration (Replace Keyword Matching with Gemini 2.5 Pro)

This is the single most impactful change. Right now `command_interpreter.py` uses regex — the "AI" in your project name doesn't exist yet. This phase makes it real.

---

### Task 1.1 — Create LLM Service Abstraction Layer ✅ DONE (2026-04-06)

**What & Why**: Build a unified LLM client that supports Gemini (primary) with OpenAI fallback. This shows evaluators you designed for provider-agnostic AI integration.

**Files Affected**:
- `apps/backend/app/services/llm/__init__.py` (new)
- `apps/backend/app/services/llm/base.py` (new)
- `apps/backend/app/services/llm/gemini_client.py` (new)
- `apps/backend/app/services/llm/openai_client.py` (new)
- `apps/backend/app/services/llm/factory.py` (new)
- `apps/backend/requirements.txt` (add google-generativeai)

**Claude Code Prompt**:
```
Read these files first to understand the existing architecture:
- apps/backend/app/common/settings.py
- apps/backend/app/services/command_interpreter.py
- apps/backend/app/services/rag_advisor.py
- apps/backend/requirements.txt

Then create a new LLM service layer at apps/backend/app/services/llm/ with these files:

1. base.py — Abstract base class `BaseLLMClient` with methods:
   - async def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str
   - async def complete_json(self, system_prompt: str, user_prompt: str, schema: dict) -> dict
     (calls complete() then parses JSON from the response, with retry on parse failure)

2. gemini_client.py — Implements BaseLLMClient using google-generativeai SDK:
   - Uses settings.gemini_api_key and model "gemini-2.5-pro"
   - Update settings.py to change gemini_model default to "gemini-2.5-pro"
   - Uses structured JSON output mode when available
   - Includes proper error handling with structlog logging
   - Has a fallback to extract JSON from markdown code blocks if the model wraps it

3. openai_client.py — Implements BaseLLMClient using httpx (not openai SDK, keep deps light):
   - Uses settings.openai_api_key, settings.openai_base_url, settings.openai_model
   - Uses response_format: { type: "json_object" } for JSON completions
   - Proper error handling

4. factory.py — Factory function `get_llm_client() -> BaseLLMClient`:
   - Reads settings.llm_provider ("GEMINI" | "OPENAI" | "OLLAMA")
   - Returns appropriate client
   - Raises clear error if API key is missing

5. __init__.py — Exports get_llm_client and BaseLLMClient

Also add "google-generativeai>=0.8.0" to requirements.txt.

Use structlog for all logging (import from app.common.logging). Follow the existing code style: type hints everywhere, __future__ annotations at top of each file.
```

**Verification**: `python -c "from app.services.llm import get_llm_client; print('OK')"`

**Estimated Effort**: 1-2 hours

---

### Task 1.2 — AI-Powered Command Interpreter ✅ DONE (2026-04-06)

**What & Why**: Replace the regex-based `interpret_command()` with Gemini-powered natural language understanding. This is the core differentiator — users can now say anything and get a structured plan.

**Files Affected**:
- `apps/backend/app/services/command_interpreter.py` (rewrite)
- `apps/backend/app/services/prompts/__init__.py` (new)
- `apps/backend/app/services/prompts/command_parser.py` (new)
- `apps/backend/tests/test_command_interpreter.py` (update)

**Claude Code Prompt**:
```
Read these files to understand the current system:
- apps/backend/app/services/command_interpreter.py (current regex-based parser)
- apps/backend/app/services/llm/factory.py (LLM client we just created)
- apps/backend/app/api/routes/commands.py (how interpret_command is called)
- apps/backend/app/persistence/models.py (Plan model schema)
- apps/backend/tests/test_command_interpreter.py (existing tests)

Now refactor the command interpreter to use LLM:

1. Create apps/backend/app/services/prompts/command_parser.py with:
   - COMMAND_PARSER_SYSTEM_PROMPT: A carefully crafted system prompt that instructs the LLM to act as a DevOps command interpreter. It should:
     - Accept natural language deployment commands
     - Output ONLY valid JSON matching this schema:
       {
         "action": "deploy" | "rollback" | "restart" | "scale" | "status" | "logs" | "unknown",
         "version": "string or null",
         "environments": ["staging", "production", "dev"],
         "post_steps": ["run_tests", "smoke_tests", "notify_team", "generate_report"],
         "confidence": 0.0-1.0,
         "reasoning": "one-line explanation of what the AI understood",
         "suggested_confirmation": "human-readable summary like: Deploy v2.1 to staging, then run smoke tests"
       }
     - Include 5-6 few-shot examples covering: simple deploy, versioned deploy, multi-env deploy, rollback, ambiguous command
     - Handle edge cases: gibberish input (action=unknown, low confidence), partial info, slang like "ship it", "push to prod", "yeet to staging"

2. Rewrite apps/backend/app/services/command_interpreter.py:
   - Rename old interpret_command to interpret_command_deterministic (keep as fallback)
   - New async function: async def interpret_command_llm(text: str) -> dict
     - Uses get_llm_client().complete_json() with the system prompt
     - Returns the parsed dict
     - If confidence < 0.4, falls back to deterministic parser with a warning
   - New wrapper: async def interpret_command(text: str) -> dict
     - Tries LLM first
     - Falls back to deterministic on any exception
     - Adds "interpretation_method": "llm" or "deterministic" to the result
   - Keep build_deployment_plan unchanged (it already works with the dict output)

3. Update apps/backend/app/api/routes/commands.py:
   - Make parse_command async (add async def)
   - Await the new async interpret_command
   - Add "confidence", "reasoning", "suggested_confirmation" to PlanPreviewResponse model

4. Update tests:
   - Keep all existing deterministic tests (they test the fallback)
   - Add new tests that mock the LLM client to verify:
     - LLM response is properly parsed
     - Fallback triggers on LLM failure
     - Low confidence triggers fallback
     - confidence/reasoning fields are present in response

IMPORTANT: The LLM-based function must be async. The deterministic fallback stays synchronous. The wrapper handles both.
Do NOT remove any existing functionality — only add to it.
```

**Verification**: Start the API, send a POST to `/api/commands/parse` with `{"project_id": 1, "text": "ship the latest hotfix to prod and run smoke tests"}` — you should get back a structured plan with confidence score and reasoning.

**Estimated Effort**: 2-3 hours

---

### Task 1.3 — AI-Powered RAG Advisor (Replace Stub) ✅ DONE (2026-04-06)

**What & Why**: The current `rag_advisor.py` is a hardcoded stub. Replace it with an LLM-powered plan validator that gives intelligent warnings. Evaluators will see the AI actually reasoning about deployment safety.

**Files Affected**:
- `apps/backend/app/services/rag_advisor.py` (rewrite)
- `apps/backend/app/services/prompts/plan_advisor.py` (new)

**Claude Code Prompt**:
```
Read these files:
- apps/backend/app/services/rag_advisor.py (current stub)
- apps/backend/app/services/command_interpreter.py (the new LLM version)
- apps/backend/app/services/llm/factory.py
- apps/backend/app/api/routes/commands.py (where advise_plan is called)
- apps/backend/app/persistence/models.py

Rewrite the RAG advisor to use LLM intelligence:

1. Create apps/backend/app/services/prompts/plan_advisor.py with:
   - PLAN_ADVISOR_SYSTEM_PROMPT: A system prompt that makes the LLM act as a senior DevOps engineer reviewing a deployment plan. It should:
     - Receive the deployment plan details (action, environments, version, time of day, post_steps)
     - Return JSON: { "risk_level": "low"|"medium"|"high"|"critical", "risk_score": 0-100, "warnings": ["string"], "recommendations": ["string"], "approval_recommendation": "auto_approve"|"manual_review"|"block" }
     - Consider: production deploys = higher risk, no tests = warning, Friday deploys = warning, missing version = risk, rollback without reason = flag
     - Include 3-4 few-shot examples

2. Rewrite apps/backend/app/services/rag_advisor.py:
   - Keep the old advise_plan as advise_plan_deterministic (fallback)
   - New async function: async def advise_plan_llm(*, action, environments, post_steps, version, project_name) -> dict
     - Returns { "risk_level", "risk_score", "warnings": list[str], "recommendations": list[str] }
   - Wrapper: async def advise_plan(...) -> list[str]
     - Tries LLM, extracts warnings + recommendations into a flat list
     - Falls back to deterministic on failure

3. Update commands.py route:
   - Make the advise_plan call awaited
   - Add risk_level and risk_score to PlanPreviewResponse

This gives evaluators a visible "Risk Score: 72/100 — HIGH" in the UI, which is very impressive for a demo.
```

**Verification**: Parse a command like "deploy to production with no tests" — should return high risk score with warnings about missing tests and production environment.

**Estimated Effort**: 1-2 hours

---

### Task 1.4 — Display AI Intelligence in Frontend ✅ DONE (2026-04-07)

**What & Why**: All the AI work is invisible if the frontend doesn't show it. Add confidence scores, risk levels, AI reasoning to the plan preview.

**Files Affected**:
- `apps/frontend/lib/types.ts` (update PlanPreview type)
- `apps/frontend/components/command-console.tsx` (update UI)

**Claude Code Prompt**:
```
Read these files:
- apps/frontend/lib/types.ts
- apps/frontend/components/command-console.tsx
- apps/frontend/components/status-pill.tsx
- apps/frontend/lib/api.ts

Update the frontend to display AI-powered plan intelligence:

1. Update lib/types.ts — add to PlanPreview interface:
   - confidence: number (0-1)
   - reasoning: string
   - suggested_confirmation: string
   - risk_level: "low" | "medium" | "high" | "critical"
   - risk_score: number (0-100)

2. Update components/command-console.tsx plan preview section:
   - After the action title, show AI confidence: "AI Confidence: 94%" with a colored badge (green >80%, yellow 50-80%, red <50%)
   - Show the AI reasoning in italic text: "AI understood: Deploy version 2.1 to staging environment, then execute smoke tests"
   - Show the suggested_confirmation as a human-readable summary above the approve button
   - Add a risk score visual: circular progress indicator or colored bar showing risk_score/100
     - Color: green (0-30), yellow (31-60), orange (61-80), red (81-100)
     - Label: "Risk: LOW", "Risk: MEDIUM", "Risk: HIGH", "Risk: CRITICAL"
   - Show recommendations as green-tinted info cards (not warnings, different from the yellow warning cards)

3. Add a subtle "Powered by Gemini 2.5 Pro" label at the bottom of the command console panel. Small, muted text.

Keep the existing dark theme styling. Use Tailwind classes consistent with the rest of the app. The risk visualization should be visually striking — this is the thing evaluators will remember.
```

**Verification**: Start frontend, type a command, see confidence score, risk level, and AI reasoning displayed.

**Estimated Effort**: 1-2 hours

---

## Phase 2: Pipeline-as-Conversation (Multi-Turn Chat Interface)

This transforms your tool from "type a command, get a plan" into "have a conversation with your DevOps AI." This is the feature that no competitor does well, and it's the most impressive thing for a demo.

---

### Task 2.1 — Conversation Backend (Chat Session API)

**What & Why**: Create a conversation engine that maintains context across multiple messages. Users can ask questions, refine plans, and execute — all in a flowing chat.

**Files Affected**:
- `apps/backend/app/persistence/models.py` (add ChatSession, ChatMessage models)
- `apps/backend/app/persistence/repositories.py` (add chat CRUD)
- `apps/backend/app/services/conversation_engine.py` (new)
- `apps/backend/app/services/prompts/conversation.py` (new)
- `apps/backend/app/api/routes/chat.py` (new)
- `apps/backend/app/api/router.py` (register new route)

**Claude Code Prompt**:
```
Read these files to understand the existing patterns:
- apps/backend/app/persistence/models.py
- apps/backend/app/persistence/repositories.py
- apps/backend/app/persistence/db.py
- apps/backend/app/api/router.py
- apps/backend/app/api/routes/commands.py
- apps/backend/app/services/llm/factory.py
- apps/backend/app/services/command_interpreter.py
- apps/backend/app/common/settings.py

Build a conversation-based DevOps chat system:

1. Add new models to apps/backend/app/persistence/models.py:

   class ChatSession(SQLModel, table=True):
       id: int | None = Field(default=None, primary_key=True)
       project_id: int
       created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
       last_message_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
       status: str = "active"  # active | archived

   class ChatMessage(SQLModel, table=True):
       id: int | None = Field(default=None, primary_key=True)
       session_id: int
       role: str  # "user" | "assistant" | "system"
       content: str
       message_type: str = "text"  # "text" | "plan_preview" | "execution_status" | "error"
       metadata_json: str = "{}"  # JSON string for structured data (plan_id, execution_id, etc.)
       created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

2. Add to repositories.py:
   - create_chat_session(session, project_id) -> ChatSession
   - get_chat_session(session, session_id) -> ChatSession | None
   - add_chat_message(session, session_id, role, content, message_type, metadata) -> ChatMessage
   - get_chat_history(session, session_id, limit=50) -> list[ChatMessage]
   - list_chat_sessions(session, project_id) -> list[ChatSession]

3. Create apps/backend/app/services/prompts/conversation.py:
   - CONVERSATION_SYSTEM_PROMPT: A system prompt that makes the LLM act as an AI DevOps assistant in a multi-turn conversation. The prompt should:
     - Tell the AI it's a DevOps deployment assistant
     - It can: explain deployment status, parse deploy/rollback commands, answer questions about the project, suggest best practices
     - When it detects a deployment intent, it should respond with a special JSON block embedded in its response:
       <<<DEPLOY_INTENT>>>{"action": "deploy", "version": "...", "environments": [...], "post_steps": [...]}<<<END_INTENT>>>
     - Otherwise it responds in natural conversational text
     - It should remember context from the conversation (the full history is provided)
     - It should ask clarifying questions if the command is ambiguous: "You want to deploy to production — did you mean with or without running tests first?"

4. Create apps/backend/app/services/conversation_engine.py:
   - class ConversationEngine:
     - async def chat(self, session_id: int, user_message: str, db_session) -> dict:
       - Loads chat history from DB
       - Builds the LLM prompt with conversation context
       - Sends to LLM
       - Parses the response:
         - If contains <<<DEPLOY_INTENT>>>, extracts the intent and also creates a Plan via the existing command pipeline
         - Otherwise, returns plain text response
       - Saves both user message and assistant response to DB
       - Returns: { "response": str, "type": "text"|"plan_generated", "plan_id": int|None, "metadata": dict }

5. Create apps/backend/app/api/routes/chat.py:
   - POST /chat/sessions — create new chat session for a project
   - GET /chat/sessions/{session_id}/messages — get chat history
   - POST /chat/sessions/{session_id}/message — send a message
     Request: { "content": str }
     Response: { "response": str, "type": str, "plan_id": int|None }
   - GET /chat/sessions — list sessions for a project (query param: project_id)

6. Register the chat router in apps/backend/app/api/router.py with prefix "/chat"

Make sure to update the init_db() in db.py to create the new tables.
Use structlog logging throughout. Follow existing patterns for error handling and session management.
```

**Verification**: `curl -X POST http://localhost:3001/api/chat/sessions -H "Content-Type: application/json" -d '{"project_id": 1}'` then send messages to the session.

**Estimated Effort**: 3-4 hours

---

### Task 2.2 — Chat UI Component (Frontend)

**What & Why**: Build a beautiful chat interface that replaces (or supplements) the command console. This is the hero feature for your demo.

**Files Affected**:
- `apps/frontend/components/chat/` (new directory)
- `apps/frontend/components/chat/chat-panel.tsx` (new)
- `apps/frontend/components/chat/chat-message.tsx` (new)
- `apps/frontend/components/chat/chat-input.tsx` (new)
- `apps/frontend/components/chat/plan-card.tsx` (new)
- `apps/frontend/components/dashboard-client.tsx` (update to include chat)
- `apps/frontend/lib/api.ts` (add chat API functions)
- `apps/frontend/lib/types.ts` (add chat types)

**Claude Code Prompt**:
```
Read these files:
- apps/frontend/components/dashboard-client.tsx
- apps/frontend/components/command-console.tsx
- apps/frontend/lib/api.ts
- apps/frontend/lib/types.ts
- apps/frontend/lib/config.ts
- apps/frontend/app/layout.tsx (for theme/styling reference)

Build a chat-based DevOps interface:

1. Add types to lib/types.ts:
   interface ChatSession { id: number; project_id: number; created_at: string; status: string }
   interface ChatMessage { id: number; session_id: number; role: "user" | "assistant" | "system"; content: string; message_type: "text" | "plan_preview" | "execution_status" | "error"; metadata: Record<string, any>; created_at: string }
   interface ChatResponse { response: string; type: "text" | "plan_generated"; plan_id: number | null; metadata: Record<string, any> }

2. Add to lib/api.ts:
   - createChatSession(projectId: number): Promise<ChatSession>
   - getChatMessages(sessionId: number): Promise<ChatMessage[]>
   - sendChatMessage(sessionId: number, content: string): Promise<ChatResponse>
   - listChatSessions(projectId: number): Promise<ChatSession[]>

3. Create components/chat/chat-message.tsx:
   - Renders a single chat message bubble
   - User messages: right-aligned, accent-colored background
   - Assistant messages: left-aligned, dark surface background
   - If message_type is "plan_preview", render an inline PlanCard component
   - If message_type is "execution_status", show a status indicator
   - Show timestamp in small muted text
   - Animate entrance with a subtle fade-in

4. Create components/chat/plan-card.tsx:
   - An inline card that appears within chat messages when a plan is generated
   - Shows: action, version, environments, risk score badge, confidence
   - Has an "Approve & Execute" button right in the chat
   - When clicked, calls approvePlan() and shows execution status inline

5. Create components/chat/chat-input.tsx:
   - Text input with send button at the bottom
   - Supports Enter to send, Shift+Enter for newline
   - Shows typing indicator when waiting for AI response
   - Placeholder text: "Ask me to deploy, check status, or explain anything..."
   - Subtle pulse animation on the send button when there's text

6. Create components/chat/chat-panel.tsx:
   - Main container that assembles the chat
   - Auto-scrolls to bottom on new messages
   - Shows a "New Conversation" button at top
   - Shows project selector (dropdown of registered projects)
   - Has a header: "DevOps AI Assistant" with a subtle AI icon
   - Manages state: session creation, message sending, polling for updates

7. Update components/dashboard-client.tsx:
   - Add a tab system at the top: "Command Console" | "AI Chat" (default to AI Chat)
   - Render ChatPanel when AI Chat tab is active
   - Render existing CommandConsole when Command Console tab is active
   - The tab should be styled with the existing dark theme

Style everything with Tailwind, matching the existing dark theme (bg-surface-800, border-white/5, text-white/90 etc.). Make the chat feel modern — think ChatGPT-style but with the military/mission-control aesthetic your app already has. Messages should have a glass-morphism effect. The chat panel should take the full width of the main content area.
```

**Verification**: Start frontend, see new "AI Chat" tab, open a conversation, type "what can you help me with?" and get an AI response.

**Estimated Effort**: 3-4 hours

---

### Task 2.3 — Conversation Context Awareness (Project Status in Chat)

**What & Why**: Make the AI chat aware of the actual project state — running containers, last deployment, health status. So users can ask "what's running right now?" and get a real answer.

**Files Affected**:
- `apps/backend/app/services/conversation_engine.py` (enhance)
- `apps/backend/app/services/prompts/conversation.py` (enhance)

**Claude Code Prompt**:
```
Read these files:
- apps/backend/app/services/conversation_engine.py
- apps/backend/app/services/prompts/conversation.py
- apps/backend/app/persistence/repositories.py (look at get_latest_deployment, list_executions_for_project)
- apps/backend/app/persistence/models.py (Project, Deployment, Execution models)
- apps/backend/app/adapters/docker_adapter.py (container_health_check)

Enhance the conversation engine to be aware of project state:

1. Update conversation_engine.py — in the chat() method, before calling the LLM:
   - Load the project details (name, detected_stack, last_known_good_tag, deployment_platform)
   - Load the latest deployment (container_id, image_tag, status)
   - Load the last 5 executions (status, created_at, log summary)
   - Build a "project context" block that gets injected into the system prompt:
     ```
     PROJECT CONTEXT:
     - Name: {name}
     - Stack: {detected_stack}
     - Current Deployment: {container_id[:12]} running {image_tag}, status: {status}
     - Last Known Good: {last_known_good_tag}
     - Recent Executions: [list of last 5 with status and date]
     - Platform: {deployment_platform}
     ```

2. Update the CONVERSATION_SYSTEM_PROMPT in prompts/conversation.py:
   - Add instructions that the AI has access to real-time project context
   - It should use this context to answer questions like:
     "What's running?" → "Your project X is running container abc123 with image devops-cmd-1:2.1, deployed 2 hours ago. Status: healthy."
     "When was the last deploy?" → Answer from execution history
     "Should I rollback?" → Check if current deployment is healthy, advise based on status
   - The AI should proactively warn if it notices issues in the context (e.g., deployment status is "failed")

This makes the conversation feel intelligent and grounded in reality, not just a generic chatbot.
```

**Verification**: In chat, ask "what's currently deployed?" — should get a real answer based on your project state.

**Estimated Effort**: 1-2 hours

---

## Phase 3: Docker Compose One-Command Setup

This is critical for evaluation — if evaluators can't start your project easily, they can't be impressed by it.

---

### Task 3.1 — Create docker-compose.yml for Full Stack

**What & Why**: Single `docker-compose up` brings up everything — backend, frontend, Redis, worker. This is table stakes for any serious project.

**Files Affected**:
- `docker-compose.yml` (new, at project root)
- `apps/backend/Dockerfile` (new)
- `apps/frontend/Dockerfile` (new)
- `.env.example` (update with Docker defaults)

**Claude Code Prompt**:
```
Read these files to understand the full stack:
- apps/backend/requirements.txt
- apps/backend/app/main.py
- apps/backend/app/common/settings.py
- apps/frontend/package.json
- apps/frontend/next.config.js
- .env.example

Create a complete Docker Compose setup:

1. Create apps/backend/Dockerfile:
   - Base: python:3.11-slim
   - Install system deps needed for docker SDK support (but we'll mount the host Docker socket)
   - Copy requirements.txt, pip install
   - Copy app code
   - Expose 3001
   - CMD: uvicorn app.main:app --host 0.0.0.0 --port 3001

2. Create apps/frontend/Dockerfile:
   - Multi-stage build:
     Stage 1 (builder): node:18-alpine, install deps, build Next.js
     Stage 2 (runner): node:18-alpine, copy built output, expose 3000
   - Use standalone output mode for Next.js

3. Create docker-compose.yml at project root with services:
   - redis:
     image: redis:7-alpine
     ports: 6379:6379
     healthcheck: redis-cli ping

   - backend:
     build: ./apps/backend
     ports: 3001:3001
     depends_on: redis (healthy)
     env_file: .env
     environment:
       - REDIS_URL=redis://redis:6379
       - DATABASE_URL=sqlite:///./data/dev.db
       - HOST=0.0.0.0
     volumes:
       - ./apps/backend/data:/app/data
       - /var/run/docker.sock:/var/run/docker.sock (for Docker-in-Docker deployments)
     healthcheck: curl -f http://localhost:3001/health

   - worker:
     build: ./apps/backend
     command: python -m app.queue.worker
     depends_on: redis (healthy), backend (healthy)
     env_file: .env
     environment:
       - REDIS_URL=redis://redis:6379
       - DATABASE_URL=sqlite:///./data/dev.db
     volumes:
       - ./apps/backend/data:/app/data
       - /var/run/docker.sock:/var/run/docker.sock

   - frontend:
     build: ./apps/frontend
     ports: 3000:3000
     depends_on: backend (healthy)
     environment:
       - NEXT_PUBLIC_API_BASE_URL=http://backend:3001

4. Update .env.example:
   - Add comments for Docker Compose usage
   - Set sensible defaults that work out of the box with compose
   - Add: # For Docker Compose, these are auto-configured: REDIS_URL, DATABASE_URL, HOST

5. Add a .dockerignore file at project root:
   - node_modules, __pycache__, .git, data/*.db, .env (not .env.example), *.pyc, .next

Also update the next.config.js to add output: "standalone" for Docker optimization.

Make sure the docker-compose.yml is clean, well-commented, and uses proper healthchecks with depends_on conditions.
```

**Verification**: `docker-compose up --build` — all 4 services start, frontend accessible at localhost:3000.

**Estimated Effort**: 2-3 hours

---

### Task 3.2 — Create Quick-Start Script

**What & Why**: A single script that handles everything — checks prerequisites, creates .env, and starts the stack.

**Files Affected**:
- `scripts/quick-start.sh` (new)
- `scripts/quick-start.cmd` (new, Windows)
- `README.md` (update)

**Claude Code Prompt**:
```
Read:
- docker-compose.yml
- .env.example
- README.md
- docs/LOCAL-USER-GUIDE.md

Create quick-start scripts and update README:

1. Create scripts/quick-start.sh (Linux/Mac):
   #!/bin/bash
   - Print a banner: "AI DevOps Commander - Quick Start"
   - Check prerequisites: docker --version, docker-compose --version (or docker compose)
   - If .env doesn't exist, copy .env.example to .env and prompt user to add API keys
   - Check if GEMINI_API_KEY is set in .env, warn if empty
   - Run docker-compose up --build -d
   - Wait for health checks (poll localhost:3001/health)
   - Print success message with URLs:
     "Dashboard: http://localhost:3000"
     "API: http://localhost:3001"
     "API Docs: http://localhost:3001/docs"
   - Make it executable (chmod +x)

2. Create scripts/quick-start.cmd (Windows):
   - Same logic adapted for Windows batch/PowerShell

3. Rewrite README.md:
   - Keep it concise but impressive
   - Hero section: project name, one-line description, key badges (Python, TypeScript, Docker, Gemini)
   - "Quick Start" section: just 3 lines:
     git clone <repo>
     cd ai-devops-commander
     ./scripts/quick-start.sh
   - "What It Does" section: 4-5 bullet points of key features
   - "Architecture" section: simple ASCII diagram
   - "Tech Stack" section: table of technologies
   - "Screenshots" section: placeholder for screenshots
   - "Development" section: how to run without Docker
   - Don't make it too long — evaluators skim READMEs
```

**Verification**: Run `./scripts/quick-start.sh` on a fresh clone — should get to a working dashboard.

**Estimated Effort**: 1-2 hours

---

## Phase 4: CI/CD Pipeline (For the Project Itself)

Your DevOps tool should have its own DevOps. This demonstrates you practice what you preach.

---

### Task 4.1 — GitHub Actions CI Pipeline

**What & Why**: Automated testing, linting, and build verification on every push. Essential for credibility.

**Files Affected**:
- `.github/workflows/ci.yml` (new)
- `.github/workflows/docker-build.yml` (new)

**Claude Code Prompt**:
```
Read:
- apps/backend/pyproject.toml (ruff config)
- apps/backend/requirements.txt
- apps/frontend/package.json
- docker-compose.yml

Create GitHub Actions CI workflows:

1. Create .github/workflows/ci.yml:
   name: CI Pipeline
   on: push (main, develop), pull_request (main)

   Jobs:

   a) backend-lint-test:
      - runs-on: ubuntu-latest
      - python 3.11
      - Install requirements.txt + ruff
      - Run: ruff check apps/backend/
      - Run: pytest apps/backend/tests/ -v --tb=short
      - Cache pip dependencies

   b) frontend-lint-build:
      - runs-on: ubuntu-latest
      - node 18
      - cd apps/frontend && npm ci
      - Run: npx tsc --noEmit (type checking)
      - Run: npm run build
      - Cache node_modules

   c) docker-compose-test:
      - runs-on: ubuntu-latest
      - needs: [backend-lint-test, frontend-lint-build]
      - Copy .env.example to .env
      - Set dummy API keys in .env
      - Run: docker-compose build (verify images build)
      - Run: docker-compose up -d
      - Wait for health: curl --retry 10 --retry-delay 5 http://localhost:3001/health
      - Run: docker-compose down

2. Create .github/workflows/docker-build.yml:
   name: Docker Build
   on: push to main (tags: v*)

   Jobs:
   - Build and tag Docker images
   - (Don't push to registry — just verify they build)

Use proper caching for pip and npm. Add status badges for the CI workflow. Make the workflow names descriptive.
```

**Verification**: Push to GitHub, check Actions tab — all jobs should pass green.

**Estimated Effort**: 1-2 hours

---

## Phase 5: Advanced Features (Impressive for Evaluators)

These are the "wow factor" features that go beyond expectations.

---

### Task 5.1 — Real-Time Deployment Streaming via WebSocket

**What & Why**: Replace the polling-based log viewer with real-time WebSocket streaming. Evaluators see logs appear instantly during deployment — very impressive in a live demo.

**Files Affected**:
- `apps/backend/app/api/routes/ws.py` (new)
- `apps/backend/app/api/router.py` (update)
- `apps/backend/app/services/orchestrator.py` (update to broadcast)
- `apps/frontend/components/live-log.tsx` (update)
- `apps/frontend/lib/ws.ts` (new)

**Claude Code Prompt**:
```
Read:
- apps/backend/app/api/router.py
- apps/backend/app/services/orchestrator.py (look at _log function)
- apps/backend/app/persistence/repositories.py (append_execution_log)
- apps/frontend/components/live-log.tsx
- apps/frontend/components/command-console.tsx (polling logic)
- apps/frontend/lib/api.ts

Add real-time WebSocket log streaming:

1. Create apps/backend/app/api/routes/ws.py:
   - Use FastAPI WebSocket support
   - WebSocket endpoint: /ws/executions/{execution_id}/logs
   - On connect: send all existing log lines
   - Then subscribe to new log lines and send them as they arrive
   - Use an in-memory pub/sub mechanism:
     - Create a simple ConnectionManager class with:
       - active_connections: dict[int, list[WebSocket]] (execution_id -> connections)
       - async def connect(execution_id, websocket)
       - async def disconnect(execution_id, websocket)
       - async def broadcast(execution_id, message: str)
     - Singleton instance: manager = ConnectionManager()

2. Update apps/backend/app/services/orchestrator.py:
   - Import the connection manager
   - In the _log() function, after appending to DB, also broadcast via WebSocket:
     asyncio.get_event_loop().call_soon_threadsafe(
         asyncio.create_task, manager.broadcast(execution.id, msg)
     )
   - Handle the case where there's no event loop (worker process) gracefully

3. Register the WebSocket route in router.py

4. Create apps/frontend/lib/ws.ts:
   - export function connectToExecutionLogs(executionId: number, onMessage: (line: string) => void): WebSocket
   - Handles reconnection with exponential backoff
   - Auto-closes on component unmount

5. Update apps/frontend/components/live-log.tsx:
   - Accept an optional executionId prop
   - When executionId is provided, connect via WebSocket instead of polling
   - Show a green "Live" indicator when WebSocket is connected
   - Smooth scroll animation when new lines arrive
   - Keep polling as fallback if WebSocket fails

This is a huge UX improvement — logs stream in real-time like a real CI/CD tool.
```

**Verification**: Start a deployment, watch logs appear line-by-line in real-time without page refresh.

**Estimated Effort**: 2-3 hours

---

### Task 5.2 — Deployment History Timeline with Analytics

**What & Why**: A visual timeline of all deployments with success/failure rates, average deploy time, and trends. Evaluators love dashboards with data visualization.

**Files Affected**:
- `apps/backend/app/api/routes/analytics.py` (new)
- `apps/frontend/components/sections/analytics-panel.tsx` (new)
- `apps/frontend/components/dashboard-client.tsx` (update)

**Claude Code Prompt**:
```
Read:
- apps/backend/app/persistence/models.py (Execution, Deployment models)
- apps/backend/app/persistence/repositories.py
- apps/frontend/components/sections/history-panel.tsx
- apps/frontend/components/sections/stat-grid.tsx
- apps/frontend/components/dashboard-client.tsx

Build deployment analytics:

1. Create apps/backend/app/api/routes/analytics.py:
   - GET /analytics/summary — returns:
     {
       "total_deployments": int,
       "success_rate": float (percentage),
       "average_deploy_time_seconds": float,
       "rollback_count": int,
       "deployments_by_day": [{"date": "2025-02-20", "count": 3, "successes": 2, "failures": 1}],
       "deployments_by_environment": {"staging": 10, "production": 5},
       "most_deployed_project": {"name": str, "count": int},
       "recent_activity": [{"timestamp": str, "action": str, "project": str, "status": str, "duration_seconds": float}]
     }
   - Query the Execution and Deployment tables
   - Register in router.py

2. Create apps/frontend/components/sections/analytics-panel.tsx:
   - A beautiful analytics dashboard section with:

   a) Stat cards row (reuse/extend stat-grid pattern):
      - Total Deployments (number with trend arrow)
      - Success Rate (percentage with green/red coloring)
      - Avg Deploy Time (formatted as "2m 34s")
      - Rollbacks (count)

   b) Deployment timeline chart:
      - Use recharts (already available) BarChart
      - X-axis: dates, Y-axis: deployment count
      - Stacked bars: green (success) / red (failure)
      - Last 30 days

   c) Environment breakdown:
      - Horizontal bar chart or donut chart showing deploys per environment

   d) Recent activity feed:
      - Scrollable list of recent deployments with status pills
      - Shows: project name, action, environment, time ago, duration, status

3. Update dashboard-client.tsx:
   - Add an "Analytics" section below or as a tab alongside the existing panels
   - Fetch analytics data on mount

Style with the existing dark theme. Make the charts glow slightly (add subtle gradients or shadows to chart elements) to match the mission-control aesthetic.
```

**Verification**: Dashboard shows deployment charts with real data from your test deployments.

**Estimated Effort**: 2-3 hours

---

### Task 5.3 — AI-Generated Deployment Summary & Post-Mortem

**What & Why**: After every deployment (success or failure), the AI generates a human-readable summary. On failures, it generates a mini post-mortem with root cause analysis. This is very impressive for evaluators.

**Files Affected**:
- `apps/backend/app/services/prompts/post_mortem.py` (new)
- `apps/backend/app/services/summary_generator.py` (new)
- `apps/backend/app/services/orchestrator.py` (update)
- `apps/backend/app/api/routes/executions.py` (update)
- `apps/frontend/components/execution-summary.tsx` (new)

**Claude Code Prompt**:
```
Read:
- apps/backend/app/services/orchestrator.py
- apps/backend/app/services/llm/factory.py
- apps/backend/app/api/routes/executions.py
- apps/backend/app/persistence/models.py

Create AI-generated deployment summaries:

1. Create apps/backend/app/services/prompts/post_mortem.py:
   - DEPLOYMENT_SUMMARY_PROMPT: System prompt for generating deployment summaries
     - Takes: execution logs, status, duration, project info
     - For SUCCESS: generates a concise summary (what was deployed, where, key events)
     - For FAILURE: generates a post-mortem with:
       - Timeline of events
       - Probable root cause (analyzed from logs)
       - Impact assessment
       - Recommended next steps
     - Output JSON: { "summary": str, "key_events": [str], "root_cause": str|null, "recommendations": [str], "severity": "info"|"warning"|"critical" }

2. Create apps/backend/app/services/summary_generator.py:
   - async def generate_deployment_summary(execution_id: int, db_session) -> dict:
     - Load execution with logs
     - Load related project and deployment info
     - Call LLM with the execution data
     - Save summary to execution metadata (add a summary_json column or use existing fields)
     - Return the summary dict
   - async def generate_deployment_summary_safe(execution_id, db_session) -> dict | None:
     - Wraps above in try/except, returns None on failure

3. Update orchestrator.py:
   - After deployment completes (success or failure), call generate_deployment_summary_safe
   - Store the result in the execution log as a final entry

4. Update executions.py API route:
   - Add GET /executions/{id}/summary endpoint
   - Returns the AI-generated summary
   - If not yet generated, trigger generation on-demand

5. Create apps/frontend/components/execution-summary.tsx:
   - Renders the AI summary in a card
   - For success: green-tinted card with summary and key events
   - For failure: red-tinted card with root cause, timeline, and recommendations
   - Show a "Generated by AI" badge
   - Display in the execution detail view or after the live log

This feature alone will impress evaluators — it shows the AI isn't just parsing commands but actively analyzing outcomes.
```

**Verification**: Complete a deployment, then view the execution — see an AI-generated summary with key events and analysis.

**Estimated Effort**: 2-3 hours

---

### Task 5.4 — Interactive Demo Mode with Guided Walkthrough

**What & Why**: For your university evaluation, you'll likely demo this live. A guided walkthrough that explains each feature while the evaluator clicks through it is invaluable.

**Files Affected**:
- `apps/frontend/components/onboarding/guided-tour.tsx` (new)
- `apps/frontend/components/onboarding/tour-steps.ts` (new)
- `apps/frontend/components/dashboard-client.tsx` (update)
- `apps/backend/app/api/routes/demo.py` (enhance)

**Claude Code Prompt**:
```
Read:
- apps/frontend/components/dashboard-client.tsx
- apps/frontend/components/demo-button.tsx
- apps/backend/app/api/routes/demo.py
- apps/frontend/lib/api.ts

Create an interactive guided demo:

1. Create apps/frontend/components/onboarding/tour-steps.ts:
   - Export TOUR_STEPS array, each step has:
     { id, target (CSS selector), title, description, position (top/bottom/left/right) }
   - Steps:
     a) "Welcome" — targets the hero banner, explains what the tool does
     b) "Register a Project" — targets the project panel, explains registration
     c) "AI Chat" — targets the chat tab, explains conversational deployment
     d) "Command Console" — targets the command textarea, explains NL commands
     e) "Plan Preview" — targets the preview panel, explains AI confidence and risk
     f) "Approve & Execute" — targets the approve button, explains safety gates
     g) "Live Logs" — targets the log area, explains real-time streaming
     h) "Analytics" — targets analytics section, explains deployment history
     i) "You're Ready!" — final step with congratulations

2. Create apps/frontend/components/onboarding/guided-tour.tsx:
   - A floating tooltip/spotlight component that:
     - Highlights the target element (dim everything else with an overlay)
     - Shows the tooltip near the target with title and description
     - Has "Next", "Previous", "Skip Tour" buttons
     - Shows step count: "Step 3 of 9"
     - Animates between steps smoothly
     - Saves "tour completed" in component state (not localStorage since we can't use it)
   - Trigger: Show automatically on first load, or via a "Start Tour" button in the header

3. Update dashboard-client.tsx:
   - Add a "Take a Tour" button in the top-right area
   - Render GuidedTour component
   - Pass the tour steps

4. Enhance apps/backend/app/api/routes/demo.py:
   - POST /demo/setup-full — creates a complete demo environment:
     - Registers 2-3 sample projects (Node.js, Python)
     - Creates a few fake execution records with varied statuses
     - Creates a chat session with pre-populated messages showing a sample conversation
     - Returns all created IDs
   - This makes it so the evaluator sees a populated dashboard immediately

Style the tour overlay with a semi-transparent dark backdrop, a glowing border around the highlighted element, and smooth transitions. Keep it professional, not gamified.
```

**Verification**: Click "Take a Tour" — see a step-by-step guided walkthrough highlighting each feature.

**Estimated Effort**: 2-3 hours

---

## Phase 6: Production Polish

---

### Task 6.1 — Error Boundaries & Loading States

**Claude Code Prompt**:
```
Read all components in apps/frontend/components/ and identify every place where:
1. API calls are made without proper loading states
2. Errors are caught but not displayed well
3. Components could crash on null/undefined data

Then:
1. Create apps/frontend/components/ui/error-boundary.tsx — React error boundary with retry button
2. Create apps/frontend/components/ui/skeleton-loader.tsx — skeleton loading placeholders matching each major component's shape
3. Add loading skeletons to: dashboard-client, command-console, chat-panel, analytics-panel, history-panel
4. Add error boundaries around each major section
5. Add empty states: "No projects yet — register one to get started", "No deployments yet", "No chat history"

These should use the existing dark theme styling. Skeleton loaders should pulse with a subtle animation.
```

**Estimated Effort**: 2-3 hours

---

### Task 6.2 — API Documentation with Swagger Enhancements

**Claude Code Prompt**:
```
Read:
- apps/backend/app/main.py
- apps/backend/app/api/routes/*.py (all route files)

Enhance the FastAPI auto-generated documentation:

1. Update main.py create_app():
   - Add description, contact, license_info to FastAPI constructor
   - Add tags_metadata for grouping endpoints:
     - "Commands" — NL command parsing and plan generation
     - "Chat" — Conversational AI interface
     - "Projects" — Project registration and management
     - "Executions" — Deployment execution and monitoring
     - "Analytics" — Deployment metrics and history
     - "Demo" — Demo setup and sample data

2. Update each route file:
   - Add docstrings to every endpoint function
   - Add response_model for all endpoints
   - Add example request/response bodies using Field(example=...) or Config.schema_extra
   - Add proper HTTP status codes for error responses
   - Add tags=["CategoryName"] to each router

3. Add a Pydantic model for every response that currently returns a plain dict

The /docs page should look professional and be self-documenting. This is important if evaluators check the API docs.
```

**Estimated Effort**: 2-3 hours

---

### Task 6.3 — Comprehensive Test Suite

**Claude Code Prompt**:
```
Read:
- apps/backend/tests/ (all test files)
- apps/backend/app/services/llm/ (the new LLM layer)
- apps/backend/app/services/conversation_engine.py
- apps/backend/app/services/summary_generator.py
- apps/backend/app/api/routes/chat.py
- apps/backend/app/api/routes/analytics.py

Write comprehensive tests for all new features:

1. tests/test_llm_service.py:
   - Test factory returns correct client based on settings
   - Test Gemini client handles API errors gracefully
   - Test JSON parsing with malformed responses
   - Test fallback behavior
   - Mock the actual API calls (don't make real ones in tests)

2. tests/test_conversation_engine.py:
   - Test chat session creation and message storage
   - Test conversation context is properly built
   - Test deploy intent extraction from LLM responses
   - Test that LLM failure doesn't crash the chat
   - Mock LLM responses

3. tests/test_summary_generator.py:
   - Test success summary generation
   - Test failure post-mortem generation
   - Test graceful handling of LLM failure

4. tests/test_chat_routes.py:
   - Test POST /chat/sessions creates session
   - Test POST /chat/sessions/{id}/message returns response
   - Test GET /chat/sessions/{id}/messages returns history
   - Test 404 for non-existent session

5. tests/test_analytics_routes.py:
   - Test GET /analytics/summary with no data
   - Test GET /analytics/summary with mock execution data
   - Test calculations (success rate, average time)

6. Update tests/conftest.py:
   - Add fixtures for chat sessions, messages
   - Add a mock LLM client fixture that returns predictable responses

Target: 90%+ coverage on new code. Use pytest markers to separate fast unit tests from slower integration tests.
```

**Estimated Effort**: 3-4 hours

---

## Phase 7: Bonus Features (If Time Permits)

---

### Task 7.1 — Slack/Discord Notification Integration

**Claude Code Prompt**:
```
Read:
- apps/backend/app/services/orchestrator.py
- apps/backend/app/common/settings.py

Add webhook-based notifications:

1. Add to settings.py:
   - slack_webhook_url: str | None = None
   - discord_webhook_url: str | None = None
   - notification_enabled: bool = False

2. Create apps/backend/app/services/notifier.py:
   - async def notify_deployment(status, project_name, environment, version, summary, url=None):
     - If slack_webhook_url is set, POST a rich Slack message block:
       - Title: ":rocket: Deployment Succeeded" or ":x: Deployment Failed"
       - Fields: Project, Environment, Version, Duration
       - Color: green or red
     - If discord_webhook_url is set, POST a Discord embed
     - Log notification send (or failure) via structlog
   - Make it fire-and-forget (don't block deployment on notification)

3. Call notify_deployment from orchestrator.py after deployment completes

4. Add settings to .env.example with comments explaining setup

This shows real-world integration capability without requiring complex OAuth.
```

**Estimated Effort**: 1-2 hours

---

### Task 7.2 — Kubernetes Deployment Support (Conceptual + Basic)

**Claude Code Prompt**:
```
Read:
- apps/backend/app/services/deployers/base.py
- apps/backend/app/services/deployers/local.py
- apps/backend/app/services/deployers/vercel.py

Add a Kubernetes deployer:

1. Create apps/backend/app/services/deployers/kubernetes.py:
   - class KubernetesDeployer(BaseDeployer):
   - Uses the kubernetes Python client library
   - Implements:
     - validate_config() — check for kubeconfig or in-cluster config
     - deploy() — update a Deployment's image tag (rolling update)
     - status() — check rollout status
     - rollback() — rollback to previous revision
   - Add "kubernetes" to requirements.txt

2. Update apps/backend/app/services/deployers/__init__.py:
   - Add "kubernetes" to the deployer factory

3. Add settings:
   - k8s_namespace: str = "default"
   - k8s_deployment_name: str | None = None
   - k8s_kubeconfig_path: str | None = None

This demonstrates the extensibility of your deployer pattern. Even if evaluators don't test it live, the code shows you designed for scale.
```

**Estimated Effort**: 2-3 hours

---

## Summary & Recommended Order

| Priority | Task | Phase | Impact | Effort |
|----------|------|-------|--------|--------|
| 1 | LLM Service Abstraction | 1.1 | Foundation | 1-2h |
| 2 | AI Command Interpreter | 1.2 | Core Feature | 2-3h |
| 3 | AI RAG Advisor | 1.3 | Core Feature | 1-2h |
| 4 | Frontend AI Display | 1.4 | UX | 1-2h |
| 5 | Docker Compose Setup | 3.1 | Critical for Demo | 2-3h |
| 6 | Quick-Start Script | 3.2 | Critical for Demo | 1-2h |
| 7 | Chat Backend | 2.1 | Hero Feature | 3-4h |
| 8 | Chat Frontend | 2.2 | Hero Feature | 3-4h |
| 9 | Context-Aware Chat | 2.3 | Hero Feature | 1-2h |
| 10 | WebSocket Streaming | 5.1 | Wow Factor | 2-3h |
| 11 | Analytics Dashboard | 5.2 | Wow Factor | 2-3h |
| 12 | AI Post-Mortems | 5.3 | Wow Factor | 2-3h |
| 13 | GitHub Actions CI | 4.1 | Credibility | 1-2h |
| 14 | Guided Tour | 5.4 | Demo Polish | 2-3h |
| 15 | Error Boundaries | 6.1 | Polish | 2-3h |
| 16 | API Docs Enhancement | 6.2 | Polish | 2-3h |
| 17 | Comprehensive Tests | 6.3 | Academic Credit | 3-4h |
| 18 | Slack/Discord Notifications | 7.1 | Bonus | 1-2h |
| 19 | Kubernetes Deployer | 7.2 | Bonus | 2-3h |

**Total Estimated Effort**: ~35-50 hours

**Minimum Viable Demo** (Tasks 1-6): ~10-14 hours — gets you real AI + easy startup
**Impressive Demo** (Tasks 1-12): ~22-30 hours — adds chat, streaming, analytics
**Full Implementation** (All tasks): ~35-50 hours — complete professional product

---

## Architecture After All Phases

```
┌───────────────────────────────────────────────────────────┐
│                    Next.js Frontend                        │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌────────────┐  │
│  │ AI Chat  │ │ Command  │ │ Analytics │ │  Guided    │  │
│  │ Panel    │ │ Console  │ │ Dashboard │ │  Tour      │  │
│  └────┬─────┘ └────┬─────┘ └─────┬─────┘ └────────────┘  │
│       │ WebSocket   │ REST        │ REST                   │
└───────┼─────────────┼─────────────┼───────────────────────┘
        │             │             │
┌───────┼─────────────┼─────────────┼───────────────────────┐
│       ▼             ▼             ▼   FastAPI Backend      │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐                  │
│  │ Chat API │ │ Commands │ │ Analytics │                  │
│  │ /chat/*  │ │ /parse   │ │ /summary  │                  │
│  └────┬─────┘ └────┬─────┘ └─────┬─────┘                  │
│       │             │             │                         │
│  ┌────▼─────────────▼─────────────▼─────┐                  │
│  │        Service Layer                  │                  │
│  │  ┌────────────────┐ ┌──────────────┐ │                  │
│  │  │ Conversation   │ │ Command      │ │                  │
│  │  │ Engine         │ │ Interpreter  │ │                  │
│  │  └───────┬────────┘ └──────┬───────┘ │                  │
│  │          │                  │          │                  │
│  │  ┌───────▼──────────────────▼───────┐ │                  │
│  │  │  LLM Abstraction Layer           │ │                  │
│  │  │  (Gemini 2.5 Pro + OpenAI)       │ │                  │
│  │  └──────────────────────────────────┘ │                  │
│  │                                       │                  │
│  │  ┌─────────┐ ┌──────────┐ ┌────────┐ │                  │
│  │  │ RAG     │ │ Summary  │ │Notifier│ │                  │
│  │  │ Advisor │ │ Generator│ │(Slack) │ │                  │
│  │  └─────────┘ └──────────┘ └────────┘ │                  │
│  └───────────────────────────────────────┘                  │
│                                                             │
│  ┌─────────────────────────────────────────┐                │
│  │  Deployers (Strategy Pattern)           │                │
│  │  Docker | Vercel | Render | Kubernetes  │                │
│  └─────────────────────────────────────────┘                │
│                                                             │
│  ┌────────┐  ┌───────┐  ┌──────────┐                       │
│  │ SQLite │  │ Redis │  │ RQ Worker│                       │
│  └────────┘  └───────┘  └──────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

---

*Good luck with the evaluation, Prince. Build it phase by phase, and demo it with confidence.*
