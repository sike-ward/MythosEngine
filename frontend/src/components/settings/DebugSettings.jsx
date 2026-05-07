export default function DebugSettings() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-bold text-txt mb-4">Debug & Diagnostics</h3>
        <div className="bg-elevated rounded-xl p-4 space-y-3">
          <div>
            <p className="text-xs font-bold text-txt-muted uppercase tracking-wider mb-2">Runtime Log</p>
            <div className="bg-card rounded-lg p-3 font-mono text-xs text-txt-muted min-h-[80px] max-h-[200px] overflow-y-auto">
              No log entries available.
            </div>
          </div>
          <div>
            <p className="text-xs font-bold text-txt-muted uppercase tracking-wider mb-2">Crash Log</p>
            <div className="bg-card rounded-lg p-3 font-mono text-xs text-txt-muted min-h-[80px] max-h-[200px] overflow-y-auto">
              No crash reports found.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
