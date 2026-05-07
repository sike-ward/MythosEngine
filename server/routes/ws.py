from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect

from MythosEngine.context.app_context import AppContext
from server.auth_utils import decode_jwt
from server.deps import get_ctx
from server.realtime import hub
from server.vault_access import resolve_vault

router = APIRouter()


@router.websocket("/ws")
async def websocket_events(
    websocket: WebSocket,
    token: str = Query(...),
    vault_id: str = Query(...),
    ctx: AppContext = Depends(get_ctx),
):
    try:
        payload = decode_jwt(token)
    except HTTPException:
        await websocket.close(code=4401)
        return
    user = ctx.users.get_user(payload.get("sub", ""))
    if not user:
        await websocket.close(code=4401)
        return

    try:
        vault = resolve_vault(ctx, user, vault_id)
    except HTTPException:
        await websocket.close(code=4403)
        return

    await hub.connect(vault.id, user.id, user.username, websocket)
    try:
        while True:
            message = await websocket.receive_json()
            event_type = message.get("type")
            if event_type == "editing.start":
                await hub.set_editing(
                    vault.id,
                    note_id=message.get("note_id", ""),
                    user_id=user.id,
                    username=user.username,
                    cursor=message.get("cursor"),
                    active=True,
                )
            elif event_type == "editing.stop":
                await hub.set_editing(
                    vault.id,
                    note_id=message.get("note_id", ""),
                    user_id=user.id,
                    username=user.username,
                    active=False,
                )
            elif event_type == "cursor.move":
                await hub.set_editing(
                    vault.id,
                    note_id=message.get("note_id", ""),
                    user_id=user.id,
                    username=user.username,
                    cursor=message.get("cursor"),
                    active=True,
                )
            else:
                await websocket.send_json({"type": "ack", "received": event_type})
    except WebSocketDisconnect:
        await hub.disconnect(vault.id, user.id, websocket)
