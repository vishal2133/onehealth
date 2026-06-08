from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_doctor
from app.core.security import decode_access_token
from app.database import SessionLocal, get_db
from app.models import Conversation, Doctor, Message
from app.schemas.chat import ConversationResponse, MessageCreate, MessageResponse


router = APIRouter(prefix="/chat", tags=["chat"])


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, conversation_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[conversation_id].append(websocket)

    def disconnect(self, conversation_id: int, websocket: WebSocket) -> None:
        self.connections[conversation_id].remove(websocket)

    async def broadcast(self, conversation_id: int, payload: dict) -> None:
        for websocket in self.connections[conversation_id]:
            await websocket.send_json(payload)


manager = ConnectionManager()


def owned_conversation(db: Session, conversation_id: int, doctor_id: int) -> Conversation:
    conversation = db.scalar(
        select(Conversation)
        .options(joinedload(Conversation.patient))
        .where(Conversation.id == conversation_id, Conversation.doctor_id == doctor_id)
    )
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


def save_doctor_message(db: Session, conversation: Conversation, content: str) -> Message:
    message = Message(
        conversation_id=conversation.id,
        sender_type="doctor",
        sender_id=conversation.doctor_id,
        content=content.strip(),
        is_read=True,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
) -> list[ConversationResponse]:
    conversations = db.scalars(
        select(Conversation)
        .options(joinedload(Conversation.patient), joinedload(Conversation.messages))
        .where(Conversation.doctor_id == doctor.id)
    ).unique().all()
    output = []
    for conversation in conversations:
        last = conversation.messages[-1] if conversation.messages else None
        unread = sum(1 for message in conversation.messages if message.sender_type == "patient" and not message.is_read)
        initials = "".join(part[0] for part in conversation.patient.name.split()[:2]).upper()
        output.append(
            ConversationResponse(
                id=conversation.id,
                patient_id=conversation.patient_id,
                patient_name=conversation.patient.name,
                category=conversation.patient.service,
                avatar=initials,
                last_message=last.content if last else None,
                last_time=last.sent_at if last else None,
                unread=unread,
            )
        )
    return sorted(output, key=lambda item: item.last_time.timestamp() if item.last_time else 0, reverse=True)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def get_messages(
    conversation_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
) -> list[Message]:
    owned_conversation(db, conversation_id, doctor.id)
    messages = db.scalars(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.sent_at)
    ).all()
    for message in messages:
        if message.sender_type == "patient":
            message.is_read = True
    db.commit()
    return list(messages)


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def post_message(
    conversation_id: int,
    payload: MessageCreate,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
) -> Message:
    conversation = owned_conversation(db, conversation_id, doctor.id)
    message = save_doctor_message(db, conversation, payload.content)
    await manager.broadcast(conversation_id, MessageResponse.model_validate(message).model_dump(mode="json", by_alias=True))
    return message


@router.websocket("/ws/{conversation_id}")
async def chat_websocket(websocket: WebSocket, conversation_id: int, token: str = Query(...)) -> None:
    try:
        doctor_id = decode_access_token(token)
    except (InvalidTokenError, KeyError, ValueError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    with SessionLocal() as db:
        try:
            conversation = owned_conversation(db, conversation_id, doctor_id)
        except HTTPException:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await manager.connect(conversation_id, websocket)
        try:
            while True:
                payload = MessageCreate.model_validate(await websocket.receive_json())
                message = save_doctor_message(db, conversation, payload.content)
                await manager.broadcast(
                    conversation_id,
                    MessageResponse.model_validate(message).model_dump(mode="json", by_alias=True),
                )
        except WebSocketDisconnect:
            manager.disconnect(conversation_id, websocket)
