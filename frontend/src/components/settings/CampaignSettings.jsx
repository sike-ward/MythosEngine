import Button from '@/components/Button';

export default function CampaignSettings({ vaultPath, setVaultPath, campaignApiKey, setCampaignApiKey, onSave }) {
  const handleBrowseVault = () => {
    if (window.electronAPI?.selectFolder) {
      window.electronAPI.selectFolder().then((path) => {
        if (path) setVaultPath(path);
      });
    } else {
      const path = window.prompt('Enter vault folder path:', vaultPath);
      if (path) setVaultPath(path);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-bold text-txt mb-4">Campaign Configuration</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-txt-muted text-sm mb-2 font-medium">Vault Path</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={vaultPath}
                onChange={(e) => setVaultPath(e.target.value)}
                placeholder="/path/to/vault"
                className="flex-1 bg-elevated rounded-xl px-4 py-3 text-txt border-2 border-transparent focus:border-accent focus:outline-none transition"
              />
              <Button variant="secondary" size="md" onClick={handleBrowseVault}>Browse</Button>
            </div>
          </div>

          <div>
            <label className="block text-txt-muted text-sm mb-2 font-medium">Campaign API Key</label>
            <input
              type="password"
              value={campaignApiKey}
              onChange={(e) => setCampaignApiKey(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-elevated rounded-xl px-4 py-3 text-txt border-2 border-transparent focus:border-accent focus:outline-none transition"
            />
          </div>
        </div>
      </div>

      <Button variant="primary" onClick={onSave} className="w-full">Save Campaign Settings</Button>
    </div>
  );
}
