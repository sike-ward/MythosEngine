"""
Notes & Folders routes for MythosEngine FastAPI server.

Endpoints
---------
GET    /notes                     — list notes (optional folder/tag filter)
GET    /notes/search              — full-text search
GET    /notes/folders             — list folders
POST   /notes/folders             — create folder
PUT    /notes/folders/{folder_id} — rename/update folder
DELETE /notes/folders/{folder_id} — delete folder
POST   /notes                     — create note
GET    /notes/{note_id}           — get note + content
PUT    /notes/{note_id}           — update note content/metadata
DELETE /notes/{note_id}           — delete note
POST   /notes/move                — move note to another folder
POST   /notes/{note_id}/tags      — add tag
DELETE /notes/{note_id}/tags/{tag} — remove tag
PUT    /notes/{note_id}/meta      — update arbitrary meta dict
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from MythosEngine.context.app_context import AppContext
from MythosEngine.models.note import Note
from MythosEngine.models.user import User
from server.dependencies import get_ctx, get_current_user

router = APIRouter(tags=["notes"])


class CreateNoteRequest(BaseModel):
    title: str
    content: str = ""
    folder_id: Optional[str] = None
    tags: List[str] = []
    meta: Dict[str, str] = {}


class UpdateNoteRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    meta: Optional[Dict[str, str]] = None


class CreateFolderRequest(BaseModel):
    name: str
    parent_id: Optional[str] = None


class UpdateFolderRequest(BaseModel):
    name: Optional[str] = None


class MoveNoteRequest(BaseModel):
    note_id: str
    dest_folder_id: Optional[str] = None


class AddTagRequest(BaseModel):
    tag: str


class UpdateMetaRequest(BaseModel):
    meta: Dict[str, str]


def _note_dict(note: Note) -> dict:
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "tags": note.tags,
        "folder_id": note.folder_id,
        "vault_id": note.vault_id,
        "owner_id": note.owner_id,
        "meta": note.meta,
        "links": note.links,
        "ai_summary": note.ai_summary,
        "created_at": note.created_at.isoformat() if note.created_at else None,
        "last_modified": note.last_modified.isoformat() if note.last_modified else None,
    }


# ── Folder routes ────────────────────────────────────────────────────────────


@router.get("/notes/folders")
def list_folders(
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
):
    folders = ctx.storage.list_folders()
    return {"folders": folders}


@router.post("/notes/folders", status_code=status.HTTP_201_CREATED)
def create_folder(
    body: CreateFolderRequest,
    ctx: AppContext = Depends(get_ctx),
    _current_user: User = Depends(get_current_user),
):
    path = body.name if not body.parent_id else f"{body.parent_id}/{body.name}"
    ctx.storage.create_folder(path)
    return {"path": path}


@router.put("/notes/folders/{folder_id:path}")
def update_folder(
    folder_id: str,
    body: UpdateFolderRequest,
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
):
    if body.name:
        parent = "/".join(folder_id.split("/")[:-1])
        dest = f"{parent}/{body.name}" if parent else body.name
        ctx.storage.move_folder(folder_id, dest)
        return {"path": dest}
    return {"path": folder_id}


@router.delete("/notes/folders/{folder_id:path}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: str,
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
):
    ctx.storage.delete_folder(folder_id)


# ── Note routes ──────────────────────────────────────────────────────────────


@router.get("/notes")
def list_notes(
    folder: str = Query(default=""),
    tag: str = Query(default=""),
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
):
    paths = ctx.storage.list_notes(folder)
    results = []
    for p in paths:
        try:
            meta = ctx.storage.get_note_metadata(p)
            entry = {
                "id": p,
                "title": p.split("/")[-1].removesuffix(".md"),
                "modified_date": meta.get("modified"),
                "created_date": meta.get("created"),
            }
            if tag:
                # Filter by tag: read note content only when needed
                try:
                    content = ctx.storage.read_note(p)
                    if tag.lower() not in content.lower():
                        continue
                except Exception:
                    continue
            results.append(entry)
        except Exception:
            results.append({"id": p, "title": p.split("/")[-1].removesuffix(".md")})
    return {"notes": results}


@router.get("/notes/search")
def search_notes(
    q: str = Query(..., min_length=1),
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
):
    found = ctx.storage.search_notes(q)
    return {"notes": [_note_dict(n) for n in found]}


@router.post("/notes", status_code=status.HTTP_201_CREATED)
def create_note(
    body: CreateNoteRequest,
    ctx: AppContext = Depends(get_ctx),
    current_user: User = Depends(get_current_user),
):
    note = ctx.notes.create_note(
        vault_id=getattr(ctx.config, "VAULT_PATH", ""),
        owner_id=current_user.id,
        title=body.title,
        content=body.content,
        folder_id=body.folder_id,
        tags=body.tags,
        meta=body.meta,
    )
    return _note_dict(note)


@router.get("/notes/{note_id:path}")
def get_note(
    note_id: str,
    ctx: AppContext = Depends(get_ctx),
    _user: User = Depends(get_current_user),
):
    # Try by UUID first, then by path
    note = ctx.notes.get_note(note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    return _note_dict(note)


@router.put("/notes/{note_id:path}")
def update_note(
    note_id: str,
    body: UpdateNoteRequest,
    ctx: AppContext = Depends(get_ctx),
    current_user: User = Depends(get_current_user),
):
    note = ctx.notes.get_note(note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    if body.title is not None:
        note.title = body.title
    if body.content is not None:
        note.content = body.content
    if body.tags is not None:
        note.tags = body.tags
    if body.meta is not None:
        note.meta.update(body.meta)
    try:
        ctx.notes.update_note(note, actor_id=current_user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return _note_dict(note)


@router.delete("/notes/{note_id:path}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: str,
    ctx: AppContext = Depends(get_ctx),
    current_user: User = Depends(get_current_user),
):
    note = ctx.notes.get_note(note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    try:
        ctx.notes.delete_note(note_id, actor_id=current_user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post("/notes/move")
def move_note(
    body: MoveNoteRequest,
    ctx: AppContext = Depends(get_ctx),
    current_user: User = Depends(get_current_user),
):
    note = ctx.notes.get_note(body.note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    dest_prefix = f"{body.dest_folder_id}/" if body.dest_folder_id else ""
    safe_title = note.title.replace("/", "_").replace("\\", "_")
    dest_path = f"{dest_prefix}{safe_title}.md"
    # Prefer the stored _path meta; fall back to note.id (the filesystem path for HybridStorage)
    src_path = note.meta.get("_path") or note.id
    ctx.storage.move_note(src_path, dest_path)
    note.folder_id = body.dest_folder_id
    note.meta["_path"] = dest_path
    try:
        ctx.notes.update_note(note, actor_id=current_user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return _note_dict(note)


@router.post("/notes/{note_id:path}/tags", status_code=status.HTTP_201_CREATED)
def add_tag(
    note_id: str,
    body: AddTagRequest,
    ctx: AppContext = Depends(get_ctx),
    current_user: User = Depends(get_current_user),
):
    note = ctx.notes.get_note(note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    if body.tag not in note.tags:
        note.tags.append(body.tag)
        try:
            ctx.notes.update_note(note, actor_id=current_user.id)
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return {"tags": note.tags}


@router.delete("/notes/{note_id:path}/tags/{tag}", status_code=status.HTTP_204_NO_CONTENT)
def remove_tag(
    note_id: str,
    tag: str,
    ctx: AppContext = Depends(get_ctx),
    current_user: User = Depends(get_current_user),
):
    note = ctx.notes.get_note(note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    note.tags = [t for t in note.tags if t != tag]
    try:
        ctx.notes.update_note(note, actor_id=current_user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.put("/notes/{note_id:path}/meta")
def update_meta(
    note_id: str,
    body: UpdateMetaRequest,
    ctx: AppContext = Depends(get_ctx),
    current_user: User = Depends(get_current_user),
):
    note = ctx.notes.get_note(note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    note.meta.update(body.meta)
    try:
        ctx.notes.update_note(note, actor_id=current_user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return {"meta": note.meta}
