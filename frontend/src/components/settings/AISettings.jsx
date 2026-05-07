import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import Button from '@/components/Button';
import { ai } from '@/api';

const AI_MODELS = [
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  { value: 'claude-3-opus', label: 'Claude 3 Opus' },
  { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
  { value: 'claude-3-haiku', label: 'Claude 3 Haiku' },
];

const inputCls =
  'w-full bg-elevated rounded-xl px-4 py-3 text-txt border-2 border-transparent focus:border-accent focus:outline-none transition';

export default function AISettings({
  apiKey, setApiKey,
  preferredModel, setPreferredModel,
  maxTokens, setMaxTokens,
  streamingEnabled, setStreamingEnabled,
  aiHistoryLimit, setAiHistoryLimit,
  onSave,
}) {
  const [showApiKey, setShowApiKey] = useState(false);

  const { data: usageData, isLoading: usageLoading } = useQuery({
    queryKey: ['ai-usage'],
    queryFn: ai.usage,
    retry: false,
  });

  return (
    <div className="space-y-8">
      {/* ── AI Configuration ───────────────────────────────────────────── */}
      <div>
        <h3 className="text-lg font-bold text-txt mb-4">AI Configuration</h3>
        <div className="space-y-4">

          {/* API Key */}
          <div>
            <label className="block text-txt-muted text-sm mb-2 font-medium">API Key</label>
            <div className="flex gap-2">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-..."
                className="flex-1 bg-elevated rounded-xl px-4 py-3 text-txt border-2 border-transparent focus:border-accent focus:outline-none transition"
              />
              <button
                onClick={() => setShowApiKey(!showApiKey)}
                className="text-txt-secondary hover:text-txt transition"
              >
                {showApiKey ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
          </div>

          {/* Preferred AI Model (item 111) */}
          <div>
            <label className="block text-txt-muted text-sm mb-2 font-medium">Preferred AI Model</label>
            <select
              value={preferredModel}
              onChange={(e) => setPreferredModel(e.target.value)}
              className={inputCls}
            >
              {AI_MODELS.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>

          {/* Max Tokens */}
          <div>
            <label className="block text-txt-muted text-sm mb-2 font-medium">Max Tokens</label>
            <input
              type="number"
              value={maxTokens}
              onChange={(e) => setMaxTokens(e.target.value)}
              className={inputCls}
            />
          </div>

          {/* Streaming toggle (item 112) */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-txt">Use streaming responses</p>
              <p className="text-xs text-txt-muted mt-0.5">Stream tokens as they arrive instead of waiting for full response</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={streamingEnabled}
                onChange={(e) => setStreamingEnabled(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-elevated rounded-full peer peer-checked:bg-accent transition-colors" />
              <div className="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform peer-checked:translate-x-5" />
            </label>
          </div>

          {/* Conversation history limit (item 113) */}
          <div>
            <label className="block text-txt-muted text-sm mb-2 font-medium">
              Max conversation history (messages)
            </label>
            <input
              type="number"
              min={1}
              max={20}
              value={aiHistoryLimit}
              onChange={(e) => setAiHistoryLimit(Math.min(20, Math.max(1, Number(e.target.value) || 10)))}
              className={inputCls}
            />
            <p className="text-xs text-txt-muted mt-1">How many past messages to include as context (1–20, default 10)</p>
          </div>
        </div>
      </div>

      <Button variant="primary" onClick={onSave} className="w-full">Save AI Settings</Button>

      {/* ── Usage This Month (item 115) ─────────────────────────────────── */}
      <div className="border-t border-txt-muted/10 pt-6">
        <h3 className="text-base font-bold text-txt mb-4">Usage this month</h3>
        {usageLoading ? (
          <p className="text-sm text-txt-muted">Loading usage…</p>
        ) : usageData ? (
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-elevated rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-txt">{usageData.total_requests.toLocaleString()}</p>
              <p className="text-xs text-txt-muted mt-1">Requests</p>
            </div>
            <div className="bg-elevated rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-txt">{usageData.total_tokens.toLocaleString()}</p>
              <p className="text-xs text-txt-muted mt-1">Tokens</p>
            </div>
            <div className="bg-elevated rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-txt">${Number(usageData.estimated_cost).toFixed(4)}</p>
              <p className="text-xs text-txt-muted mt-1">Est. Cost</p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-txt-muted">No usage data available.</p>
        )}
      </div>
    </div>
  );
}
