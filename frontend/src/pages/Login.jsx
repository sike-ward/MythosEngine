import { useState } from 'react';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Input from '@/components/Input';
import { auth, setToken } from '@/api';

// Must mirror server-side validate_password_strength rules (Item 54)
const SPECIAL_CHARS = /[!@#$%^&*\-_]/;
function validatePassword(pw) {
  if (pw.length < 8) return 'At least 8 characters required';
  if (!/[A-Z]/.test(pw)) return 'At least 1 uppercase letter required';
  if (!/[0-9]/.test(pw)) return 'At least 1 number required';
  if (!SPECIAL_CHARS.test(pw)) return 'At least 1 special character required (!@#$%^&*-_)';
  return null;
}

export default function Login({ onLogin, needsSetup = false }) {
  // Modes: 'login', 'register', 'setup'
  const [mode, setMode] = useState(needsSetup ? 'setup' : 'login');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Login form
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Register form
  const [regEmail, setRegEmail] = useState('');
  const [regUsername, setRegUsername] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regPwHint, setRegPwHint] = useState(null);
  const [regInviteCode, setRegInviteCode] = useState('');

  // Setup form (first-run admin)
  const [setupEmail, setSetupEmail] = useState('');
  const [setupUsername, setSetupUsername] = useState('');
  const [setupPassword, setSetupPassword] = useState('');
  const [setupPwHint, setSetupPwHint] = useState(null);
  const [setupConfirm, setSetupConfirm] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await auth.login(loginEmail, loginPassword);
      setToken(data.token);
      onLogin(data.token, data.user, data.exp ?? null);
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    const hint = validatePassword(regPassword);
    if (hint) { setError(hint); return; }
    setLoading(true);
    try {
      const data = await auth.register(regEmail, regUsername, regPassword, regInviteCode);
      setToken(data.token);
      onLogin(data.token, data.user, data.exp ?? null);
    } catch (err) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSetup = async (e) => {
    e.preventDefault();
    setError('');

    if (setupPassword !== setupConfirm) {
      setError('Passwords do not match');
      return;
    }
    const hint = validatePassword(setupPassword);
    if (hint) { setError(hint); return; }

    setLoading(true);
    try {
      const data = await auth.setup(setupEmail, setupUsername, setupPassword);
      setToken(data.token);
      onLogin(data.token, data.user, data.exp ?? null);
    } catch (err) {
      setError(err.message || 'Setup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen bg-base flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="text-4xl mb-4">⚡</div>
          <h1 className="text-2xl font-bold text-txt mb-2">MythosEngine</h1>
        </div>

        {/* ── Setup Mode (first run) ──────────────────────────────── */}
        {mode === 'setup' && (
          <>
            <h2 className="text-xl font-bold text-txt mb-2">Welcome to MythosEngine</h2>
            <p className="text-txt-secondary text-sm mb-6">
              Create your admin account to get started.
            </p>

            {error && (
              <div className="mb-4 p-3 rounded-lg bg-danger/10 border border-danger/20">
                <p className="text-danger text-sm">{error}</p>
              </div>
            )}

            <form onSubmit={handleSetup} className="space-y-4">
              <Input
                label="Email"
                type="email"
                placeholder="admin@example.com"
                value={setupEmail}
                onChange={(e) => setSetupEmail(e.target.value)}
                required
              />
              <Input
                label="Username"
                type="text"
                placeholder="Your name"
                value={setupUsername}
                onChange={(e) => setSetupUsername(e.target.value)}
                required
              />
              <div>
                <Input
                  label="Password"
                  type="password"
                  placeholder="Min 8 chars, uppercase, number, special"
                  value={setupPassword}
                  onChange={(e) => {
                    setSetupPassword(e.target.value);
                    setSetupPwHint(e.target.value ? validatePassword(e.target.value) : null);
                  }}
                  required
                />
                {setupPwHint && (
                  <p className="text-danger text-xs mt-1">{setupPwHint}</p>
                )}
              </div>
              <Input
                label="Confirm Password"
                type="password"
                placeholder="Repeat password"
                value={setupConfirm}
                onChange={(e) => setSetupConfirm(e.target.value)}
                required
              />
              <Button type="submit" variant="primary" className="w-full" disabled={loading}>
                {loading ? 'Creating account...' : 'Create Admin Account'}
              </Button>
            </form>
          </>
        )}

        {/* ── Login Mode ─────────────────────────────────────────── */}
        {mode === 'login' && (
          <>
            <h2 className="text-xl font-bold text-txt mb-2">Welcome back</h2>
            <p className="text-txt-secondary text-sm mb-6">
              Sign in to your account to continue
            </p>

            {error && (
              <div className="mb-4 p-3 rounded-lg bg-danger/10 border border-danger/20">
                <p className="text-danger text-sm">{error}</p>
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
              <Input
                label="Email"
                type="email"
                placeholder="you@example.com"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                required
              />
              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                required
              />
              <Button type="submit" variant="primary" className="w-full" disabled={loading}>
                {loading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-txt-muted text-sm">
                Have an invite code?{' '}
                <button
                  onClick={() => { setMode('register'); setError(''); }}
                  className="text-accent hover:text-accent/80 font-medium transition"
                >
                  Register
                </button>
              </p>
            </div>
          </>
        )}

        {/* ── Register Mode ──────────────────────────────────────── */}
        {mode === 'register' && (
          <>
            <h2 className="text-xl font-bold text-txt mb-2">Create account</h2>
            <p className="text-txt-secondary text-sm mb-6">
              Join the worlds of MythosEngine
            </p>

            {error && (
              <div className="mb-4 p-3 rounded-lg bg-danger/10 border border-danger/20">
                <p className="text-danger text-sm">{error}</p>
              </div>
            )}

            <form onSubmit={handleRegister} className="space-y-4">
              <Input
                label="Invite Code"
                type="text"
                placeholder="XXXX-XXXX-XXXX"
                value={regInviteCode}
                onChange={(e) => setRegInviteCode(e.target.value)}
                required
              />
              <Input
                label="Email"
                type="email"
                placeholder="you@example.com"
                value={regEmail}
                onChange={(e) => setRegEmail(e.target.value)}
                required
              />
              <Input
                label="Username"
                type="text"
                placeholder="your_username"
                value={regUsername}
                onChange={(e) => setRegUsername(e.target.value)}
                required
              />
              <div>
                <Input
                  label="Password"
                  type="password"
                  placeholder="Min 8 chars, uppercase, number, special"
                  value={regPassword}
                  onChange={(e) => {
                    setRegPassword(e.target.value);
                    setRegPwHint(e.target.value ? validatePassword(e.target.value) : null);
                  }}
                  required
                />
                {regPwHint && (
                  <p className="text-danger text-xs mt-1">{regPwHint}</p>
                )}
              </div>
              <Button type="submit" variant="primary" className="w-full" disabled={loading}>
                {loading ? 'Creating account...' : 'Register'}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-txt-muted text-sm">
                Already have an account?{' '}
                <button
                  onClick={() => { setMode('login'); setError(''); }}
                  className="text-accent hover:text-accent/80 font-medium transition"
                >
                  Sign In
                </button>
              </p>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
