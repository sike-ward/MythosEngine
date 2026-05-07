import Badge from '@/components/Badge';

export default function PermissionsPanel({ selectedNote, allFolders, onSetGroup }) {
  return (
    <>
      {/* Folder */}
      <div>
        <p className="text-xs font-bold text-txt-muted uppercase tracking-wider mb-1">Folder</p>
        <p className="text-sm text-txt">
          {selectedNote.folder_id
            ? `📁 ${allFolders.find((f) => f.id === selectedNote.folder_id)?.name || selectedNote.folder_id}`
            : '📄 Unfiled'}
        </p>
      </div>

      {/* Group */}
      <div>
        <p className="text-xs font-bold text-txt-muted uppercase tracking-wider mb-1">Group</p>
        <input
          value={selectedNote.group_id || ''}
          onChange={(e) => onSetGroup(e.target.value)}
          placeholder="None"
          className="w-full bg-elevated rounded-lg px-2 py-1 text-xs text-txt border border-transparent focus:border-accent focus:outline-none"
        />
      </div>

      {/* Permissions */}
      <div>
        <p className="text-xs font-bold text-txt-muted uppercase tracking-wider mb-1">Permissions</p>
        {Object.keys(selectedNote.permissions || {}).length > 0 ? (
          <div className="space-y-1">
            {Object.entries(selectedNote.permissions).map(([userId, role]) => (
              <div key={userId} className="flex justify-between text-xs">
                <span className="text-txt truncate">{userId}</span>
                <Badge label={role} variant={role === 'admin' ? 'admin' : 'player'} />
              </div>
            ))}
          </div>
        ) : (
          <p className="text-txt-muted text-xs">Owner only</p>
        )}
      </div>

      {/* Links */}
      <div>
        <p className="text-xs font-bold text-txt-muted uppercase tracking-wider mb-1">
          Links ({(selectedNote.links || []).length})
        </p>
        {(selectedNote.links || []).length > 0 ? (
          <div className="space-y-1">
            {selectedNote.links.map((linkId) => (
              <p key={linkId} className="text-xs text-accent truncate">🔗 {linkId}</p>
            ))}
          </div>
        ) : (
          <p className="text-txt-muted text-xs">No links</p>
        )}
      </div>
    </>
  );
}
