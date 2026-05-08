import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import SectionHeader from '@/components/SectionHeader';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Input from '@/components/Input';
import FolderTree from '@/components/browse/FolderTree';
import NoteEditor from '@/components/browse/NoteEditor';
import TagPanel from '@/components/browse/TagPanel';
import MetaPanel from '@/components/browse/MetaPanel';
import PermissionsPanel from '@/components/browse/PermissionsPanel';
import { SkeletonLine } from '@/components/Skeleton';
import { notes, folders, ai, groups, users, isRateLimitError, RATE_LIMIT_MSG } from '@/api';
import { useVault } from '@/context/VaultContext';
import { useRealtime } from '@/context/RealtimeContext';

// ════════════════════════════════════════════════════════════════════════════
// Browse — Full vault browser (thin orchestrator)
// ════════════════════════════════════════════════════════════════════════════

export default function Browse({ user }) {
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const { activeVaultId } = useVault();
  const { editing, lastEvent, startEditing, updateCursor, stopEditing } = useRealtime();

  // ── Selection & navigation ───────────────────────────────────────────────
  const [selectedNoteId, setSelectedNoteId] = useState(null);
  const [activeFolder, setActiveFolder] = useState(null);
  const [expandedFolders, setExpandedFolders] = useState(new Set());

  // ── Editing ──────────────────────────────────────────────────────────────
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');

  // ── Search ───────────────────────────────────────────────────────────────
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searchHistory, setSearchHistory] = useState([]);
  const searchTimeout = useRef(null);

  // ── Tag filter ───────────────────────────────────────────────────────────
  const [tagFilter, setTagFilter] = useState('');

  // ── New tag input ────────────────────────────────────────────────────────
  const [newTag, setNewTag] = useState('');

  // ── Create note/folder dialogs ───────────────────────────────────────────
  const [showCreateNote, setShowCreateNote] = useState(false);
  const [newNoteTitle, setNewNoteTitle] = useState('');
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');

  // ── Move note ────────────────────────────────────────────────────────────
  const [showMoveDialog, setShowMoveDialog] = useState(false);

  // ── Metadata editing ─────────────────────────────────────────────────────
  const [showMetaEditor, setShowMetaEditor] = useState(false);
  const [metaKey, setMetaKey] = useState('');
  const [metaValue, setMetaValue] = useState('');

  // ── AI state ─────────────────────────────────────────────────────────────
  const [proposedLinks, setProposedLinks] = useState([]);
  const [summaryResult, setSummaryResult] = useState('');
  const canManagePermissions = (user?.roles || []).includes('admin');

  // ════════════════════════════════════════════════════════════════════════
  // React Query data fetching
  // ════════════════════════════════════════════════════════════════════════

  const { data: allFolders = [], isLoading: foldersLoading } = useQuery({
    queryKey: ['folders', activeVaultId],
    queryFn: () => folders.list(activeVaultId),
    enabled: !!activeVaultId,
  });

  const { data: allNotes = [], isLoading: notesLoading } = useQuery({
    queryKey: ['notes', activeVaultId],
    queryFn: () => notes.list('', '', activeVaultId),
    enabled: !!activeVaultId,
  });

  const { data: groupList = [] } = useQuery({
    queryKey: ['groups'],
    queryFn: groups.list,
    enabled: canManagePermissions,
  });

  const { data: userList = [] } = useQuery({
    queryKey: ['users'],
    queryFn: users.list,
    enabled: canManagePermissions,
  });

  const { data: selectedNote, isLoading: noteLoading } = useQuery({
    queryKey: ['note', selectedNoteId],
    queryFn: () => notes.get(selectedNoteId),
    enabled: !!selectedNoteId,
  });

  const loading = foldersLoading || notesLoading;

  // Sync edit state when note loads
  useEffect(() => {
    if (selectedNote && !isEditing) {
      setEditTitle(selectedNote.title);
      setEditContent(selectedNote.content || '');
    }
  }, [selectedNote]);

  // Clear AI state when note changes
  useEffect(() => {
    setProposedLinks([]);
    setSummaryResult('');
  }, [selectedNoteId]);

  // Auto-select note from URL query param
  useEffect(() => {
    const noteId = searchParams.get('note');
    if (noteId) setSelectedNoteId(noteId);
  }, [searchParams]);

  useEffect(() => {
    if (lastEvent?.type === 'note.saved' && lastEvent.vault_id === activeVaultId) {
      invalidateAll();
    }
  }, [lastEvent, activeVaultId]);

  useEffect(() => () => {
    if (selectedNoteId) stopEditing(selectedNoteId);
  }, [selectedNoteId]);

  // ── Ctrl+S to save ───────────────────────────────────────────────────────
  useEffect(() => {
    const handler = (e) => {
      if (e.ctrlKey && e.key === 's' && isEditing) {
        e.preventDefault();
        handleSave();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isEditing, editTitle, editContent, selectedNoteId]);

  // ── Search (debounced) ───────────────────────────────────────────────────
  useEffect(() => {
    if (!activeVaultId) {
      setSearchResults(null);
      return;
    }
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(async () => {
      try {
        const data = await notes.search(searchQuery, { vault_id: activeVaultId });
        setSearchResults(data.items || []);
        // Push to history (deduplicate, keep last 10)
        setSearchHistory((prev) => {
          const deduped = prev.filter((q) => q !== searchQuery);
          return [searchQuery, ...deduped].slice(0, 10);
        });
      } catch {
        setSearchResults([]);
      }
    }, 300);
    return () => clearTimeout(searchTimeout.current);
  }, [searchQuery, activeVaultId]);

  // ════════════════════════════════════════════════════════════════════════
  // Derived data
  // ════════════════════════════════════════════════════════════════════════

  const allTags = [...new Set(allNotes.flatMap((n) => n.tags || []))].sort();

  const displayNotes = (() => {
    if (searchResults) return searchResults;
    let list = allNotes;
    if (activeFolder) list = list.filter((n) => n.folder_id === activeFolder);
    if (tagFilter) list = list.filter((n) => (n.tags || []).some((t) => t.toLowerCase() === tagFilter.toLowerCase()));
    return list;
  })();

  const notesByFolder = {};
  allNotes.forEach((n) => {
    const fid = n.folder_id || '__unfiled__';
    if (!notesByFolder[fid]) notesByFolder[fid] = [];
    notesByFolder[fid].push(n);
  });
  const unfiledNotes = notesByFolder['__unfiled__'] || [];

  const wordCount = (text) => text ? text.trim().split(/\s+/).filter(Boolean).length : 0;
  const editingPresence = editing.find((item) => item.note_id === selectedNoteId && item.user_id !== user?.id);
  const permissionSubjects = new Set([user?.id, ...(user?.groups || [])].filter(Boolean));
  const permissionRank = { read: 1, write: 2 };
  const notePermissionRole = selectedNote
    ? [...permissionSubjects]
        .map((subject) => selectedNote.permissions?.[subject])
        .filter(Boolean)
        .sort((left, right) => (permissionRank[right] || 0) - (permissionRank[left] || 0))[0] || null
    : null;
  const canEdit =
    !!selectedNote &&
    !editingPresence &&
    (
      selectedNote.owner_id === user?.id ||
      notePermissionRole === 'write' ||
      (user?.roles || []).includes('admin') ||
      (user?.roles || []).includes('gm')
    );

  // ════════════════════════════════════════════════════════════════════════
  // Mutations
  // ════════════════════════════════════════════════════════════════════════

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ['notes', activeVaultId] });
    queryClient.invalidateQueries({ queryKey: ['folders', activeVaultId] });
    if (selectedNoteId) queryClient.invalidateQueries({ queryKey: ['note', selectedNoteId] });
  };

  const saveNoteMutation = useMutation({
    mutationFn: (data) => notes.update(selectedNoteId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes', activeVaultId] });
      queryClient.invalidateQueries({ queryKey: ['note', selectedNoteId] });
      setIsEditing(false);
      stopEditing(selectedNoteId);
      toast.success('Saved');
    },
    onError: (err) => toast.error('Failed to save: ' + err.message),
  });

  const deleteNoteMutation = useMutation({
    mutationFn: (id) => notes.delete(id),
    onSuccess: () => {
      setSelectedNoteId(null);
      invalidateAll();
      toast.success('Note deleted');
    },
    onError: (err) => toast.error('Failed to delete: ' + err.message),
  });

  const createNoteMutation = useMutation({
    mutationFn: ({ title, folderId }) => notes.create(title, '', folderId, [], {}, activeVaultId),
    onSuccess: (created) => {
      setShowCreateNote(false);
      setNewNoteTitle('');
      queryClient.invalidateQueries({ queryKey: ['notes', activeVaultId] });
      setSelectedNoteId(created.id);
      toast.success('Note created');
    },
    onError: (err) => toast.error('Failed to create note: ' + err.message),
  });

  const createFolderMutation = useMutation({
    mutationFn: (name) => folders.create(name, null, activeVaultId),
    onSuccess: () => {
      setShowCreateFolder(false);
      setNewFolderName('');
      queryClient.invalidateQueries({ queryKey: ['folders', activeVaultId] });
      toast.success('Folder created');
    },
    onError: (err) => toast.error('Failed to create folder: ' + err.message),
  });

  const deleteFolderMutation = useMutation({
    mutationFn: (id) => folders.delete(id),
    onSuccess: (_, id) => {
      if (activeFolder === id) setActiveFolder(null);
      queryClient.invalidateQueries({ queryKey: ['folders', activeVaultId] });
      queryClient.invalidateQueries({ queryKey: ['notes', activeVaultId] });
      toast.success('Folder deleted');
    },
    onError: (err) => toast.error('Failed to delete folder: ' + err.message),
  });

  // ════════════════════════════════════════════════════════════════════════
  // Handlers
  // ════════════════════════════════════════════════════════════════════════

  const handleSelectNote = (noteItem) => {
    setIsEditing(false);
    setShowMetaEditor(false);
    setShowMoveDialog(false);
    setSelectedNoteId(noteItem.id);
  };

  const handleSave = () => {
    if (!selectedNoteId || !canEdit) return;
    saveNoteMutation.mutate({ title: editTitle, content: editContent });
  };

  const handleDelete = () => {
    if (!selectedNote) return;
    if (!confirm(`Delete "${selectedNote.title}"? This cannot be undone.`)) return;
    deleteNoteMutation.mutate(selectedNote.id);
  };

  const handleCreateNote = () => {
    if (!newNoteTitle.trim()) return;
    createNoteMutation.mutate({ title: newNoteTitle, folderId: activeFolder });
  };

  const handleCreateFolder = () => {
    if (!newFolderName.trim()) return;
    createFolderMutation.mutate(newFolderName);
  };

  const handleDeleteFolder = (folderId) => {
    const folder = allFolders.find((f) => f.id === folderId);
    if (!confirm(`Delete folder "${folder?.name}"? Notes inside will become unfiled.`)) return;
    deleteFolderMutation.mutate(folderId);
  };

  const handleAddTag = async () => {
    if (!selectedNote || !newTag.trim()) return;
    try {
      await notes.addTag(selectedNote.id, newTag.trim());
      setNewTag('');
      queryClient.invalidateQueries({ queryKey: ['note', selectedNoteId] });
      queryClient.invalidateQueries({ queryKey: ['notes', activeVaultId] });
      toast.success('Tag added');
    } catch (err) {
      toast.error('Failed to add tag: ' + err.message);
    }
  };

  const handleRemoveTag = async (tag) => {
    if (!selectedNote) return;
    try {
      await notes.removeTag(selectedNote.id, tag);
      queryClient.invalidateQueries({ queryKey: ['note', selectedNoteId] });
      queryClient.invalidateQueries({ queryKey: ['notes', activeVaultId] });
      toast.success('Tag removed');
    } catch (err) {
      toast.error('Failed to remove tag: ' + err.message);
    }
  };

  // Fully wired: calls AI, then auto-adds each suggested tag (item 116)
  const handleSuggestTags = async () => {
    if (!selectedNote) return;
    try {
      const result = await ai.suggestTags(
        selectedNote.content || selectedNote.title,
        selectedNote.tags || [],
      );
      if (!result.tags?.length) {
        toast.success('No new tags suggested');
        return;
      }
      // Auto-add all suggested tags
      for (const tag of result.tags) {
        await notes.addTag(selectedNote.id, tag);
      }
      queryClient.invalidateQueries({ queryKey: ['note', selectedNoteId] });
      queryClient.invalidateQueries({ queryKey: ['notes', activeVaultId] });
      toast.success(`Added ${result.tags.length} tag${result.tags.length > 1 ? 's' : ''}: ${result.tags.join(', ')}`);
    } catch (err) {
      if (isRateLimitError(err)) { toast.error(RATE_LIMIT_MSG); return; }
      toast.error('Tag suggestion failed: ' + err.message);
    }
  };

  // Fully wired: calls AI, shows result inline below editor (item 116)
  const handleSummarize = async () => {
    if (!selectedNote?.content) { toast.error('Note has no content to summarize'); return; }
    try {
      const result = await ai.summarize(selectedNote.content);
      setSummaryResult(result.summary);
    } catch (err) {
      if (isRateLimitError(err)) { toast.error(RATE_LIMIT_MSG); return; }
      toast.error('Summarization failed: ' + err.message);
    }
  };

  // Item 109: propose-links handler
  const handleProposeLinks = async () => {
    if (!selectedNote) return;
    const content = isEditing ? editContent : (selectedNote.content || '');
    if (!content.trim()) { toast.error('Note has no content to analyze'); return; }
    try {
      const noteTitles = allNotes
        .filter((n) => n.id !== selectedNote.id)
        .map((n) => n.title);
      const result = await ai.proposeLinks(content, noteTitles);
      if (!result.links?.length) {
        toast.success('No link suggestions found');
        return;
      }
      setProposedLinks(result.links);
      toast.success(`${result.links.length} link suggestion${result.links.length > 1 ? 's' : ''} — click a chip to insert`);
    } catch (err) {
      if (isRateLimitError(err)) { toast.error(RATE_LIMIT_MSG); return; }
      toast.error('Link suggestion failed: ' + err.message);
    }
  };

  const handleMoveNote = async (destFolderId) => {
    if (!selectedNote) return;
    try {
      await notes.move(selectedNote.id, destFolderId || null);
      setShowMoveDialog(false);
      queryClient.invalidateQueries({ queryKey: ['note', selectedNoteId] });
      queryClient.invalidateQueries({ queryKey: ['notes', activeVaultId] });
      toast.success('Note moved');
    } catch (err) {
      toast.error('Failed to move: ' + err.message);
    }
  };

  const handleAddMeta = async () => {
    if (!selectedNote || !metaKey.trim()) return;
    try {
      await notes.updateMeta(selectedNote.id, { [metaKey.trim()]: metaValue });
      setMetaKey('');
      setMetaValue('');
      queryClient.invalidateQueries({ queryKey: ['note', selectedNoteId] });
      toast.success('Metadata updated');
    } catch (err) {
      toast.error('Failed to update metadata: ' + err.message);
    }
  };

  const handleRemoveMeta = async (key) => {
    if (!selectedNote) return;
    try {
      await notes.updateMeta(selectedNote.id, { [key]: '' });
      queryClient.invalidateQueries({ queryKey: ['note', selectedNoteId] });
      toast.success('Metadata removed');
    } catch (err) {
      toast.error('Failed to remove metadata: ' + err.message);
    }
  };

  const handleSetGroup = async (groupId) => {
    if (!selectedNote) return;
    try {
      await notes.update(selectedNote.id, { group_id: groupId || null });
      queryClient.invalidateQueries({ queryKey: ['note', selectedNoteId] });
      toast.success('Group updated');
    } catch (err) {
      toast.error('Failed to update group: ' + err.message);
    }
  };

  const handleSetPermission = async (subjectId, role) => {
    if (!selectedNote || !canEdit) return;
    const nextPermissions = { ...(selectedNote.permissions || {}) };
    if (!subjectId) return;
    if (!role) delete nextPermissions[subjectId];
    else nextPermissions[subjectId] = role;
    try {
      await notes.update(selectedNote.id, { permissions: nextPermissions });
      queryClient.invalidateQueries({ queryKey: ['note', selectedNoteId] });
      queryClient.invalidateQueries({ queryKey: ['notes', activeVaultId] });
      toast.success('Permissions updated');
    } catch (err) {
      toast.error('Failed to update permissions: ' + err.message);
    }
  };

  const handleToggleGmOnly = async (gmOnly) => {
    if (!selectedNote || !canEdit) return;
    try {
      await notes.updateMeta(selectedNote.id, { gm_only: gmOnly ? 'true' : '' });
      queryClient.invalidateQueries({ queryKey: ['note', selectedNoteId] });
      queryClient.invalidateQueries({ queryKey: ['notes', activeVaultId] });
      toast.success('Visibility updated');
    } catch (err) {
      toast.error('Failed to update visibility: ' + err.message);
    }
  };

  const toggleFolder = (folderId) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(folderId)) next.delete(folderId);
      else next.add(folderId);
      return next;
    });
  };

  const handleHistorySelect = (query) => {
    setSearchQuery(query);
  };

  const handleClearHistory = () => {
    setSearchHistory([]);
  };

  // ════════════════════════════════════════════════════════════════════════
  // RENDER
  // ════════════════════════════════════════════════════════════════════════

  return (
    <div className="p-6 flex flex-col h-full gap-4 min-w-0">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex justify-between items-start">
        <SectionHeader title="📖 Browse" subtitle="Explore and manage your vault." />
        <div className="flex gap-2 items-center">
          <Button variant="primary" size="sm" onClick={() => setShowCreateNote(true)} disabled={!activeVaultId}>+ Note</Button>
          <Button variant="secondary" size="sm" onClick={() => setShowCreateFolder(true)} disabled={!activeVaultId}>+ Folder</Button>
        </div>
      </div>

      {!activeVaultId && (
        <Card className="p-4">
          <p className="text-sm text-txt">
            No project selected. Select a project in the sidebar, or create one in Settings → Campaign before browsing notes.
          </p>
        </Card>
      )}

      {/* ── Create dialogs ─────────────────────────────────────────────── */}
      {showCreateNote && (
        <Card className="p-4 flex gap-2 items-end">
          <div className="flex-1">
            <Input
              label="New Note Title"
              placeholder="My new note..."
              value={newNoteTitle}
              onChange={(e) => setNewNoteTitle(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreateNote()}
            />
          </div>
          <Button variant="primary" size="sm" onClick={handleCreateNote}>Create</Button>
          <Button variant="ghost" size="sm" onClick={() => setShowCreateNote(false)}>Cancel</Button>
        </Card>
      )}
      {showCreateFolder && (
        <Card className="p-4 flex gap-2 items-end">
          <div className="flex-1">
            <Input
              label="New Folder Name"
              placeholder="NPCs, Locations, etc..."
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreateFolder()}
            />
          </div>
          <Button variant="primary" size="sm" onClick={handleCreateFolder}>Create</Button>
          <Button variant="ghost" size="sm" onClick={() => setShowCreateFolder(false)}>Cancel</Button>
        </Card>
      )}

      {/* ── Main layout (3-panel) ──────────────────────────────────────── */}
      {activeVaultId && (
        <div className="flex gap-4 flex-1 overflow-hidden min-h-0 min-w-0">

        {/* LEFT PANEL */}
        <FolderTree
          allFolders={allFolders}
          allNotes={allNotes}
          notesByFolder={notesByFolder}
          unfiledNotes={unfiledNotes}
          activeFolder={activeFolder}
          onFolderSelect={setActiveFolder}
          expandedFolders={expandedFolders}
          onToggleFolder={toggleFolder}
          selectedNoteId={selectedNoteId}
          onNoteSelect={handleSelectNote}
          onDeleteFolder={handleDeleteFolder}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          searchResults={searchResults}
          allTags={allTags}
          tagFilter={tagFilter}
          onTagFilter={setTagFilter}
          loading={loading}
          searchHistory={searchHistory}
          onHistorySelect={handleHistorySelect}
          onClearHistory={handleClearHistory}
        />

        {/* CENTER PANEL */}
        <NoteEditor
          selectedNote={selectedNote}
          allFolders={allFolders}
          isEditing={isEditing}
          editTitle={editTitle}
          editContent={editContent}
          onTitleChange={setEditTitle}
          onContentChange={setEditContent}
          onEdit={() => {
            if (!canEdit) return;
            setIsEditing(true);
            startEditing(selectedNote?.id, 0);
          }}
          onSave={handleSave}
          onCancel={() => {
            setIsEditing(false);
            stopEditing(selectedNote?.id);
            if (selectedNote) {
              setEditTitle(selectedNote.title);
              setEditContent(selectedNote.content || '');
            }
          }}
          onDelete={handleDelete}
          onSummarize={handleSummarize}
          onSuggestTags={handleSuggestTags}
          onSuggestLinks={handleProposeLinks}
          proposedLinks={proposedLinks}
          onClearProposedLinks={() => setProposedLinks([])}
          summaryResult={summaryResult}
          onClearSummary={() => setSummaryResult('')}
          showMoveDialog={showMoveDialog}
          onToggleMove={setShowMoveDialog}
          onMove={handleMoveNote}
          wordCount={wordCount}
          activeFolder={activeFolder}
          noteLoading={noteLoading && !!selectedNoteId}
          canEdit={canEdit}
          editingPresence={editingPresence}
          onCursorChange={(cursor) => selectedNoteId && updateCursor(selectedNoteId, cursor)}
        />

        {/* RIGHT PANEL */}
        {selectedNote && (
          <Card className="w-72 flex-shrink-0 flex flex-col overflow-hidden p-0">
            <div className="px-4 py-3 border-b border-txt-muted/10">
              <h3 className="text-sm font-bold text-txt">Properties</h3>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-4">
              <TagPanel
                selectedNote={selectedNote}
                newTag={newTag}
                onNewTagChange={setNewTag}
                onAddTag={handleAddTag}
                onRemoveTag={handleRemoveTag}
                onSuggestTags={handleSuggestTags}
              />

              <PermissionsPanel
                selectedNote={selectedNote}
                allFolders={allFolders}
                onSetGroup={handleSetGroup}
                groups={groupList}
                users={userList}
                canEdit={canEdit}
                onSetPermission={handleSetPermission}
                onToggleGmOnly={handleToggleGmOnly}
              />

              <MetaPanel
                selectedNote={selectedNote}
                showMetaEditor={showMetaEditor}
                onToggleMetaEditor={() => setShowMetaEditor((v) => !v)}
                metaKey={metaKey}
                metaValue={metaValue}
                onMetaKeyChange={setMetaKey}
                onMetaValueChange={setMetaValue}
                onAddMeta={handleAddMeta}
                onRemoveMeta={handleRemoveMeta}
              />

              {/* AI Summary */}
              {selectedNote.ai_summary && (
                <div>
                  <p className="text-xs font-bold text-txt-muted uppercase tracking-wider mb-1">AI Summary</p>
                  <p className="text-xs text-txt-secondary">{selectedNote.ai_summary}</p>
                </div>
              )}

              {/* File info */}
              <div className="border-t border-txt-muted/10 pt-3">
                <p className="text-xs font-bold text-txt-muted uppercase tracking-wider mb-2">Info</p>
                <div className="space-y-1 text-xs text-txt-muted">
                  <div className="flex justify-between">
                    <span>Created</span>
                    <span className="text-txt">{new Date(selectedNote.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Modified</span>
                    <span className="text-txt">{new Date(selectedNote.last_modified).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Words</span>
                    <span className="text-txt">{wordCount(selectedNote.content)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Owner</span>
                    <span className="text-txt truncate ml-2">{selectedNote.owner_id || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>ID</span>
                    <span className="text-txt truncate ml-2 font-mono text-[10px]">{selectedNote.id}</span>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        )}
        </div>
      )}
    </div>
  );
}
