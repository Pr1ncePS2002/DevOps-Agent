"""Multi-turn conversation engine for the DevOps AI assistant.

Flow per turn:
1. Load project context (stack, deployment, recent executions).
2. Load chat history from DB.
3. Build a rich system prompt that includes real project state.
4. Call the LLM.
5. Parse the response:
   - If it contains <<<DEPLOY_INTENT>>>…<<<END_INTENT>>> extract the intent
     and kick off the command pipeline to create a Plan.
   - Otherwise return plain text.
6. Persist both the user message and the assistant reply.
"""
from __future__ import annotations

import json
import re

import structlog

from app.persistence.repositories import (
    add_chat_message,
    create_plan,
    get_chat_history,
    get_chat_session,
    get_latest_deployment,
    get_project,
    list_executions_for_project,
)
from app.services.command_interpreter import build_deployment_plan, interpret_command_async
from app.services.prompts.conversation import CONVERSATION_SYSTEM_PROMPT

log = structlog.get_logger(__name__).bind(component="conversation_engine")

_INTENT_RE = re.compile(
    r"<<<DEPLOY_INTENT>>>(.*?)<<<END_INTENT>>>",
    re.DOTALL,
)


def _build_project_context(project, latest_deployment, recent_executions: list) -> str:
    """Render a text block summarising real-time project state."""
    lines = ["PROJECT CONTEXT (real-time):"]

    if project:
        lines.append(f"- Name: {project.name}")
        lines.append(f"- Stack: {project.detected_stack or 'unknown'}")
        lines.append(f"- Platform: {project.deployment_platform}")
        lkg = project.last_known_good_tag or "none"
        lines.append(f"- Last Known Good Tag: {lkg}")
    else:
        lines.append("- Project: unknown")

    if latest_deployment:
        cid = (latest_deployment.container_id or "")[:12] or "n/a"
        lines.append(
            f"- Current Deployment: container={cid} image={latest_deployment.image_tag or 'n/a'} "
            f"status={latest_deployment.status}"
        )
    else:
        lines.append("- Current Deployment: none")

    if recent_executions:
        lines.append("- Recent Executions (newest first):")
        for exc in recent_executions[:5]:
            ts = str(exc.created_at)[:19]
            lines.append(f"    [{ts}] status={exc.status}")
    else:
        lines.append("- Recent Executions: none")

    return "\n".join(lines)


def _build_messages_for_llm(history: list, user_message: str) -> list[dict]:
    """Convert DB chat history + new message into the LLM messages list."""
    messages = []
    for msg in history:
        if msg.role in {"user", "assistant"}:
            messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})
    return messages


async def _call_llm_conversational(system_prompt: str, messages: list[dict]) -> str:
    """Send a multi-turn conversation to the LLM and return raw text."""
    from app.services.llm.factory import get_llm_client

    client = get_llm_client()

    # Build a single user prompt that includes conversation history, since
    # BaseLLMClient only exposes system + user. For multi-turn we embed
    # prior turns in the user prompt body.
    if len(messages) == 1:
        user_prompt = messages[0]["content"]
    else:
        history_text = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in messages[:-1]
        )
        user_prompt = (
            f"Conversation so far:\n{history_text}\n\n"
            f"User: {messages[-1]['content']}"
        )

    return await client.complete(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.3)


async def _create_plan_from_intent(intent: dict, project, db_session) -> int | None:
    """Parse intent dict → create a Plan in DB and return its id."""
    if project is None:
        return None

    try:
        # Use the existing async interpreter to get the full parsed dict
        text = (
            f"{intent.get('action', 'deploy')} "
            f"{'v' + intent['version'] if intent.get('version') else ''} "
            f"to {', '.join(intent.get('environments', ['staging']))} "
            f"{'and ' + ' '.join(intent.get('post_steps', [])) if intent.get('post_steps') else ''}"
        ).strip()

        parsed = await interpret_command_async(text)

        # Override with the intent values since they come from structured LLM output
        parsed["action"] = intent.get("action", parsed["action"])
        if intent.get("version"):
            parsed["version"] = intent["version"]
        if intent.get("environments"):
            parsed["environments"] = intent["environments"]
        if intent.get("post_steps") is not None:
            parsed["post_steps"] = intent["post_steps"]

        repo_path = project.workspace_path or project.repo_path or ""
        default_port = 3000 if (project.detected_stack or "node") == "node" else 8000

        dp = build_deployment_plan(
            project_id=project.id or 0,
            repo_path=repo_path,
            detected_stack=project.detected_stack or "unknown",
            dockerfile_path=project.dockerfile_path,
            has_env_file=project.has_env_file,
            default_port=default_port,
            parsed=parsed,
        )

        plan = create_plan(
            db_session,
            project_id=project.id or 0,
            raw_command=text,
            action=parsed["action"],
            version=parsed.get("version"),
            environments=parsed["environments"],
            post_steps=parsed["post_steps"],
            warnings=dp["warnings"],
            detected_stack=dp["detected_stack"],
            dockerfile_path=dp["dockerfile_path"],
            image_tag=dp["image_tag"],
            ports=dp["ports"],
            env_injected=dp["env_injected"],
        )
        return plan.id

    except Exception as exc:
        log.warning("intent_plan_creation_failed", error=str(exc))
        return None


class ConversationEngine:
    """Stateless engine — all state is loaded from the DB on each call."""

    async def chat(
        self,
        *,
        session_id: int,
        user_message: str,
        db_session,
    ) -> dict:
        """Process one user turn and return the assistant response.

        Returns:
            {
                "response": str,
                "type": "text" | "plan_generated",
                "plan_id": int | None,
                "metadata": dict,
            }
        """
        log.info("chat_turn_start", session_id=session_id, msg_len=len(user_message))

        chat_session = get_chat_session(db_session, session_id)
        if chat_session is None:
            return {
                "response": "Session not found.",
                "type": "error",
                "plan_id": None,
                "metadata": {},
            }

        project = get_project(db_session, chat_session.project_id)
        latest_deployment = (
            get_latest_deployment(db_session, chat_session.project_id) if project else None
        )
        recent_executions = (
            list_executions_for_project(db_session, chat_session.project_id, limit=5)
            if project
            else []
        )

        project_ctx = _build_project_context(project, latest_deployment, recent_executions)
        system_prompt = f"{CONVERSATION_SYSTEM_PROMPT}\n\n{project_ctx}"

        history = get_chat_history(db_session, session_id, limit=40)
        messages = _build_messages_for_llm(history, user_message)

        # Persist the user message first
        add_chat_message(
            db_session,
            session_id=session_id,
            role="user",
            content=user_message,
            message_type="text",
        )

        # Call LLM
        try:
            raw_response = await _call_llm_conversational(system_prompt, messages)
        except Exception as exc:
            log.error("conversation_llm_failed", error=str(exc))
            error_msg = "I'm having trouble connecting to the AI service. Please try again."
            add_chat_message(
                db_session,
                session_id=session_id,
                role="assistant",
                content=error_msg,
                message_type="error",
            )
            return {"response": error_msg, "type": "error", "plan_id": None, "metadata": {}}

        # Parse DEPLOY_INTENT if present
        intent_match = _INTENT_RE.search(raw_response)
        plan_id: int | None = None
        response_type = "text"
        metadata: dict = {}

        if intent_match:
            try:
                intent = json.loads(intent_match.group(1).strip())
                plan_id = await _create_plan_from_intent(intent, project, db_session)
                response_type = "plan_generated"
                metadata = {"intent": intent, "plan_id": plan_id}
                log.info("deploy_intent_detected", action=intent.get("action"), plan_id=plan_id)
            except (json.JSONDecodeError, Exception) as exc:
                log.warning("intent_parse_failed", error=str(exc))

        # Strip the intent block from the visible response text
        clean_response = _INTENT_RE.sub("", raw_response).strip()
        if not clean_response:
            clean_response = "Plan created successfully. Review and approve it above."

        # Persist assistant message
        add_chat_message(
            db_session,
            session_id=session_id,
            role="assistant",
            content=clean_response,
            message_type="plan_preview" if plan_id else "text",
            metadata={"plan_id": plan_id} if plan_id else {},
        )

        log.info(
            "chat_turn_done",
            session_id=session_id,
            type=response_type,
            plan_id=plan_id,
        )

        return {
            "response": clean_response,
            "type": response_type,
            "plan_id": plan_id,
            "metadata": metadata,
        }
