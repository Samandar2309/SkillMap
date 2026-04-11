import { useMemo, useState } from 'react';

import type { Question } from '../api/types';

interface TestCenterProps {
  questions: Question[];
  loading: boolean;
  error: string;
  onReload: () => Promise<void>;
  onSubmit: (answers: { question_id: number; choice_id: number }[]) => Promise<{ totalScore: number }>;
}

export function TestCenter({ questions, loading, error, onReload, onSubmit }: TestCenterProps) {
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [submitError, setSubmitError] = useState('');
  const [result, setResult] = useState<number | null>(null);

  const isComplete = useMemo(() => {
    return questions.length > 0 && questions.every((q) => answers[q.id]);
  }, [answers, questions]);

  const submit = async () => {
    try {
      setSubmitError('');
      const payload = questions.map((q) => ({
        question_id: q.id,
        choice_id: answers[q.id],
      }));
      const response = await onSubmit(payload);
      setResult(response.totalScore);
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : 'Testni yuborib bo\'lmadi.');
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1>Aptitude test</h1>
          <p className="text-muted-foreground">Savollar backenddan olinadi</p>
        </div>
        <button className="rounded-lg border border-border px-3 py-2" onClick={onReload}>
          Yangilash
        </button>
      </div>

      {loading && <div className="rounded-xl border border-border p-6">Savollar yuklanmoqda...</div>}
      {!!error && <div className="rounded-xl border border-red-300 bg-red-50 p-4 text-red-600">{error}</div>}

      {!loading && !error && questions.length === 0 && (
        <div className="rounded-xl border border-border p-6 text-muted-foreground">Savollar mavjud emas.</div>
      )}

      {questions.map((question) => (
        <div key={question.id} className="rounded-xl border border-border p-5 space-y-3">
          <p className="font-medium">{question.text}</p>
          <p className="text-xs text-muted-foreground">{question.skill_category}</p>
          <div className="space-y-2">
            {question.choices.map((choice) => (
              <label key={choice.id} className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name={`q-${question.id}`}
                  checked={answers[question.id] === choice.id}
                  onChange={() => setAnswers((prev) => ({ ...prev, [question.id]: choice.id }))}
                />
                {choice.text}
              </label>
            ))}
          </div>
        </div>
      ))}

      {submitError && <p className="text-sm text-red-500">{submitError}</p>}
      {result !== null && <p className="text-sm text-green-600">Test topshirildi. Ball: {result}</p>}

      <button
        onClick={submit}
        disabled={!isComplete || loading}
        className="rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
      >
        Testni yuborish
      </button>
    </div>
  );
}

