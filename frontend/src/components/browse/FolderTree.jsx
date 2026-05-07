import { useState } from 'react';
import Card from '@/components/Card';
import Button from '@/components/Button';
import NoteList from './NoteList';
import { SkeletonLine } from '@/components/Skeleton';

export default function FolderTree({
  allFolders,
  allNotes,
  notesByFolder,
  unfiledNotes,
  activeFolder,
  onFolderSelect,
  expandedFolders,
  onToggleFolder,
  selectedNoteId,
  onNoteSelect,
  onDeleteFolder,
  searchQuery,
  onSearchChange,
  searchResults,
  allTags,
  tagFilter,
  onTagFilter,
  loading,
  searchHistory = [],
  onHistorySelect,
  onClearHistory,
}) {
  const [historyOpen, setHistoryOpen] = useState(false);

  return (
    <Card className="w-72 flex-shrink-0 flex flex-col overflow-hidden p-0">
      {/* Search bar */}
      <div className="p-3 border-b border-txt-muted/10">
        <input
          placeholder="Search notes..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          onFocus={() => setHistoryOpen(true)}
          onBlur={() => setHistoryOpen(false)}
          className="w-full bg-elevated rounded-lg px-3 py-2 text-sm text-txt border border-transparent focus:border-accent focus:outline-none transition placeholder:text-txt-muted"
        />
      </div>

      {/* Search history dropdown — shown when input is focused and empty */}
      {historyOpen && !searchQuery && searchHistory.length > 0 && (
        <div className="border-b border-txt-muted/10 bg-card">
          {searchHistory.map((q, i) => (
            <button
              key={i}
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => { onHistorySelect(q); setHistoryOpen(false); }}
              className="w-full text-left px-3 py-2 text-sm text-txt hover:bg-hover transition flex items-center gap-2 truncate"
            >
              <span className="text-txt-muted text-xs flex-shrink-0">↩</span>
              <span className="truncate">{q}</span>
            </button>
          ))}
          <button
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => { onClearHistory(); setHistoryOpen(false); }}
            className="w-full text-left px-3 py-2 text-xs text-txt-muted hover:bg-hover transition border-t border-txt-muted/10"
          >
            Clear history
          </button>
        </div>
      )}

      {/* Tag filter */}
      {allTags.length > 0 && (
        <div className="px-3 py-2 border-b border-txt-muted/10">
          <select
            value={tagFilter}
            onChange={(e) => onTagFilter(e.target.value)}
            className="w-full bg-elevated rounded-lg px-2 py-1.5 text-xs text-txt border border-transparent focus:border-accent focus:outline-none"
          >
            <option value="">All Tags</option>
            {allTags.map((t) => (
              <option key={t} value={t}>
                {t} ({allNotes.filter((n) => (n.tags || []).includes(t)).length})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Tree area */}
      <div className="flex-1 overflow-y-auto p-2">
        {loading ? (
          <div className="space-y-2 p-2">
            <SkeletonLine width="w-3/4" />
            <SkeletonLine width="w-1/2" />
            <SkeletonLine width="w-2/3" />
          </div>
        ) : searchResults ? (
          /* Search results mode */
          <div className="space-y-0.5">
            <p className="text-txt-muted text-xs px-2 py-1 font-medium">
              {searchResults.length} result{searchResults.length !== 1 ? 's' : ''}
            </p>
            <NoteList
              notes={searchResults}
              selectedNoteId={selectedNoteId}
              onNoteSelect={onNoteSelect}
            />
          </div>
        ) : (
          /* Folder tree mode */
          <div className="space-y-0.5">
            {allNotes.length === 0 && allFolders.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center space-y-2">
                <div className="text-3xl">📁</div>
                <p className="text-txt-muted text-sm">Select a folder to get started</p>
                <p className="text-txt-muted text-xs">or create a new note with + Note</p>
              </div>
            ) : (
              <>
                {/* All Notes button */}
                <button
                  onClick={() => onFolderSelect(null)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition ${
                    !activeFolder ? 'bg-accent/10 text-accent font-semibold' : 'text-txt hover:bg-hover'
                  }`}
                >
                  📋 All Notes ({allNotes.length})
                </button>

                {/* Folders */}
                {allFolders.map((folder) => {
                  const folderNotes = notesByFolder[folder.id] || [];
                  const isExpanded = expandedFolders.has(folder.id);
                  const isActive = activeFolder === folder.id;

                  return (
                    <div key={folder.id}>
                      <div className="flex items-center group">
                        <button
                          onClick={() => { onToggleFolder(folder.id); onFolderSelect(folder.id); }}
                          className={`flex-1 text-left px-3 py-2 rounded-lg text-sm transition flex items-center gap-2 ${
                            isActive ? 'bg-accent/10 text-accent font-semibold' : 'text-txt hover:bg-hover'
                          }`}
                        >
                          <span className="text-xs">{isExpanded ? '▼' : '▶'}</span>
                          <span>📁 {folder.name}</span>
                          <span className="text-txt-muted text-xs ml-auto">{folderNotes.length}</span>
                        </button>
                        <button
                          onClick={() => onDeleteFolder(folder.id)}
                          className="hidden group-hover:block text-danger text-xs px-1 hover:bg-danger/10 rounded"
                          title="Delete folder"
                        >
                          ✕
                        </button>
                      </div>

                      {isExpanded && folderNotes.length > 0 && (
                        <div className="ml-5 space-y-0.5">
                          <NoteList
                            notes={folderNotes}
                            selectedNoteId={selectedNoteId}
                            onNoteSelect={onNoteSelect}
                          />
                        </div>
                      )}

                      {isExpanded && folderNotes.length === 0 && (
                        <p className="ml-5 text-txt-muted text-xs px-3 py-1">No notes here yet — create one!</p>
                      )}
                    </div>
                  );
                })}

                {/* Unfiled notes */}
                {unfiledNotes.length > 0 && (
                  <div>
                    <button
                      onClick={() => { onToggleFolder('__unfiled__'); onFolderSelect(null); }}
                      className="w-full text-left px-3 py-2 rounded-lg text-sm text-txt-muted hover:bg-hover transition flex items-center gap-2"
                    >
                      <span className="text-xs">{expandedFolders.has('__unfiled__') ? '▼' : '▶'}</span>
                      <span>📄 Unfiled</span>
                      <span className="text-xs ml-auto">{unfiledNotes.length}</span>
                    </button>
                    {expandedFolders.has('__unfiled__') && (
                      <div className="ml-5 space-y-0.5">
                        <NoteList
                          notes={unfiledNotes}
                          selectedNoteId={selectedNoteId}
                          onNoteSelect={onNoteSelect}
                        />
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
