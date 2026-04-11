import { useMemo, useState } from 'react';

interface OnboardingProps {
  loading: boolean;
  error: string;
  onSubmit: (payload: {
    direction: string;
    english_level: string;
    current_goal: string;
  }) => Promise<void>;
}

const ENGLISH_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

export function Onboarding({ loading, error, onSubmit }: OnboardingProps) {
  const [direction, setDirection] = useState('');
  const [englishLevel, setEnglishLevel] = useState('B1');
  const [currentGoal, setCurrentGoal] = useState('');

  const disabled = useMemo(() => {
    return !direction.trim() || !englishLevel.trim() || !currentGoal.trim() || loading;
  }, [currentGoal, direction, englishLevel, loading]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-2xl rounded-2xl border border-border bg-card p-6 space-y-4">
        <h2>Onboarding</h2>
        <p className="text-sm text-muted-foreground">
          Ma'lumot yuborilgach, `/profiles/onboard/` chaqiriladi va keyin `/ai/generate/` + polling ishga tushadi.
        </p>

        <div className="space-y-2">
          <label className="text-sm">Direction</label>
          <input
            className="w-full rounded-lg border border-border bg-background px-3 py-2"
            placeholder="Masalan: backend"
            value={direction}
            onChange={(e) => setDirection(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm">English level</label>
          <select
            className="w-full rounded-lg border border-border bg-background px-3 py-2"
            value={englishLevel}
            onChange={(e) => setEnglishLevel(e.target.value)}
          >
            {ENGLISH_LEVELS.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <label className="text-sm">Current goal</label>
          <textarea
            className="w-full rounded-lg border border-border bg-background px-3 py-2"
            rows={5}
            value={currentGoal}
            onChange={(e) => setCurrentGoal(e.target.value)}
          />
        </div>

        {!!error && <p className="text-sm text-red-500">{error}</p>}

        <button
          className="rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
          disabled={disabled}
          onClick={() =>
            void onSubmit({
              direction,
              english_level: englishLevel,
              current_goal: currentGoal,
            })
          }
        >
          {loading ? 'Yaratilmoqda...' : 'Onboardingni yakunlash va roadmap yaratish'}
        </button>
      </div>
    </div>
  );
}
