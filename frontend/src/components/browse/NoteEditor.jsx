import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import Card from '@/components/Card';
import Button from '@/components/Button';
import { SkeletonLine } from '@/components/Skeleton';

export default function NoteEditor({
  selectedNote,
  allFolders,
  isEditing,
  editTitle,
  editContent,
  onTitleChange,
  onContentChange,
  onEdit,
  onSave,
  onCancel,
  onDelete,
  onSummarize,
  onSuggestTags,
  onSuggestLinks,
  proposedLinks = [],
  onClearProposedLinks,
  summaryResult = '',
  onClearSummary,
  showMoveDialog,
  onToggleMove,
  onMove,
  wordCount,
  activeFolder,
  noteLoading,
}) {
  const [showPreview, setShowPreview] = useState(false);
  const textareaRef = useRef(null);
  // Deferred cursor position after React re-renders the textarea value
  const [pendingCursor, setPendingCursor] = useState(null);

  useEffect(() => {
    if (pendingCursor !== null && textareaRef.current) {
      textareaRef.current.selectionStart = pendingCursor;
      textareaRef.current.selectionEnd = pendingCursor;
      textareaRef.current.focus();
      setPendingCursor(null);
    }
  }, [editContent, pendingCursor]);

  const handleInsertLink = (link) => {
    if (!textareaRef.current) return;
    const ta = textareaRef.current;
    const start = ta.selectionStart ?? editContent.length;
    const insert = `[[${link}]]`;
    const newContent = editContent.slice(0, start) + insert + editContent.slice(start);
    onContentChange(newContent);
    setPendingCursor(start + insert.length);
  };

  if (noteLoading) {
    return (
      <Card className="flex-1 flex flex-col overflow-hidden p-5 space-y-4">
        <SkeletonLine width="w-1/2" height="h-6" />
        <SkeletonLine />
        <SkeletonLine width="w-5/6" />
        <SkeletonLine width="w-4/6" />
      </Card>
    );
  }

  if (!selectedNote) {
    return (
      <Card className="flex-1 flex flex-col overflow-hidden p-0">
        <div className="flex items-center justify-center h-full">
          <div className="text-center space-y-3">
            <div className="text-4xl">📖</div>
            <p className="text-txt-muted">Select a folder to get started</p>
            <p className="text-txt-muted text-xs">or create a new note with + Note</p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="flex-1 flex flex-col overflow-hidden p-0">
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-txt-muted/10 flex-wrap">
        {!isEditing ? (
          <>
            <h2 className="text-lg font-bold text-txt flex-1 truncate">{selectedNote.title}</h2>
            <Button variant="secondary" size="sm" onClick={onEdit}>Edit</Button>
            <Button variant="secondary" size="sm" onClick={() => onToggleMove(!showMoveDialog)}>Move</Button>
            {onSummarize && (
              <Button variant="ghost" size="sm" onClick={onSummarize}>Summarize</Button>
            )}
            {onSuggestTags && (
              <Button variant="ghost" size="sm" onClick={onSuggestTags}>Suggest Tags</Button>
            )}
            {onSuggestLinks && (
              <Button variant="ghost" size="sm" onClick={onSuggestLinks}>Suggest Links</Button>
            )}
            <Button variant="danger" size="sm" onClick={onDelete}>Delete</Button>
          </>
        ) : (
          <>
            <input
              value={editTitle}
              onChange={(e) => onTitleChange(e.target.value)}
              className="flex-1 bg-elevated rounded-lg px-3 py-1.5 text-lg font-bold text-txt border border-transparent focus:border-accent focus:outline-none"
            />
            <button
              onClick={() => setShowPreview((p) => !p)}
              className={`text-xs px-2 py-1 rounded transition ${showPreview ? 'bg-accent/20 text-accent' : 'text-txt-muted hover:text-txt'}`}
            >
              {showPreview ? 'Editor' : 'Preview'}
            </button>
            {onSuggestLinks && (
              <Button variant="ghost" size="sm" onClick={onSuggestLinks}>Suggest Links</Button>
            )}
            <Button variant="primary" size="sm" onClick={onSave} title="Ctrl+S">
              Save
            </Button>
            <Button variant="ghost" size="sm" onClick={onCancel}>Cancel</Button>
          </>
        )}
      </div>

      {/* Move dialog */}
      {showMoveDialog && (
        <div className="px-4 py-2 bg-elevated/50 border-b border-txt-muted/10 flex flex-wrap gap-2 items-center">
          <span className="text-txt-muted text-xs font-medium">Move to:</span>
          <Button
            variant={!selectedNote.folder_id ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => onMove(null)}
          >
            Unfiled
          </Button>
          {allFolders.map((f) => (
            <Button
              key={f.id}
              variant={selectedNote.folder_id === f.id ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => onMove(f.id)}
            >
              📁 {f.name}
            </Button>
          ))}
        </div>
      )}

      {/* Proposed links chips (item 109) */}
      {proposedLinks.length > 0 && (
        <div className="px-4 py-2 bg-elevated/40 border-b border-txt-muted/10">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-txt-muted font-medium shrink-0">Link suggestions:</span>
            {proposedLinks.map((link) => (
              <button
                key={link}
                onClick={() => handleInsertLink(link)}
                className="text-xs px-2.5 py-1 rounded-full bg-accent/15 text-accent hover:bg-accent/30 transition font-medium"
                title={`Insert [[${link}]]`}
              >
                {link}
              </button>
            ))}
            <button
              onClick={onClearProposedLinks}
              className="text-xs text-txt-muted hover:text-txt ml-auto transition"
              title="Dismiss"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Content area */}
      <div className="flex-1 overflow-y-auto p-5">
        {isEditing ? (
          showPreview ? (
            <div className="prose prose-invert max-w-none">
              <ReactMarkdown>{editContent || '*No content*'}</ReactMarkdown>
            </div>
          ) : (
            <textarea
              ref={textareaRef}
              value={editContent}
              onChange={(e) => onContentChange(e.target.value)}
              className="w-full h-full min-h-[300px] bg-elevated rounded-xl px-4 py-3 text-txt border-2 border-transparent focus:border-accent focus:outline-none transition resize-none font-mono text-sm"
            />
          )
        ) : (
          <div className="prose prose-invert max-w-none">
            <div className="text-txt whitespace-pre-wrap text-sm leading-relaxed">
              {selectedNote.content || 'No content'}
            </div>
          </div>
        )}
      </div>

      {/* Inline AI summary (item 116) */}
      {summaryResult && (
        <div className="mx-5 mb-3 p-3 bg-accent/8 rounded-xl border border-accent/20">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-xs font-bold text-accent uppercase tracking-wider mb-1">AI Summary</p>
              <p className="text-sm text-txt leading-relaxed">{summaryResult}</p>
            </div>
            <button
              onClick={onClearSummary}
              className="text-txt-muted hover:text-txt transition shrink-0 text-xs mt-0.5"
              title="Dismiss"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Bottom bar */}
      <div className="px-4 py-2 border-t border-txt-muted/10 flex justify-between items-center text-xs text-txt-muted">
        <span>
          {wordCount(selectedNote.content)} words
          {selectedNote.folder_id && (
            <> · 📁 {allFolders.find((f) => f.id === selectedNote.folder_id)?.name || selectedNote.folder_id}</>
          )}
        </span>
        <span>Modified: {new Date(selectedNote.last_modified).toLocaleString()}</span>
      </div>
    </Card>
  );
}
