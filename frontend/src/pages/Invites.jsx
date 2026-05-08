import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import SectionHeader from '@/components/SectionHeader';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Badge from '@/components/Badge';
import { invites } from '@/api';

export default function Invites({ user }) {
  const isAdmin = user?.roles?.includes?.('admin');

  if (!isAdmin) {
    return (
      <div className="p-10">
        <p className="text-txt-muted">Owner access required.</p>
      </div>
    );
  }

  return <InviteManagement />;
}

function InviteManagement() {
  const qc = useQueryClient();
  const { data: inviteList = [], isLoading } = useQuery({
    queryKey: ['invites'],
    queryFn: invites.list,
  });

  const generateMutation = useMutation({
    mutationFn: () => invites.generate(),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['invites'] });
      navigator.clipboard.writeText(data.code).catch(() => {});
      toast.success(`Invite code copied to clipboard: ${data.code}`);
    },
    onError: (err) => toast.error(err.message),
  });

  const revokeMutation = useMutation({
    mutationFn: (code) => invites.revoke(code),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invites'] });
      toast.success('Invite revoked');
    },
    onError: (err) => toast.error(err.message),
  });

  const statusVariant = (status) => {
    if (status === 'Active') return 'active';
    if (status === 'Expired') return 'expired';
    return 'disabled';
  };

  return (
    <div className="p-10 space-y-6">
      <div className="flex items-center justify-between">
        <SectionHeader
          title="Invite Management"
          subtitle="Generate one-time invite codes for new users to register."
        />
        <Button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
        >
          {generateMutation.isPending ? 'Generating...' : 'Generate Invite'}
        </Button>
      </div>

      <Card className="p-0 overflow-hidden">
        {isLoading ? (
          <div className="p-6 text-center text-txt-muted text-sm">Loading invites...</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-elevated">
              <tr className="text-left text-txt-muted">
                <th className="px-6 py-4 font-medium">Code</th>
                <th className="px-6 py-4 font-medium">Created</th>
                <th className="px-6 py-4 font-medium">Expires</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Used By</th>
                <th className="px-6 py-4 font-medium"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {inviteList.map((invite) => (
                <tr key={invite.id} className="text-txt hover:bg-elevated/40 transition-colors">
                  <td className="px-6 py-4">
                    <code className="font-mono text-accent text-xs bg-elevated px-2 py-1 rounded tracking-wider">
                      {invite.code}
                    </code>
                  </td>
                  <td className="px-6 py-4 text-txt-muted">
                    {new Date(invite.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-txt-muted">
                    {new Date(invite.expires_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4">
                    <Badge label={invite.status} variant={statusVariant(invite.status)} />
                  </td>
                  <td className="px-6 py-4 text-txt-muted">
                    {invite.used_by ?? '—'}
                  </td>
                  <td className="px-6 py-4">
                    <Button
                      variant="danger"
                      size="sm"
                      disabled={invite.is_used || !invite.is_active || revokeMutation.isPending}
                      onClick={() => revokeMutation.mutate(invite.code)}
                    >
                      Revoke
                    </Button>
                  </td>
                </tr>
              ))}
              {!inviteList.length && (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center text-txt-muted">
                    No invites yet. Generate one to get started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
