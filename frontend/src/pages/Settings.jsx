import { useState, useEffect } from 'react';
import SectionHeader from '@/components/SectionHeader';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Input from '@/components/Input';
import Badge from '@/components/Badge';
import { auth, settings, users, invites, debug } from '@/api';
import { THEMES, applyTheme, getStoredTheme } from '@/theme';

export default function Settings({ user }) {
  const [activeTab, setActiveTab] = useState('app');
  const [showPassword, setShowPassword] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');

  // App Settings — use snake_case to match backend
  const [theme, setTheme] = useState(getStoredTheme());
  const [fontSize, setFontSize] = useState('medium');
  const [autosave, setAutosave] = useState(true);

  // My Account
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');

  // AI Settings
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [model, setModel] = useState('gpt-4');
  const [maxTokens, setMaxTokens] = useState('2048');

  // Campaign
  const [vaultPath, setVaultPath] = useState('/vault');
  const [campaignApiKey, setCampaignApiKey] = useState('');

  // Users list — loaded from API
  const [usersList, setUsersList] = useState([]);
  const [usersLoading, setUsersLoading] = useState(false);

  // Invite codes
  const [invitesList, setInvitesList] = useState([]);
  const [invitesLoading, setInvitesLoading] = useState(false);

  // Reset password dialog
  const [resetUserId, setResetUserId] = useState(null);
  const [resetNewPassword, setResetNewPassword] = useState('');

  // Debug log viewer (admin only)
  const [crashLogs, setCrashLogs] = useState([]);
  const [runtimeLog, setRuntimeLog] = useState('');
  const [selectedLog, setSelectedLog] = useState(null); // { name, content }
  const [debugLoading, setDebugLoading] = useState(false);

  // Load settings from backend on mount (theme excluded — localStorage is source of truth)
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const data = await settings.get();
        // Don't override theme from backend — localStorage (via getStoredTheme)
        // is the live source of truth, already applied by initTheme() at startup.
        if (data.font_size) setFontSize(data.font_size.toLowerCase());
        if (data.autosave !== undefined) setAutosave(data.autosave);
        if (data.vault_path) setVaultPath(data.vault_path);
        if (data.completion_model) setModel(data.completion_model);
        if (data.max_tokens) setMaxTokens(String(data.max_tokens));
        if (data.api_key) setApiKey(data.api_key);
        if (data.campaign_api_key) setCampaignApiKey(data.campaign_api_key);
      } catch (err) {
        console.error('Failed to load settings:', err);
      }
    };
    loadSettings();
  }, []);

  // Load users + invites when the admin tab is activated
  useEffect(() => {
    if (activeTab === 'users' && isAdmin) {
      loadUsers();
      loadInvites();
    }
    if (activeTab === 'debug' && isAdmin) {
      loadDebugLogs();
    }
  }, [activeTab]);

  const isAdmin = user?.roles?.includes?.('admin') || user?.role === 'admin';

  const loadUsers = async () => {
    setUsersLoading(true);
    try {
      const list = await users.list();
      setUsersList(list);
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setUsersLoading(false);
    }
  };

  const showSaveStatus = (msg) => {
    setSaveStatus(msg);
    setTimeout(() => setSaveStatus(''), 3000);
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      setPasswordError('Passwords do not match');
      return;
    }
    if (newPassword.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      return;
    }

    try {
      await auth.changePassword(currentPassword, newPassword);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setPasswordError('');
      showSaveStatus('Password updated successfully');
    } catch (err) {
      setPasswordError(err.message);
    }
  };

  const handleSaveSettings = async () => {
    try {
      await settings.update({
        theme,
        font_size: fontSize,
        autosave,
      });
      showSaveStatus('Settings saved');
    } catch (err) {
      console.error('Failed to save settings:', err);
      showSaveStatus('Failed to save settings');
    }
  };

  const handleSaveAI = async () => {
    try {
      await settings.update({
        completion_model: model,
        max_tokens: parseInt(maxTokens, 10) || 2048,
        api_key: apiKey || undefined,
      });
      showSaveStatus('AI settings saved');
    } catch (err) {
      console.error('Failed to save AI settings:', err);
      showSaveStatus('Failed to save AI settings');
    }
  };

  const handleSaveCampaign = async () => {
    try {
      await settings.update({
        vault_path: vaultPath,
        campaign_api_key: campaignApiKey || undefined,
      });
      showSaveStatus('Campaign settings saved');
    } catch (err) {
      console.error('Failed to save campaign settings:', err);
      showSaveStatus('Failed to save campaign settings');
    }
  };

  const handleBrowseVault = () => {
    // Use Electron dialog if available, otherwise prompt
    if (window.electronAPI?.selectFolder) {
      window.electronAPI.selectFolder().then((path) => {
        if (path) setVaultPath(path);
      });
    } else {
      const path = window.prompt('Enter vault folder path:', vaultPath);
      if (path) setVaultPath(path);
    }
  };

  const handleDisableUser = async (userId) => {
    try {
      await users.disable(userId);
      await loadUsers();
      showSaveStatus('User disabled');
    } catch (err) {
      console.error('Failed to disable user:', err);
    }
  };

  const handleEnableUser = async (userId) => {
    try {
      await users.enable(userId);
      await loadUsers();
      showSaveStatus('User enabled');
    } catch (err) {
      console.error('Failed to enable user:', err);
    }
  };

  const handleResetPassword = async () => {
    if (!resetUserId || !resetNewPassword.trim()) return;
    if (resetNewPassword.length < 8) {
      showSaveStatus('Password must be at least 8 characters');
      return;
    }
    try {
      await users.resetPassword(resetUserId, resetNewPassword);
      setResetUserId(null);
      setResetNewPassword('');
      showSaveStatus('Password reset successfully');
    } catch (err) {
      console.error('Failed to reset password:', err);
      showSaveStatus('Failed to reset password');
    }
  };

  // ── Invite management ────────────────────────────────────────────────
  const loadInvites = async () => {
    setInvitesLoading(true);
    try {
      const list = await invites.list();
      setInvitesList(list);
    } catch (err) {
      console.error('Failed to load invites:', err);
    } finally {
      setInvitesLoading(false);
    }
  };

  const handleGenerateInvite = async () => {
    try {
      await invites.generate();
      await loadInvites();
      showSaveStatus('Invite code generated');
    } catch (err) {
      console.error('Failed to generate invite:', err);
      showSaveStatus('Failed to generate invite');
    }
  };

  const handleRevokeInvite = async (id) => {
    try {
      await invites.revoke(id);
      await loadInvites();
      showSaveStatus('Invite revoked');
    } catch (err) {
      console.error('Failed to revoke invite:', err);
    }
  };

  const loadDebugLogs = async () => {
    setDebugLoading(true);
    try {
      const [logs, log] = await Promise.all([
        debug.listCrashLogs(),
        debug.getRuntimeLog(),
      ]);
      setCrashLogs(logs);
      setRuntimeLog(log.content || '');
    } catch (err) {
      console.error('Failed to load debug logs:', err);
    } finally {
      setDebugLoading(false);
    }
  };

  const handleViewCrashLog = async (filename) => {
    try {
      const data = await debug.getCrashLog(filename);
      setSelectedLog({ name: filename, content: data.content || '' });
    } catch (err) {
      showSaveStatus('Failed to load log: ' + err.message);
    }
  };

  const handleDeleteCrashLog = async (filename) => {
    if (!confirm(`Delete crash log "${filename}"?`)) return;
    try {
      await debug.deleteCrashLog(filename);
      setCrashLogs((prev) => prev.filter((l) => l.name !== filename));
      if (selectedLog?.name === filename) setSelectedLog(null);
      showSaveStatus('Log deleted');
    } catch (err) {
      showSaveStatus('Failed to delete: ' + err.message);
    }
  };

  const handleCopyInvite = (code) => {
    navigator.clipboard.writeText(code).then(() => {
      showSaveStatus('Copied to clipboard!');
    }).catch(() => {
      showSaveStatus('Failed to copy');
    });
  };

  const NavItem = ({ id, label }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`w-full text-left px-4 py-2.5 rounded-lg transition font-medium ${
        activeTab === id
          ? 'bg-accent/10 text-accent'
          : 'text-txt hover:bg-hover'
      }`}
    >
      {label}
    </button>
  );

  // Helper: get display role from user object (handles both .role and .roles)
  const getUserRole = (u) => {
    if (u.roles && Array.isArray(u.roles)) return u.roles[0] || 'player';
    return u.role || 'player';
  };

  return (
    <div className="p-10 space-y-6 h-full">
      <div className="flex justify-between items-start">
        <SectionHeader
          title="⚙️ Settings"
          subtitle="Configure your MythosEngine experience."
        />
        {saveStatus && (
          <span className="text-accent text-sm font-medium bg-accent/10 px-3 py-1.5 rounded-lg">
            {saveStatus}
          </span>
        )}
      </div>

      <div className="flex gap-6 flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <div className="w-48">
          <nav className="space-y-2">
            <NavItem id="app" label="App Settings" />
            <NavItem id="account" label="My Account" />
            <NavItem id="ai" label="AI Settings" />
            <NavItem id="campaign" label="Campaign" />
            <NavItem id="help" label="Help & About" />
            {isAdmin && (
              <NavItem id="users" label="User Management" />
            )}
            {isAdmin && (
              <NavItem id="debug" label="Debug Logs" />
            )}
          </nav>
        </div>

        {/* Right Content */}
        <Card className="flex-1 p-6 overflow-y-auto">
          {/* App Settings */}
          {activeTab === 'app' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-txt mb-4">Appearance</h3>
                <div className="space-y-4">
                  {/* Theme selector with live preview swatches */}
                  <div>
                    <label className="block text-txt-muted text-sm mb-2 font-medium">
                      Theme
                    </label>
                    <div className="grid grid-cols-1 gap-2">
                      {THEMES.map((t) => (
                        <button
                          key={t.id}
                          onClick={() => {
                            setTheme(t.id);
                            applyTheme(t.id);
                          }}
                          className={`flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition text-left ${
                            theme === t.id
                              ? 'border-accent bg-accent/5'
                              : 'border-transparent bg-elevated hover:bg-hover'
                          }`}
                        >
                          {/* Color swatches */}
                          <div className="flex gap-1 flex-shrink-0">
                            <span
                              className="w-5 h-5 rounded-full border border-txt-muted/20"
                              style={{ background: t.preview.bg }}
                            />
                            <span
                              className="w-5 h-5 rounded-full border border-txt-muted/20"
                              style={{ background: t.preview.card }}
                            />
                            <span
                              className="w-5 h-5 rounded-full border border-txt-muted/20"
                              style={{ background: t.preview.accent }}
                            />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-txt text-sm font-semibold">{t.label}</p>
                            <p className="text-txt-muted text-xs truncate">{t.description}</p>
                          </div>
                          {theme === t.id && (
                            <span className="text-accent text-sm flex-shrink-0">&#10003;</span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-txt-muted text-sm mb-2 font-medium">
                      Font Size
                    </label>
                    <select
                      value={fontSize}
                      onChange={(e) => setFontSize(e.target.value)}
                      className="w-full bg-elevated rounded-xl px-4 py-3 text-txt border-2 border-transparent focus:border-accent focus:outline-none transition"
                    >
                      <option value="small">Small</option>
                      <option value="medium">Medium</option>
                      <option value="large">Large</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="border-t border-txt-muted/20 pt-6">
                <h3 className="text-lg font-bold text-txt mb-4">Behavior</h3>
                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={autosave}
                      onChange={(e) => setAutosave(e.target.checked)}
                      className="w-4 h-4 rounded bg-elevated border-2 border-txt-muted accent-accent"
                    />
                    <span className="text-txt">Enable autosave</span>
                  </label>
                </div>
              </div>

              <Button variant="primary" onClick={handleSaveSettings} className="w-full">
                Save Settings
              </Button>
            </div>
          )}

          {/* My Account */}
          {activeTab === 'account' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-txt mb-4">Account Info</h3>
                <div className="space-y-4 bg-elevated rounded-lg p-4">
                  <div>
                    <p className="text-txt-muted text-sm">Username</p>
                    <p className="text-txt font-medium">{user?.username || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-txt-muted text-sm">Email</p>
                    <p className="text-txt font-medium">{user?.email || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-txt-muted text-sm">Role</p>
                    <p className="text-txt font-medium capitalize">{getUserRole(user || {})}</p>
                  </div>
                </div>
              </div>

              <div className="border-t border-txt-muted/20 pt-6">
                <h3 className="text-lg font-bold text-txt mb-4">Change Password</h3>
                <div className="space-y-4">
                  <Input
                    label="Current Password"
                    type="password"
                    placeholder="••••••••"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                  />
                  <Input
                    label="New Password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                  />
                  <Input
                    label="Confirm Password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                  />

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={showPassword}
                      onChange={(e) => setShowPassword(e.target.checked)}
                      className="w-4 h-4 rounded bg-elevated border-2 border-txt-muted accent-accent"
                    />
                    <span className="text-txt-secondary text-sm">Show password</span>
                  </label>

                  {passwordError && (
                    <p className="text-danger text-sm">{passwordError}</p>
                  )}

                  <Button variant="success" onClick={handleChangePassword} className="w-full">
                    Update Password
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* AI Settings */}
          {activeTab === 'ai' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-txt mb-4">AI Configuration</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-txt-muted text-sm mb-2 font-medium">
                      API Key
                    </label>
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
                    <label className="block text-txt-muted text-sm mb-2 font-medium">
                      Model
                    </label>
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
                    <label className="block text-txt-muted text-sm mb-2 font-medium">
                      Max Tokens
                    </label>
                    <input
                      type="number"
                      value={maxTokens}
                      onChange={(e) => setMaxTokens(e.target.value)}
                      className="w-full bg-elevated rounded-xl px-4 py-3 text-txt border-2 border-transparent focus:border-accent focus:outline-none transition"
                    />
                  </div>
                </div>
              </div>

              <Button variant="primary" onClick={handleSaveAI} className="w-full">
                Save AI Settings
              </Button>
            </div>
          )}

          {/* Campaign */}
          {activeTab === 'campaign' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-txt mb-4">Campaign Configuration</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-txt-muted text-sm mb-2 font-medium">
                      Vault Path
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={vaultPath}
                        onChange={(e) => setVaultPath(e.target.value)}
                        placeholder="/path/to/vault"
                        className="flex-1 bg-elevated rounded-xl px-4 py-3 text-txt border-2 border-transparent focus:border-accent focus:outline-none transition"
                      />
                      <Button variant="secondary" size="md" onClick={handleBrowseVault}>
                        Browse
                      </Button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-txt-muted text-sm mb-2 font-medium">
                      Campaign API Key
                    </label>
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

              <Button variant="primary" onClick={handleSaveCampaign} className="w-full">
                Save Campaign Settings
              </Button>
            </div>
          )}

          {/* Help & About */}
          {activeTab === 'help' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-txt mb-4">About MythosEngine</h3>
                <div className="space-y-4 text-txt-secondary">
                  <p>
                    MythosEngine is a powerful world-building and campaign management tool
                    designed for game masters and creative writers.
                  </p>
                  <p>
                    Version: 1.0.0
                  </p>
                </div>
              </div>

              <div className="border-t border-txt-muted/20 pt-6">
                <h3 className="text-lg font-bold text-txt mb-4">Resources</h3>
                <div className="space-y-2">
                  <Button
                    variant="secondary"
                    className="w-full justify-start"
                    onClick={() => window.open('https://github.com/MythosEngine/docs', '_blank')}
                  >
                    📖 Documentation
                  </Button>
                  <Button
                    variant="secondary"
                    className="w-full justify-start"
                    onClick={() => window.open('https://discord.gg/mythosengine', '_blank')}
                  >
                    💬 Community Discord
                  </Button>
                  <Button
                    variant="secondary"
                    className="w-full justify-start"
                    onClick={() => window.open('https://github.com/MythosEngine/issues', '_blank')}
                  >
                    🐛 Report Issue
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Debug Logs */}
          {activeTab === 'debug' && isAdmin && (
            <div className="space-y-6">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-txt">Crash Logs</h3>
                  <Button variant="secondary" size="sm" onClick={loadDebugLogs} disabled={debugLoading}>
                    {debugLoading ? 'Loading…' : 'Refresh'}
                  </Button>
                </div>

                {debugLoading ? (
                  <p className="text-txt-muted text-sm">Loading logs...</p>
                ) : crashLogs.length === 0 ? (
                  <div className="bg-elevated rounded-xl p-4 text-center">
                    <p className="text-txt-muted text-sm">No crash logs found.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {crashLogs.map((log) => (
                      <div
                        key={log.name}
                        className="flex items-center gap-3 bg-elevated rounded-xl px-4 py-3"
                      >
                        <span className="text-txt text-sm font-mono flex-1 truncate">{log.name}</span>
                        <span className="text-txt-muted text-xs flex-shrink-0">
                          {(log.size / 1024).toFixed(1)} KB
                        </span>
                        <Button variant="secondary" size="sm" onClick={() => handleViewCrashLog(log.name)}>
                          View
                        </Button>
                        <Button variant="danger" size="sm" onClick={() => handleDeleteCrashLog(log.name)}>
                          Delete
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Crash log viewer modal */}
              {selectedLog && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-6">
                  <div className="bg-card rounded-2xl shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col">
                    <div className="flex items-center justify-between px-6 py-4 border-b border-txt-muted/20">
                      <h3 className="text-base font-bold text-txt font-mono">{selectedLog.name}</h3>
                      <Button variant="ghost" size="sm" onClick={() => setSelectedLog(null)}>
                        Close
                      </Button>
                    </div>
                    <pre className="flex-1 overflow-auto p-6 text-xs text-txt-secondary font-mono leading-relaxed whitespace-pre-wrap">
                      {selectedLog.content}
                    </pre>
                  </div>
                </div>
              )}

              {/* Runtime log */}
              <div className="border-t border-txt-muted/20 pt-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-txt">Runtime Log</h3>
                  <Button variant="secondary" size="sm" onClick={loadDebugLogs} disabled={debugLoading}>
                    Refresh
                  </Button>
                </div>
                <pre className="bg-elevated rounded-xl p-4 text-xs text-txt-secondary font-mono leading-relaxed whitespace-pre-wrap overflow-auto max-h-96">
                  {runtimeLog || 'No runtime log available.'}
                </pre>
              </div>
            </div>
          )}

          {/* User Management */}
          {activeTab === 'users' && isAdmin && (
            <div className="space-y-6">

              {/* ── Invite Codes ──────────────────────────────────── */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-txt">Invite Codes</h3>
                  <Button variant="primary" size="sm" onClick={handleGenerateInvite}>
                    + Generate Invite
                  </Button>
                </div>
                <p className="text-txt-muted text-sm mb-3">
                  Share invite codes with players so they can create their own accounts.
                </p>

                {invitesLoading ? (
                  <p className="text-txt-muted text-sm">Loading invites...</p>
                ) : invitesList.length === 0 ? (
                  <div className="bg-elevated rounded-xl p-4 text-center">
                    <p className="text-txt-muted text-sm">No invite codes yet. Generate one to share with a player.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {invitesList.map((inv) => {
                      const isActive = inv.is_active && (!inv.expires_at || new Date(inv.expires_at) > new Date());
                      const isUsed = inv.used_by || (inv.use_count > 0 && inv.use_count >= (inv.max_uses || 1));
                      const statusLabel = isUsed ? 'used' : isActive ? 'active' : 'expired';
                      const statusVariant = isUsed ? 'disabled' : isActive ? 'active' : 'expired';

                      return (
                        <div
                          key={inv.id || inv.code}
                          className="flex items-center gap-3 bg-elevated rounded-xl px-4 py-3"
                        >
                          <code className="text-txt font-mono text-sm flex-1 select-all">
                            {inv.code}
                          </code>
                          <Badge label={statusLabel} variant={statusVariant} />
                          {isActive && !isUsed && (
                            <>
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => handleCopyInvite(inv.code)}
                              >
                                Copy
                              </Button>
                              <Button
                                variant="danger"
                                size="sm"
                                onClick={() => handleRevokeInvite(inv.id)}
                              >
                                Revoke
                              </Button>
                            </>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* ── Users Table ───────────────────────────────────── */}
              <div className="border-t border-txt-muted/20 pt-6">
                <h3 className="text-lg font-bold text-txt mb-4">Manage Users</h3>

                {/* Reset password dialog */}
                {resetUserId && (
                  <div className="bg-elevated rounded-xl p-4 mb-4 flex items-end gap-3">
                    <div className="flex-1">
                      <label className="block text-txt-muted text-xs mb-1 font-medium">
                        New password for {usersList.find((u) => u.id === resetUserId)?.username || 'user'}
                      </label>
                      <input
                        type="text"
                        value={resetNewPassword}
                        onChange={(e) => setResetNewPassword(e.target.value)}
                        placeholder="Min 8 characters"
                        className="w-full bg-card rounded-lg px-3 py-2 text-sm text-txt border border-transparent focus:border-accent focus:outline-none"
                      />
                    </div>
                    <Button variant="primary" size="sm" onClick={handleResetPassword}>
                      Reset
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => { setResetUserId(null); setResetNewPassword(''); }}>
                      Cancel
                    </Button>
                  </div>
                )}

                {usersLoading ? (
                  <p className="text-txt-muted text-sm">Loading users...</p>
                ) : usersList.length === 0 ? (
                  <p className="text-txt-muted text-sm">No users found</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-txt-muted/20">
                          <th className="text-left py-3 px-4 text-txt-muted font-medium">User</th>
                          <th className="text-left py-3 px-4 text-txt-muted font-medium">Email</th>
                          <th className="text-left py-3 px-4 text-txt-muted font-medium">Role</th>
                          <th className="text-left py-3 px-4 text-txt-muted font-medium">Status</th>
                          <th className="text-left py-3 px-4 text-txt-muted font-medium">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {usersList.map((u) => (
                          <tr
                            key={u.id}
                            className="border-b border-txt-muted/10 hover:bg-hover transition"
                          >
                            <td className="py-3 px-4 text-txt font-medium">{u.username}</td>
                            <td className="py-3 px-4 text-txt-secondary">{u.email}</td>
                            <td className="py-3 px-4">
                              <Badge
                                label={getUserRole(u)}
                                variant={getUserRole(u) === 'admin' ? 'admin' : 'player'}
                              />
                            </td>
                            <td className="py-3 px-4">
                              <Badge
                                label={u.is_active !== false ? 'active' : 'disabled'}
                                variant={u.is_active !== false ? 'active' : 'disabled'}
                              />
                            </td>
                            <td className="py-3 px-4 space-x-1">
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => { setResetUserId(u.id); setResetNewPassword(''); }}
                              >
                                Reset PW
                              </Button>
                              {u.is_active !== false ? (
                                <Button variant="danger" size="sm" onClick={() => handleDisableUser(u.id)}>
                                  Disable
                                </Button>
                              ) : (
                                <Button variant="success" size="sm" onClick={() => handleEnableUser(u.id)}>
                                  Enable
                                </Button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
