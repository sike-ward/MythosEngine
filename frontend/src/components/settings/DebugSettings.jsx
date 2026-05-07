import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { debug } from '@/api';
import Button from '@/components/Button';

export default function DebugSettings() {
  const queryClient = useQueryClient();
  const [selectedCrash, setSelectedCrash] = useState('');

  const { data: runtimeLog, isLoading: runtimeLoading } = useQuery({
    queryKey: ['debug-runtime-log'],
    queryFn: debug.getRuntimeLog,
    refetchInterval: 10000,
  });

  const { data: crashLogs = [], isLoading: crashListLoading } = useQuery({
    queryKey: ['debug-crash-logs'],
    queryFn: debug.listCrashLogs,
  });

  const { data: crashLogContent, isLoading: crashLoading } = useQuery({
    queryKey: ['debug-crash-log', selectedCrash],
    queryFn: () => debug.getCrashLog(selectedCrash),
    enabled: Boolean(selectedCrash),
  });

  useEffect(() => {
    if (!crashLogs.length) {
      setSelectedCrash('');
      return;
    }
    if (!selectedCrash || !crashLogs.find((l) => l.name === selectedCrash)) {
      setSelectedCrash(crashLogs[0].name);
    }
  }, [crashLogs, selectedCrash]);

  const deleteCrashMutation = useMutation({
    mutationFn: debug.deleteCrashLog,
    onSuccess: (_res, filename) => {
      if (selectedCrash === filename) setSelectedCrash('');
      queryClient.invalidateQueries({ queryKey: ['debug-crash-logs'] });
      queryClient.invalidateQueries({ queryKey: ['debug-crash-log'] });
      toast.success('Crash log deleted');
    },
    onError: () => toast.error('Failed to delete crash log'),
  });

  const runtimeLines = useMemo(() => {
    const content = runtimeLog?.content || '';
    if (!content.trim()) return [];
    return content.split('\n').slice(-200);
  }, [runtimeLog]);

  const lineClass = (line) => {
    if (line.includes('[ERROR]') || line.includes('Traceback')) return 'text-danger';
    if (line.includes('[WARNING]')) return 'text-warning';
    return 'text-txt-muted';
  };

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['debug-runtime-log'] });
    queryClient.invalidateQueries({ queryKey: ['debug-crash-logs'] });
    if (selectedCrash) queryClient.invalidateQueries({ queryKey: ['debug-crash-log', selectedCrash] });
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-txt">Debug & Diagnostics</h3>
          <Button variant="secondary" size="sm" onClick={handleRefresh}>
            Refresh
          </Button>
        </div>
        <div className="bg-elevated rounded-xl p-4 space-y-3">
          <div>
            <p className="text-xs font-bold text-txt-muted uppercase tracking-wider mb-2">Runtime Log</p>
            <div className="bg-card rounded-lg p-3 font-mono text-xs text-txt-muted min-h-[80px] max-h-[200px] overflow-y-auto">
              {runtimeLoading ? (
                'Loading runtime log...'
              ) : runtimeLines.length === 0 ? (
                'No log entries available.'
              ) : (
                runtimeLines.map((line, idx) => (
                  <p key={`${idx}-${line.slice(0, 24)}`} className={lineClass(line)}>{line}</p>
                ))
              )}
            </div>
          </div>
          <div>
            <p className="text-xs font-bold text-txt-muted uppercase tracking-wider mb-2">Crash Log</p>
            {crashListLoading ? (
              <div className="bg-card rounded-lg p-3 font-mono text-xs text-txt-muted min-h-[80px]">
                Loading crash reports...
              </div>
            ) : crashLogs.length === 0 ? (
              <div className="bg-card rounded-lg p-3 font-mono text-xs text-txt-muted min-h-[80px]">
                No crash reports found.
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex gap-2 items-center">
                  <select
                    value={selectedCrash}
                    onChange={(e) => setSelectedCrash(e.target.value)}
                    className="flex-1 bg-card rounded-lg px-3 py-2 text-sm text-txt border border-transparent focus:border-accent focus:outline-none"
                  >
                    {crashLogs.map((log) => (
                      <option key={log.name} value={log.name}>
                        {log.name}
                      </option>
                    ))}
                  </select>
                  <Button
                    variant="danger"
                    size="sm"
                    disabled={!selectedCrash || deleteCrashMutation.isPending}
                    onClick={() => deleteCrashMutation.mutate(selectedCrash)}
                  >
                    Delete
                  </Button>
                </div>
                <div className="bg-card rounded-lg p-3 font-mono text-xs text-txt-muted min-h-[80px] max-h-[220px] overflow-y-auto whitespace-pre-wrap">
                  {crashLoading ? 'Loading crash log...' : (crashLogContent?.content || 'No crash report selected.')}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
