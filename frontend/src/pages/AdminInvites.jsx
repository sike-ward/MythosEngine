import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import SectionHeader from '@/components/SectionHeader';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Input from '@/components/Input';
import { invites } from '@/api';

export default function AdminInvites() {
  const qc = useQueryClient();
  const [ttlDays, setTtlDays] = useState('7');
  const [maxUses, setMaxUses] = useState('1');
  const { data: inviteList = [] } = useQuery({ queryKey: ['invites'], queryFn: invites.list });

  const generateInvite = useMutation({
    mutationFn: () => invites.generate({ ttl_days: Number(ttlDays) || 7, max_uses: Number(maxUses) || 1 }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invites'] });
      toast.success('Invite generated');
    },
    onError: (err) => toast.error(err.message),
  });

  const revokeInvite = useMutation({
    mutationFn: invites.revoke,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invites'] });
      toast.success('Invite revoked');
    },
    onError: (err) => toast.error(err.message),
  });

  return (
    <div className="p-10 space-y-6">
      <SectionHeader title="🎟️ Admin Invites" subtitle="Manage invite codes, expiry, and usage limits." />
      <Card className="p-6 space-y-4">
        <div className="grid md:grid-cols-2 gap-4">
          <Input label="TTL (days)" type="number" min="1" value={ttlDays} onChange={(e) => setTtlDays(e.target.value)} />
          <Input label="Max uses" type="number" min="1" value={maxUses} onChange={(e) => setMaxUses(e.target.value)} />
        </div>
        <Button onClick={() => generateInvite.mutate()}>Generate invite</Button>
      </Card>

      <Card className="p-6">
        <div className="space-y-3">
          {inviteList.map((invite) => (
            <div key={invite.id} className="flex items-center gap-3 bg-elevated rounded-xl px-4 py-3">
              <code className="flex-1 text-sm text-txt">{invite.code}</code>
              <span className="text-xs text-txt-muted">Expires {new Date(invite.expires_at).toLocaleString()}</span>
              <span className="text-xs text-txt-muted">
                {invite.use_count}/{invite.max_uses} uses
              </span>
              <span className="text-xs font-semibold text-txt">{invite.status}</span>
              <Button variant="secondary" size="sm" onClick={() => navigator.clipboard.writeText(invite.code).then(() => toast.success('Copied'))}>
                Copy
              </Button>
              {invite.is_active && invite.status === 'Active' && (
                <Button variant="danger" size="sm" onClick={() => revokeInvite.mutate(invite.id)}>
                  Revoke
                </Button>
              )}
            </div>
          ))}
          {!inviteList.length && <p className="text-sm text-txt-muted">No invites yet.</p>}
        </div>
      </Card>
    </div>
  );
}
