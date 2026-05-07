import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Input from '@/components/Input';
import { auth, setToken } from '@/api';
import { loginSchema, registerSchema } from '@/schemas/auth';

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
  const [mode, setMode] = useState(needsSetup ? 'setup' : 'login');
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState('');

  // Login form with Zod validation
  const loginForm = useForm({ resolver: zodResolver(loginSchema) });
  // Register form with Zod validation
  const registerForm = useForm({ resolver: zodResolver(registerSchema) });

  // Setup form (first-run admin) — simple controlled state
  const [setupEmail, setSetupEmail] = useState('');
  const [setupUsername, setSetupUsername] = useState('');
  const [setupPassword, setSetupPassword] = useState('');
  const [setupPwHint, setSetupPwHint] = useState(null);
  const [setupConfirm, setSetupConfirm] = useState('');
  const [setupError, setSetupError] = useState('');

  const switchMode = (next) => {
    setMode(next);
    setApiError('');
    loginForm.clearErrors();
    registerForm.clearErrors();
  };

  const handleLogin = loginForm.handleSubmit(async ({ email, password }) => {
    setApiError('');
    setLoading(true);
    try {
      const data = await auth.login(email, password);
      setToken(data.token);
      onLogin(data.token, data.user, data.exp ?? null);
    } catch (err) {
      setApiError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  });

  const handleRegister = registerForm.handleSubmit(
    async ({ email, password, displayName, inviteCode }) => {
      setApiError('');
      setLoading(true);
      try {
        const data = await auth.register(email, displayName, password, inviteCode);
        setToken(data.token);
        onLogin(data.token, data.user);
      } catch (err) {
        setApiError(err.message || 'Registration failed');
      } finally {
        setLoading(false);
      }
    }
  );

  const handleSetup = async (e) => {
    e.preventDefault();
    setSetupError('');
    if (setupPassword !== setupConfirm) {
      setSetupError('Passwords do not match');
      return;
    }
    const hint = validatePassword(setupPassword);
    if (hint) { setSetupError(hint); return; }
    setLoading(true);
    try {
      const data = await auth.setup(setupEmail, setupUsername, setupPassword);
      setToken(data.token);
      onLogin(data.token, data.user, data.exp ?? null);
    } catch (err) {
      setSetupError(err.message || 'Setup failed');
    } finally {
      setLoading(false);
    }
  };

  const FieldError = ({ message }) =>
    message ? <p className="text-danger text-xs mt-1">{message}</p> : null;

  const ApiErrorBox = ({ msg }) =>
    msg ? (
      <div className="mb-4 p-3 rounded-lg bg-danger/10 border border-danger/20">
        <p className="text-danger text-sm">{msg}</p>
      </div>
    ) : null;

  return (
    <div className="h-screen w-screen bg-base flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="text-4xl mb-4">⚡</div>
          <h1 className="text-2xl font-bold text-txt mb-2">MythosEngine</h1>
        </div>

        {/* ── Setup Mode ── */}
        {mode === 'setup' && (
          <>
            <h2 className="text-xl font-bold text-txt mb-2">Welcome to MythosEngine</h2>
            <p className="text-txt-secondary text-sm mb-6">Create your admin account to get started.</p>
            <ApiErrorBox msg={setupError} />
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

        {/* ── Login Mode ── */}
        {mode === 'login' && (
          <>
            <h2 className="text-xl font-bold text-txt mb-2">Welcome back</h2>
            <p className="text-txt-secondary text-sm mb-6">Sign in to your account to continue</p>
            <ApiErrorBox msg={apiError} />
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Input
                  label="Email"
                  type="email"
                  placeholder="you@example.com"
                  {...loginForm.register('email')}
                />
                <FieldError message={loginForm.formState.errors.email?.message} />
              </div>
              <div>
                <Input
                  label="Password"
                  type="password"
                  placeholder="••••••••"
                  {...loginForm.register('password')}
                />
                <FieldError message={loginForm.formState.errors.password?.message} />
              </div>
              <Button type="submit" variant="primary" className="w-full" disabled={loading}>
                {loading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>
            <div className="mt-6 text-center">
              <p className="text-txt-muted text-sm">
                Have an invite code?{' '}
                <button onClick={() => switchMode('register')} className="text-accent hover:text-accent/80 font-medium transition">
                  Register
                </button>
              </p>
            </div>
          </>
        )}

        {/* ── Register Mode ── */}
        {mode === 'register' && (
          <>
            <h2 className="text-xl font-bold text-txt mb-2">Create account</h2>
            <p className="text-txt-secondary text-sm mb-6">Join the worlds of MythosEngine</p>
            <ApiErrorBox msg={apiError} />
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <Input label="Invite Code" type="text" placeholder="XXXX-XXXX-XXXX" {...registerForm.register('inviteCode')} />
                <FieldError message={registerForm.formState.errors.inviteCode?.message} />
              </div>
              <div>
                <Input label="Email" type="email" placeholder="you@example.com" {...registerForm.register('email')} />
                <FieldError message={registerForm.formState.errors.email?.message} />
              </div>
              <div>
                <Input label="Display Name" type="text" placeholder="your_username" {...registerForm.register('displayName')} />
                <FieldError message={registerForm.formState.errors.displayName?.message} />
              </div>
              <div>
                <Input label="Password" type="password" placeholder="••••••••" {...registerForm.register('password')} />
                <FieldError message={registerForm.formState.errors.password?.message} />
              </div>
              <Button type="submit" variant="primary" className="w-full" disabled={loading}>
                {loading ? 'Creating account...' : 'Register'}
              </Button>
            </form>
            <div className="mt-6 text-center">
              <p className="text-txt-muted text-sm">
                Already have an account?{' '}
                <button onClick={() => switchMode('login')} className="text-accent hover:text-accent/80 font-medium transition">
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
