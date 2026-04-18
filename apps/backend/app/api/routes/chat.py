"""Chat / conversation API routes.

POST /chat/sessions              — create a new chat session for a project
GET  /chat/sessions              — list sessions (query param: project_id)
GET  /chat/sessions/{id}/messages — get message history
POST /chat/sessions/{id}/message  — send a user message, get AI reply
"""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.persistence.db import session_scope
from app.persistence.repositories import (
    create_chat_session,
    get_chat_history,
    get_chat_session,
    list_chat_sessions,
)
from app.services.conversation_engine import ConversationEngine

router = APIRouter()

_engine = ConversationEngine()


# ── Request / Response schemas ────────────────────────────────────────────────


class CreateSessionRequest(BaseModel):
    project_id: int


class ChatMessageSchema(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    message_type: str
    metadata: dict
    created_at: str


class ChatSessionSchema(BaseModel):
    id: int
    project_id: int
    created_at: str
    last_message_at: str
    status: str


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


class ChatResponse(BaseModel):
    response: str
    type: str  # "text" | "plan_generated" | "error"
    plan_id: int | None
    metadata: dict


# ── Routes ───────────────────────────────────────────────────────────────────


@router.post("/sessions", response_model=ChatSessionSchema)
def create_session(payload: CreateSessionRequest) -> ChatSessionSchema:
    with session_scope() as session:
        chat_session = create_chat_session(session, payload.project_id)
        return ChatSessionSchema(
            id=chat_session.id or 0,
            project_id=chat_session.project_id,
            created_at=chat_session.created_at,
            last_message_at=chat_session.last_message_at,
            status=chat_session.status,
        )


@router.get("/sessions", response_model=list[ChatSessionSchema])
def list_sessions(project_id: int) -> list[ChatSessionSchema]:
    with session_scope() as session:
        sessions = list_chat_sessions(session, project_id)
        return [
            ChatSessionSchema(
                id=s.id or 0,
                project_id=s.project_id,
                created_at=s.created_at,
                last_message_at=s.last_message_at,
                status=s.status,
            )
            for s in sessions
        ]


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageSchema])
def get_messages(session_id: int) -> list[ChatMessageSchema]:
    with session_scope() as session:
        chat_session = get_chat_session(session, session_id)
        if chat_session is None:
            raise HTTPException(status_code=404, detail="Chat session not found")

        messages = get_chat_history(session, session_id)
        return [
            ChatMessageSchema(
                id=m.id or 0,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                message_type=m.message_type,
                metadata=_safe_json(m.metadata_json),
                created_at=m.created_at,
            )
            for m in messages
        ]


@router.post("/sessions/{session_id}/message", response_model=ChatResponse)
async def send_message(session_id: int, payload: SendMessageRequest) -> ChatResponse:
    with session_scope() as session:
        chat_session = get_chat_session(session, session_id)
        if chat_session is None:
            raise HTTPException(status_code=404, detail="Chat session not found")

        result = await _engine.chat(
            session_id=session_id,
            user_message=payload.content,
            db_session=session,
        )

        return ChatResponse(
            response=result["response"],
            type=result["type"],
            plan_id=result["plan_id"],
            metadata=result["metadata"],
        )


# ── Helpers ───────────────────────────────────────────────────────────────────


def _safe_json(text: str) -> dict:
    try:
        return json.loads(text or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}
