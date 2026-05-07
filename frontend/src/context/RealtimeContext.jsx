import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { getToken, getWsBase } from '@/api';

const RealtimeContext = createContext(null);

export function RealtimeProvider({ user, activeVaultId, children }) {
  const socketRef = useRef(null);
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [editing, setEditing] = useState([]);
  const [lastEvent, setLastEvent] = useState(null);

  useEffect(() => {
    const token = getToken();
    if (!user || !activeVaultId || !token) return undefined;

    const socket = new WebSocket(
      `${getWsBase()}/ws?token=${encodeURIComponent(token)}&vault_id=${encodeURIComponent(activeVaultId)}`
    );
    socketRef.current = socket;

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        setLastEvent(payload);
        if (payload.type === 'presence.snapshot') {
          setOnlineUsers(payload.users || []);
          setEditing(payload.editing || []);
        }
      } catch {
        // ignore malformed events
      }
    };

    socket.onclose = () => {
      if (socketRef.current === socket) socketRef.current = null;
    };

    return () => {
      socket.close();
      if (socketRef.current === socket) socketRef.current = null;
      setOnlineUsers([]);
      setEditing([]);
    };
  }, [user?.id, activeVaultId]);

  const send = (payload) => {
    const socket = socketRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(payload));
    }
  };

  const value = useMemo(
    () => ({
      onlineUsers,
      editing,
      lastEvent,
      startEditing: (noteId, cursor = 0) => send({ type: 'editing.start', note_id: noteId, cursor }),
      updateCursor: (noteId, cursor = 0) => send({ type: 'cursor.move', note_id: noteId, cursor }),
      stopEditing: (noteId) => send({ type: 'editing.stop', note_id: noteId }),
    }),
    [onlineUsers, editing, lastEvent]
  );

  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
}

export function useRealtime() {
  const ctx = useContext(RealtimeContext);
  if (!ctx) throw new Error('useRealtime must be used within RealtimeProvider');
  return ctx;
}
