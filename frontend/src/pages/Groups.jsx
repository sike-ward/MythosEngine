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
  can_read: 'Can Read',
  can_write: 'Can Write',
  can_delete: 'Can Delete',
  can_invite: 'Can Invite',
  can_admin: 'Can Admin',
};
const DEFAULT_PERMISSIONS = {
  can_read: true,
  can_write: false,
  can_delete: false,
  can_invite: false,
  can_admin: false,
};

export default function Groups({ user }) {
  const qc = useQueryClient();
  const isAdmin = user?.roles?.includes?.('admin');

  const [selectedGroupId, setSelectedGroupId] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createDesc, setCreateDesc] = useState('');
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editPerms, setEditPerms] = useState({ ...DEFAULT_PERMISSIONS });
  const [memberEmail, setMemberEmail] = useState('');

  const { data: groupList = [] } = useQuery({ queryKey: ['groups'], queryFn: groups.list });
  const { data: userList = [] } = useQuery({
    queryKey: ['users'],
    queryFn: users.list,
    enabled: isAdmin,
  });

  const selectedGroup = useMemo(
    () => groupList.find((g) => g.id === selectedGroupId) ?? null,
    [groupList, selectedGroupId]
  );

  useEffect(() => {
    setEditName(selectedGroup?.name ?? '');
    setEditDesc(selectedGroup?.description ?? '');
    setEditPerms({ ...DEFAULT_PERMISSIONS, ...(selectedGroup?.permissions ?? {}) });
    setMemberEmail('');
  }, [selectedGroup?.id]);

  const refresh = () => qc.invalidateQueries({ queryKey: ['groups'] });

  const createGroup = useMutation({
    mutationFn: () =>
      groups.create({ name: createName.trim(), description: createDesc.trim() || undefined }),
    onSuccess: (group) => {
      setCreateName('');
      setCreateDesc('');
      setShowCreate(false);
      setSelectedGroupId(group.id);
      refresh();
      toast.success('Group created');
    },
    onError: (err) => toast.error(err.message),
  });

  const saveGroup = useMutation({
    mutationFn: () =>
      groups.update(selectedGroupId, {
        name: editName.trim(),
        description: editDesc.trim() || undefined,
        permissions: editPerms,
      }),
    onSuccess: () => {
      refresh();
      toast.success('Group saved');
    },
    onError: (err) => toast.error(err.message),
  });

  const deleteGroup = useMutation({
    mutationFn: () => groups.remove(selectedGroupId),
    onSuccess: () => {
      setSelectedGroupId(null);
      refresh();
      toast.success('Group deleted');
    },
    onError: (err) => toast.error(err.message),
  });

  const addMember = useMutation({
    mutationFn: (userId) => groups.addMember(selectedGroupId, userId),
    onSuccess: () => {
      setMemberEmail('');
      refresh();
      toast.success('Member added');
    },
    onError: (err) => toast.error(err.message),
  });

  const removeMember = useMutation({
    mutationFn: (userId) => groups.removeMember(selectedGroupId, userId),
    onSuccess: () => {
      refresh();
      toast.success('Member removed');
    },
    onError: (err) => toast.error(err.message),
  });

  const matchedUser = useMemo(() => {
    const q = memberEmail.trim().toLowerCase();
    return q ? userList.find((u) => u.email.toLowerCase() === q) ?? null : null;
  }, [userList, memberEmail]);

  const memberDetails = useMemo(
    () =>
      (selectedGroup?.members ?? []).map((id) => {
        const found = userList.find((u) => u.id === id);
        return found ?? { id, email: id, username: '' };
      }),
    [selectedGroup, userList]
  );

  return (
    <div className="p-10 space-y-6">
      <SectionHeader title="Groups" subtitle="View and manage groups and their permissions." />

      <div className="grid lg:grid-cols-[280px,1fr] gap-6">
        {/* Left panel — group list */}
        <Card className="p-4 space-y-3">
          {isAdmin && !showCreate && (
            <Button className="w-full" onClick={() => setShowCreate(true)}>
              + New Group
            </Button>
          )}

          {showCreate && (
            <div className="space-y-2 pb-3 border-b border-border-subtle">
              <Input
                label="Name"
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
                placeholder="Campaign name…"
              />
              <Input
                label="Description"
                value={createDesc}
                onChange={(e) => setCreateDesc(e.target.value)}
                placeholder="Optional"
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => createGroup.mutate()}
                  disabled={createName.trim().length < 2}
                >
                  Create
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => {
                    setShowCreate(false);
                    setCreateName('');
                    setCreateDesc('');
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}

          <div className="space-y-1">
            {groupList.map((group) => (
              <button
                key={group.id}
                onClick={() => setSelectedGroupId(group.id)}
                className={`w-full text-left rounded-xl px-4 py-3 transition-all ${
                  selectedGroupId === group.id
                    ? 'bg-accent-soft text-accent font-semibold'
                    : 'bg-elevated text-txt hover:bg-hover'
                }`}
              >
                <div className="truncate">{group.name}</div>
                <div className="text-xs text-txt-muted">
                  {group.members?.length ?? 0} member
                  {group.members?.length !== 1 ? 's' : ''}
                </div>
              </button>
            ))}
            {!groupList.length && (
              <p className="text-sm text-txt-muted px-2 py-2">No groups yet.</p>
            )}
          </div>
        </Card>

        {/* Right panel — group detail */}
        <Card className="p-6">
          {!selectedGroup ? (
            <p className="text-txt-muted text-sm">Select a group to view details.</p>
          ) : (
            <div className="space-y-6">
              {/* Name / Description */}
              <div className="space-y-3">
                <Input
                  label="Name"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  disabled={!isAdmin}
                />
                <Input
                  label="Description"
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  disabled={!isAdmin}
                />
              </div>

              {/* Permissions */}
              <div>
                <p className="text-sm font-semibold text-txt mb-3">Permissions</p>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {PERMISSION_KEYS.map((key) => (
                    <label
                      key={key}
                      className={`flex items-center gap-3 rounded-xl px-4 py-3 bg-elevated select-none ${
                        isAdmin ? 'cursor-pointer' : 'cursor-default opacity-70'
                      }`}
                    >
                      <input
                        type="checkbox"
                        className="accent-accent w-4 h-4"
                        checked={!!editPerms[key]}
                        onChange={(e) =>
                          isAdmin && setEditPerms((p) => ({ ...p, [key]: e.target.checked }))
                        }
                        disabled={!isAdmin}
                      />
                      <span className="text-sm text-txt">{PERMISSION_LABELS[key]}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Save / Delete — admin only */}
              {isAdmin && (
                <div className="flex gap-3">
                  <Button onClick={() => saveGroup.mutate()}>Save</Button>
                  <Button variant="danger" onClick={() => deleteGroup.mutate()}>
                    Delete Group
                  </Button>
                </div>
              )}

              {/* Members */}
              <div>
                <p className="text-sm font-semibold text-txt mb-3">
                  Members ({memberDetails.length})
                </p>

                <div className="space-y-2">
                  {memberDetails.map(({ id, email, username }) => (
                    <div key={id} className="flex items-center gap-3 bg-elevated rounded-xl px-4 py-3">
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-txt truncate">{email || id}</div>
                        {username && username !== email && (
                          <div className="text-xs text-txt-muted truncate">{username}</div>
                        )}
                      </div>
                      {isAdmin && (
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => removeMember.mutate(id)}
                        >
                          Remove
                        </Button>
                      )}
                    </div>
                  ))}
                  {!memberDetails.length && (
                    <p className="text-sm text-txt-muted">No members yet.</p>
                  )}
                </div>

                {/* Add Member — admin only */}
                {isAdmin && (
                  <div className="mt-4 space-y-1">
                    <div className="flex gap-2 items-end">
                      <div className="flex-1">
                        <Input
                          label="Add member by email"
                          value={memberEmail}
                          onChange={(e) => setMemberEmail(e.target.value)}
                          placeholder="user@example.com"
                        />
                      </div>
                      <Button
                        onClick={() => matchedUser && addMember.mutate(matchedUser.id)}
                        disabled={!matchedUser}
                      >
                        Add
                      </Button>
                    </div>
                    {memberEmail && !matchedUser && (
                      <p className="text-xs text-txt-muted">No user found with that email.</p>
                    )}
                    {matchedUser && (
                      <p className="text-xs text-accent">Found: {matchedUser.username}</p>
                    )}
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
