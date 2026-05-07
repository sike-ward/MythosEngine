import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import SectionHeader from '@/components/SectionHeader';
import Card from '@/components/Card';
import Button from '@/components/Button';
import { TextArea } from '@/components/Input';
import { ai } from '@/api';

const BASE_URL =
  typeof window !== 'undefined' && window.electronAPI
    ? 'http://127.0.0.1:8741'
    : '/api';

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [streamingMode, setStreamingMode] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const nextId = () => `msg-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

  const handleAsk = async () => {
    if (!prompt.trim() || loading) return;

    const userMessage = { id: nextId(), role: 'user', content: prompt };
    const history = messages.slice(-10).map((m) => ({ role: m.role, content: m.content }));
    setMessages((prev) => [...prev, userMessage]);
    setPrompt('');
    setLoading(true);

    if (streamingMode) {
      await handleStreamingAsk(prompt, history);
    } else {
      await handleRegularAsk(prompt, history);
    }
  };

  const handleRegularAsk = async (userPrompt, history) => {
    try {
      const response = await ai.ask(userPrompt, history);
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: 'assistant', content: response.response },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: 'error', content: `Error: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleStreamingAsk = async (userPrompt, history) => {
    const assistantId = nextId();
    setMessages((prev) => [...prev, { id: assistantId, role: 'assistant', content: '' }]);

    try {
      const { getToken } = await import('@/api');
      const token = getToken();
      const res = await fetch(`${BASE_URL}/ai/ask/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ prompt: userPrompt, history }),
      });

      if (!res.ok) throw new Error(`Stream error: ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const data = line.slice(6);
          if (data === '[DONE]') break;
          try {
            const parsed = JSON.parse(data);
            if (parsed.error) throw new Error(parsed.error);
            if (parsed.token) {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, content: m.content + parsed.token } : m
                )
              );
            }
          } catch {
            // ignore parse errors on individual chunks
          }
        }
      }
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId ? { ...m, role: 'error', content: `Error: ${err.message}` } : m
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([]);
    setPrompt('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleAsk();
    }
  };

  return (
    <div className="p-10 space-y-6 flex flex-col h-full">
      <div className="flex justify-between items-start">
        <SectionHeader
          title="✦ AI Assistant"
          subtitle="Ask anything about your world, lore, or notes."
        />
        <label className="flex items-center gap-2 text-sm text-txt-muted cursor-pointer">
          <input
            type="checkbox"
            checked={streamingMode}
            onChange={(e) => setStreamingMode(e.target.checked)}
            className="w-4 h-4 rounded bg-elevated border-2 border-txt-muted accent-accent"
          />
          Streaming
        </label>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="text-5xl mb-4">✦</div>
              <p className="text-txt-secondary text-lg font-medium">Ask anything about your campaign</p>
              <p className="text-txt-muted text-sm mt-1">Lore, NPCs, quests, rules — your AI guide awaits.</p>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-2xl px-4 py-4 rounded-xl ${
                  msg.role === 'user'
                    ? 'bg-accent/10 text-txt'
                    : msg.role === 'error'
                      ? 'bg-danger/10 text-danger border border-danger/20'
                      : 'bg-card text-txt'
                }`}
              >
                {msg.role === 'assistant' ? (
                  <ReactMarkdown className="prose prose-sm prose-invert max-w-none text-txt">
                    {msg.content || '…'}
                  </ReactMarkdown>
                ) : (
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                )}
              </div>
            </div>
          ))
        )}
        {loading && !streamingMode && (
          <div className="flex justify-start">
            <Card className="px-4 py-4 max-w-xs lg:max-w-md">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
                <p className="text-txt-secondary text-sm">Thinking...</p>
              </div>
            </Card>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <Card className="p-6 space-y-4">
        <TextArea
          placeholder="Ask about your world..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          title="Ctrl+Enter to send"
        />
        <div className="flex gap-3">
          <Button
            variant="primary"
            onClick={handleAsk}
            disabled={loading || !prompt.trim()}
            className="flex-1"
            title="Ctrl+Enter to send"
          >
            {loading ? 'Thinking...' : '✦ Ask AI'}
          </Button>
          <Button
            variant="ghost"
            onClick={handleClear}
            disabled={loading}
            className="flex-1"
          >
            Clear
          </Button>
        </div>
      </Card>
    </div>
  );
}
