import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Layers, Plus, Settings2, Trash2, X, Check } from 'lucide-react';
import Button from '@/components/Button';
import Input, { TextArea } from '@/components/Input';
import SectionHeader from '@/components/SectionHeader';
import { vaults as vaultsApi } from '@/api';
import { useVault } from '@/context/VaultContext';

function formatDate(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  } catch {
    return '—';
  }
}

function VaultCard({ vault, isActive, onEnter }) {
  const qc = useQueryClient();
  const [expanded, setExpanded] = useState(false);
  const [editName, setEditName] = useState(vault.name);
  const [editDesc, setEditDesc] = useState(vault.description || '');
  const [confirmDelete, setConfirmDelete] = useState(false);

  const refreshVaults = () => qc.invalidateQueries({ queryKey: ['vaults'] });

  const updateMutation = useMutation({
    mutationFn: (data) => vaultsApi.update(vault.id, data),
    onSuccess: () => { refreshVaults(); toast.success('Vault updated'); },
    onError: (err) => toast.error(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: () => vaultsApi.remove(vault.id),
    onSuccess: () => { refreshVaults(); toast.success('Vault archived'); setConfirmDelete(false); setExpanded(false); },
    onError: (err) => toast.error(err.message),
  });

  const handleSave = () => {
    const payload = {};
    const trimmedName = editName.trim();
    if (trimmedName && trimmedName !== vault.name) payload.name = trimmedName;
    if (editDesc !== (vault.description || '')) payload.description = editDesc;
    if (!Object.keys(payload).length) { toast('No changes to save'); return; }
    updateMutation.mutate(payload);
  };

  return (
    <div
      className={`bg-surface rounded-2xl border-2 transition-all flex flex-col ${
        isActive ? 'border-accent' : 'border-border-subtle hover:border-accent/40'
      }`}
    >
      {/* Clickable card body — enters vault */}
      <button className="text-left p-5 flex-1 min-w-0" onClick={onEnter}>
        <div className="flex items-start gap-2 mb-2">
          <Layers size={18} className={`mt-0.5 shrink-0 ${isActive ? 'text-accent' : 'text-txt-muted'}`} />
          <span className={`font-semibold text-base truncate ${isActive ? 'text-accent' : 'text-txt'}`}>
            {vault.name}
          </span>
          {isActive && (
            <span className="shrink-0 text-[10px] uppercase tracking-widest font-bold bg-accent/20 text-accent px-2 py-0.5 rounded-full">
              Active
            </span>
          )}
        </div>
        <p className="text-txt-muted text-sm line-clamp-2 min-h-[2.5rem] ml-6">
          {vault.description || <span className="italic opacity-50">No description</span>}
        </p>
        <div className="flex items-center gap-4 mt-3 ml-6 text-xs text-txt-muted">
          <span>{vault.members?.length ?? 0} member{vault.members?.length !== 1 ? 's' : ''}</span>
          <span>Created {formatDate(vault.created_at)}</span>
        </div>
      </button>

      {/* Settings toggle bar */}
      <div className="px-5 py-3 border-t border-border-subtle">
        <button
          onClick={() => { setExpanded((v) => !v); setConfirmDelete(false); }}
          className="text-xs text-txt-muted hover:text-txt flex items-center gap-1.5 transition-colors"
        >
          <Settings2 size={13} />
          {expanded ? 'Hide settings' : 'Manage'}
        </button>
      </div>

      {/* Inline settings panel */}
      {expanded && (
        <div className="px-5 pb-5 space-y-3 border-t border-border-subtle pt-4">
          <Input
            label="Name"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
          />
          <TextArea
            label="Description"
            value={editDesc}
            onChange={(e) => setEditDesc(e.target.value)}
            placeholder="Describe this vault…"
          />
          <div className="flex flex-wrap gap-2 pt-1">
            <Button
              size="sm"
              variant="secondary"
              onClick={handleSave}
              disabled={updateMutation.isPending}
            >
              Save changes
            </Button>
            {!confirmDelete ? (
              <Button size="sm" variant="danger" onClick={() => setConfirmDelete(true)}>
                <Trash2 size={13} className="mr-1 inline" />
                Delete
              </Button>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-sm text-danger font-medium">Are you sure?</span>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => deleteMutation.mutate()}
                  disabled={deleteMutation.isPending}
                >
                  <Check size={13} className="mr-1 inline" />
                  Yes, archive
                </Button>
                <Button size="sm" variant="secondary" onClick={() => setConfirmDelete(false)}>
                  <X size={13} className="mr-1 inline" />
                  Cancel
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Vaults() {
  const qc = useQueryClient();
  const { vaults: vaultList = [], activeVaultId, setActiveVaultId } = useVault();
  const [showModal, setShowModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');

  const createMutation = useMutation({
    mutationFn: () =>
      vaultsApi.create({ name: newName.trim(), description: newDesc.trim() || undefined }),
    onSuccess: (vault) => {
      qc.invalidateQueries({ queryKey: ['vaults'] });
      setActiveVaultId(vault.id);
      localStorage.setItem('me_active_vault', vault.id);
      toast.success(`Vault "${vault.name}" created`);
      setShowModal(false);
      setNewName('');
      setNewDesc('');
    },
    onError: (err) => toast.error(err.message),
  });

  const handleEnterVault = (vaultId) => {
    setActiveVaultId(vaultId);
    localStorage.setItem('me_active_vault', vaultId);
  };

  const closeModal = () => {
    setShowModal(false);
    setNewName('');
    setNewDesc('');
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <SectionHeader title="Vaults" subtitle="Your campaign and world containers" />
        <Button onClick={() => setShowModal(true)} className="flex items-center gap-2">
          <Plus size={18} />
          New Vault
        </Button>
      </div>

      {vaultList.length === 0 ? (
        <div className="text-center py-20 text-txt-muted">
          <Layers size={40} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium mb-1">No vaults yet</p>
          <p className="text-sm">Create your first vault to start organizing your world.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {vaultList.map((vault) => (
            <VaultCard
              key={vault.id}
              vault={vault}
              isActive={vault.id === activeVaultId}
              onEnter={() => handleEnterVault(vault.id)}
            />
          ))}
        </div>
      )}

      {/* New Vault Modal */}
      {showModal && (
        <div
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
          onClick={(e) => { if (e.target === e.currentTarget) closeModal(); }}
        >
          <div className="bg-surface rounded-2xl border border-border-subtle w-full max-w-md shadow-xl">
            <div className="flex items-center justify-between p-6 border-b border-border-subtle">
              <h2 className="text-lg font-bold text-txt">New Vault</h2>
              <button onClick={closeModal} className="text-txt-muted hover:text-txt transition-colors">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <Input
                label="Name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="My Campaign"
                autoFocus
                onKeyDown={(e) => { if (e.key === 'Enter' && newName.trim()) createMutation.mutate(); }}
              />
              <TextArea
                label="Description"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="Describe your campaign world…"
              />
            </div>
            <div className="flex justify-end gap-3 px-6 pb-6">
              <Button variant="secondary" onClick={closeModal}>Cancel</Button>
              <Button
                onClick={() => createMutation.mutate()}
                disabled={!newName.trim() || createMutation.isPending}
              >
                Create Vault
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
