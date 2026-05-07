import { useState } from 'react';
import Button from '@/components/Button';

export default function AISettings({ apiKey, setApiKey, model, setModel, maxTokens, setMaxTokens, onSave }) {
  const [showApiKey, setShowApiKey] = useState(false);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-bold text-txt mb-4">AI Configuration</h3>
        <div className="space-y-4">
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

          <div>
            <label className="block text-txt-muted text-sm mb-2 font-medium">Model</label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full bg-elevated rounded-xl px-4 py-3 text-txt border-2 border-transparent focus:border-accent focus:outline-none transition"
            >
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-3.5">GPT-3.5 Turbo</option>
              <option value="claude">Claude</option>
            </select>
          </div>

          <div>
            <label className="block text-txt-muted text-sm mb-2 font-medium">Max Tokens</label>
            <input
              type="number"
              value={maxTokens}
              onChange={(e) => setMaxTokens(e.target.value)}
              className="w-full bg-elevated rounded-xl px-4 py-3 text-txt border-2 border-transparent focus:border-accent focus:outline-none transition"
            />
          </div>
        </div>
      </div>

      <Button variant="primary" onClick={onSave} className="w-full">Save AI Settings</Button>
    </div>
  );
}
