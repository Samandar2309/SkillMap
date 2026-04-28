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

  const answeredCount = useMemo(() => questions.filter((q) => answers[q.id]).length, [answers, questions]);
  const completionPercent = questions.length > 0 ? Math.round((answeredCount / questions.length) * 100) : 0;

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
    <section className="space-y-5">
      <article className="relative overflow-hidden rounded-[2rem] border border-white/60 bg-gradient-to-br from-sky-600 via-blue-600 to-emerald-500 p-6 text-white shadow-xl">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(255,255,255,0.22),_transparent_28%),radial-gradient(circle_at_bottom_left,_rgba(15,23,42,0.16),_transparent_26%)]" />
        <div className="relative flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold sm:text-3xl">Qobiliyat testi</h1>
            <p className="mt-2 text-sm text-white/90">Savollar backenddan olinadi va javoblar real API orqali yuboriladi.</p>
            <div className="mt-3 inline-flex items-center rounded-full bg-white/20 px-3 py-1 text-xs font-semibold">
              {answeredCount}/{questions.length} savol javoblandi
            </div>
          </div>
          <button
            className="rounded-2xl border border-white/40 bg-white/15 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/25"
            onClick={onReload}
          >
            Savollarni yangilash
          </button>
        </div>
        <div className="relative mt-4">
          <div className="h-2 rounded-full bg-white/25">
            <div className="h-full rounded-full bg-white" style={{ width: `${completionPercent}%` }} />
          </div>
          <p className="mt-2 text-xs font-semibold uppercase tracking-[0.14em] text-white/85">Bajarilish: {completionPercent}%</p>
        </div>
      </article>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-2xl border border-sky-100 bg-sky-50 p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-sky-700">Maslahat</p>
          <p className="mt-1 text-sm text-slate-700">Savolni oxirigacha o'qib, eng yaqin tajribangizga mos javobni tanlang.</p>
        </div>
        <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-emerald-700">Namuna yondashuv</p>
          <p className="mt-1 text-sm text-slate-700">Agar mavzu yangi bo'lsa boshlang'ich variantni, amaliy ishlatgan bo'lsangiz yuqori variantni tanlang.</p>
        </div>
        <div className="rounded-2xl border border-amber-100 bg-amber-50 p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-amber-700">Natija</p>
          <p className="mt-1 text-sm text-slate-700">Test natijasiga qarab yo'l xaritangiz moslashtiriladi.</p>
        </div>
      </div>

      {loading && <div className="rounded-2xl border border-border bg-white p-6">Savollar yuklanmoqda...</div>}
      {!!error && <div className="rounded-xl border border-red-300 bg-red-50 p-4 text-red-600">{error}</div>}

      {!loading && !error && questions.length === 0 && (
        <div className="rounded-xl border border-border p-6 text-muted-foreground">Savollar mavjud emas.</div>
      )}

      {questions.map((question) => (
        <article key={question.id} className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md space-y-3">
          <div className="flex items-start justify-between gap-3">
            <p className="font-semibold text-slate-900">{question.text}</p>
            <span className="rounded-full border border-sky-200 bg-sky-50 px-2.5 py-1 text-[11px] font-semibold text-sky-700">
              #{question.id}
            </span>
          </div>
          <p className="text-xs text-muted-foreground">Yo'nalish: {question.skill_category}</p>
          <p className="rounded-xl border border-blue-100 bg-blue-50 px-3 py-2 text-xs text-blue-700">
            Javob namunasi: agar bu mavzuda hali tajriba kam bo'lsa boshlang'ich variantni, amalda ishlatgan bo'lsangiz yuqori variantni tanlang.
          </p>
          <div className="space-y-2.5">
            {question.choices.map((choice) => (
              <label
                key={choice.id}
                className={[
                  "flex cursor-pointer items-center gap-3 rounded-xl border px-3 py-2 text-sm transition",
                  answers[question.id] === choice.id
                    ? "border-emerald-300 bg-emerald-50 text-emerald-800"
                    : "border-slate-200 bg-slate-50 text-slate-700 hover:border-sky-300 hover:bg-sky-50",
                ].join(" ")}
              >
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
        </article>
      ))}

      {submitError && <p className="text-sm text-red-500">{submitError}</p>}
      {result !== null && <p className="text-sm text-green-600">Test topshirildi. Natija: {result} ball</p>}

      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-slate-600">Tayyor bo'lsangiz testni yuboring. Natija asosida tizim keyingi bosqichlarni moslaydi.</p>
          <button
            onClick={submit}
            disabled={!isComplete || loading}
            className="rounded-xl bg-gradient-to-r from-sky-600 to-emerald-500 px-5 py-2.5 text-sm font-semibold text-white shadow-md transition hover:brightness-105 disabled:opacity-60"
          >
            Testni yuborish
          </button>
        </div>
      </div>
    </section>
  );
}

