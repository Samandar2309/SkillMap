import { useState } from 'react';

interface AuthPanelProps {
  onLogin: (email: string, password: string) => Promise<void>;
  onRegister: (email: string, password: string, passwordConfirm: string) => Promise<void>;
  onVerify: (uid: string, token: string) => Promise<void>;
  loading: boolean;
  error: string;
}

export function AuthPanel({ onLogin, onRegister, onVerify, loading, error }: AuthPanelProps) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [uid, setUid] = useState('');
  const [verifyToken, setVerifyToken] = useState('');

  const submit = async () => {
    if (isRegister) {
      await onRegister(email, password, passwordConfirm);
      return;
    }
    await onLogin(email, password);
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-lg space-y-4">
        <h2>{isRegister ? 'Ro\'yxatdan o\'tish' : 'Kirish'}</h2>
        <p className="text-sm text-muted-foreground">SkillMap API bilan real integratsiya</p>

        <input
          className="w-full rounded-lg border border-border bg-background px-3 py-2"
          placeholder="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          className="w-full rounded-lg border border-border bg-background px-3 py-2"
          placeholder="Parol"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {isRegister && (
          <input
            className="w-full rounded-lg border border-border bg-background px-3 py-2"
            placeholder="Parolni tasdiqlang"
            type="password"
            value={passwordConfirm}
            onChange={(e) => setPasswordConfirm(e.target.value)}
          />
        )}

        {error && <p className="text-sm text-red-500">{error}</p>}

        <button
          className="w-full rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
          disabled={loading}
          onClick={submit}
        >
          {loading ? 'Yuklanmoqda...' : isRegister ? 'Ro\'yxatdan o\'tish' : 'Kirish'}
        </button>

        <button
          className="w-full rounded-lg border border-border px-4 py-2"
          onClick={() => setIsRegister((prev) => !prev)}
        >
          {isRegister ? 'Akkauntingiz bormi? Kirish' : 'Akkaunt yo\'qmi? Ro\'yxatdan o\'ting'}
        </button>

        <div className="border-t border-border pt-4 space-y-2">
          <p className="text-xs text-muted-foreground">Email verify (ixtiyoriy):</p>
          <input
            className="w-full rounded-lg border border-border bg-background px-3 py-2"
            placeholder="uid"
            value={uid}
            onChange={(e) => setUid(e.target.value)}
          />
          <input
            className="w-full rounded-lg border border-border bg-background px-3 py-2"
            placeholder="token"
            value={verifyToken}
            onChange={(e) => setVerifyToken(e.target.value)}
          />
          <button
            className="w-full rounded-lg border border-border px-4 py-2"
            disabled={loading || !uid || !verifyToken}
            onClick={() => void onVerify(uid, verifyToken)}
          >
            Verify email
          </button>
        </div>
      </div>
    </div>
  );
}
