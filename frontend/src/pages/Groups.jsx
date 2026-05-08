import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import SectionHeader from '@/components/SectionHeader';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Input from '@/components/Input';
import { groups, users } from '@/api';

const PERMISSION_KEYS = ['can_read', 'can_write', 'can_delete', 'can_invite', 'can_admin'];
const PERMISSION_LABELS = {
  can_read: 'Read',
  can_write: 'Write',
  can_delete: 'Delete',
  can_invite: 'Invite',
  can_admin: 'Admin',
};
const DEFAULT_PERMISSIONS = {
  can_read: true,
  can_write: false,
  can_delete: false,
  can_invite: false,
  can_admin: false,
};

export default function Groups({ user }) {
  const isAdmin = user?.roles?.includes?.('admin');
  const qc = useQueryClient();

  const [selectedGroupId, setSelectedGroupId] = useState(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [permissions, setPermissions] = useState({ ...DEFAULT_PERMISSIONS });
  const [memberEmail, setMemberEmail] = useState('');
  const [showNewForm, setShowNewForm] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDescription, setNewDescription] = useState('');

  const { data: groupList = [] } = useQuery({
    queryKey: ['groups'],
    queryFn: () => groups.list(),
  });
  const { data: userList = [] } = useQuery({
    queryKey: ['users'],
    queryFn: users.list,
    enabled: isAdmin,
  });

  const selectedGroup = useMemo(
    () => groupList.find((g) => g.id === selectedGroupId) || null,
    [groupList, selectedGroupId]
  );

  useEffect(() => {
    if (selectedGroup) {
      setName(selectedGroup.name || '');
      setDescription(selectedGroup.description || '');
      setPermissions({ ...DEFAULT_PERMISSIONS, ...(selectedGroup.permissions || {}) });
    }
  }, [selectedGroup]);

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ['groups'] });
    qc.invalidateQueries({ queryKey: ['users'] });
  };

  const createGroup = useMutation({
    mutationFn: () => groups.create({ name: newName.trim(), description: newDescription.trim() || undefined }),
    onSuccess: (group) => {
      setNewName('');
      setNewDescription('');
      setShowNewForm(false);
      setSelectedGroupId(group.id);
      refresh();
      toast.success('Group created');
    },
    onError: (err) => toast.error(err.message),
  });

  const saveGroup = useMutation({
    mutationFn: () =>
      groups.update(selectedGroup.id, {
        name: name.trim(),
        description: description.trim() || undefined,
        permissions,
      }),
    onSuccess: () => {
      refresh();
      toast.success('Group saved');
    },
    onError: (err) => toast.error(err.message),
  });

  const deleteGroup = useMutation({
    mutationFn: () => groups.remove(selectedGroup.id),
    onSuccess: () => {
      setSelectedGroupId(null);
      refresh();
      toast.success('Group deleted');
    },
    onError: (err) => toast.error(err.message),
  });

  const addMember = useMutation({
    mutationFn: () => {
      const match = userList.find(
        (u) => u.email?.toLowerCase() === memberEmail.trim().toLowerCase() ||
               u.username?.toLowerCase() === memberEmail.trim().toLowerCase()
      );
      if (!match) throw new Error('No user found with that email or username');
      return groups.addMember(selectedGroup.id, match.id);
    },
    onSuccess: () => {
      setMemberEmail('');
      refresh();
      toast.success('Member added');
    },
    onError: (err) => toast.error(err.message),
  });

  const removeMember = useMutation({
    mutationFn: ({ groupId, userId }) => groups.removeMember(groupId, userId),
    onSuccess: () => {
      refresh();
      toast.success('Member removed');
    },
    onError: (err) => toast.error(err.message),
  });

  const togglePermission = (key) => {
    if (!isAdmin) return;
    setPermissions((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="p-10 space-y-6">
      <SectionHeader
        title="Groups & Permissions"
        subtitle="Manage campaign groups and their vault access permissions."
      />

      <div className="grid lg:grid-cols-[300px,1fr] gap-6">
        {/* Left panel — group list */}
        <Card className="p-5 space-y-4">
          {isAdmin && (
            <Button
              className="w-full"
              onClick={() => {
                setShowNewForm((v) => !v);
                setSelectedGroupId(null);
              }}
            >
              {showNewForm ? 'Cancel' : '+ New Group'}
            </Button>
          )}

          {showNewForm && (
            <div className="space-y-3 border border-border-subtle rounded-xl p-4">
              <Input
                label="Name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Group name"
              />
              <Input
                label="Description"
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                placeholder="Optional description"
              />
              <Button
                className="w-full"
                onClick={() => createGroup.mutate()}
                disabled={newName.trim().length < 2 || createGroup.isPending}
              >
                Create
              </Button>
            </div>
          )}

          <div className="space-y-2">
            {groupList.length === 0 && (
              <p className="text-txt-muted text-sm">No groups yet.</p>
            )}
            {groupList.map((group) => (
              <button
                key={group.id}
                onClick={() => { setSelectedGroupId(group.id); setShowNewForm(false); }}
                className={`w-full text-left rounded-xl px-4 py-3 transition-all ${
                  selectedGroupId === group.id
                    ? 'bg-accent-soft text-accent'
                    : 'bg-elevated text-txt hover:bg-hover'
                }`}
              >
                <div className="font-semibold truncate">{group.name}</div>
                <div className="text-xs text-txt-muted">{group.members?.length ?? 0} member{group.members?.length !== 1 ? 's' : ''}</div>
              </button>
            ))}
          </div>
        </Card>

        {/* Right panel — group detail */}
        <Card className="p-6 space-y-6">
          {!selectedGroup ? (
            <p className="text-txt-muted">Select a group to view details.</p>
          ) : (
            <>
              {/* Name & description */}
              <div className="space-y-3">
                <Input
                  label="Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={!isAdmin}
                />
                <Input
                  label="Description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={!isAdmin}
                />
              </div>

              {/* Permissions */}
              <div>
                <p className="text-sm font-medium text-txt-muted mb-3">Permissions</p>
                <div className="flex flex-wrap gap-3">
                  {PERMISSION_KEYS.map((key) => (
                    <label
                      key={key}
                      className={`flex items-center gap-2 px-4 py-2 rounded-xl border-2 cursor-pointer select-none transition-all ${
                        permissions[key]
                          ? 'border-accent bg-accent-soft text-accent'
                          : 'border-border-subtle bg-elevated text-txt-muted'
                      } ${!isAdmin ? 'opacity-60 cursor-not-allowed' : 'hover:border-accent/60'}`}
                    >
                      <input
                        type="checkbox"
                        checked={!!permissions[key]}
                        onChange={() => togglePermission(key)}
                        disabled={!isAdmin}
                        className="sr-only"
                      />
                      <span className="text-sm font-medium">{PERMISSION_LABELS[key]}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Save / Delete */}
              {isAdmin && (
                <div className="flex gap-3">
                  <Button
                    onClick={() => saveGroup.mutate()}
                    disabled={saveGroup.isPending || name.trim().length < 2}
                  >
                    Save
                  </Button>
                  <Button
                    variant="danger"
                    onClick={() => deleteGroup.mutate()}
                    disabled={deleteGroup.isPending}
                  >
                    Delete Group
                  </Button>
                </div>
              )}

              {/* Members list */}
              <div>
                <p className="text-sm font-medium text-txt-muted mb-3">Members</p>

                {isAdmin && (
                  <div className="flex gap-2 mb-4">
                    <div className="flex-1">
                      <Input
                        placeholder="Email or username"
                        value={memberEmail}
                        onChange={(e) => setMemberEmail(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && memberEmail.trim() && addMember.mutate()}
                      />
                    </div>
                    <Button
                      onClick={() => addMember.mutate()}
                      disabled={!memberEmail.trim() || addMember.isPending}
                    >
                      Add
                    </Button>
                  </div>
                )}

                <div className="space-y-2">
                  {(selectedGroup.members || []).length === 0 && (
                    <p className="text-sm text-txt-muted">No members yet.</p>
                  )}
                  {(selectedGroup.members || []).map((memberId) => {
                    const member = userList.find((u) => u.id === memberId);
                    return (
                      <div key={memberId} className="flex items-center gap-3 bg-elevated rounded-xl px-4 py-3">
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-txt truncate">{member?.username || memberId}</div>
                          <div className="text-xs text-txt-muted truncate">{member?.email || ''}</div>
                        </div>
                        <div className="text-xs text-txt-muted shrink-0">
                          {selectedGroup.member_roles?.[memberId] || 'player'}
                        </div>
                        {isAdmin && (
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => removeMember.mutate({ groupId: selectedGroup.id, userId: memberId })}
                            disabled={removeMember.isPending}
                          >
                            Remove
                          </Button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
