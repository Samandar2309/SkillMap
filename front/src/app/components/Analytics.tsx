import type { DashboardStatsView } from '../api/mappers';

interface AnalyticsProps {
  stats: DashboardStatsView | null;
  loading: boolean;
  error: string;
}

export function Analytics({ stats, loading, error }: AnalyticsProps) {
  if (loading) {
    return <div className="p-8">Analytics yuklanmoqda...</div>;
  }

  if (error) {
    return <div className="p-8 text-red-500">{error}</div>;
  }

  if (!stats) {
    return <div className="p-8 text-muted-foreground">Analytics ma'lumoti topilmadi.</div>;
  }

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="mb-2">Statistika va tahlil</h1>
        <p className="text-muted-foreground">Backend hisob-kitoblari asosida real analitika</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Metric title="Yo'l xarita bajarilishi" value={`${stats.roadmapCompletionPercentage}%`} />
        <Metric title="Jami ball" value={`${stats.totalPoints}`} />
        <Metric title="Bajarilgan vazifalar" value={`${stats.completedTasksCount}`} />
        <Metric title="Joriy seriya" value={`${stats.currentStreak}`} />
      </div>

      <div className="rounded-xl border border-border p-5">
        <h3 className="mb-3">Progress tafsiloti</h3>
        <ul className="space-y-2 text-sm">
          <li>Eng uzun seriya: <strong>{stats.longestStreak}</strong></li>
          <li>Jami vazifalar: <strong>{stats.totalTasksCount}</strong></li>
          <li>Bajarilish nisbati: <strong>{stats.completedTasksCount}/{stats.totalTasksCount}</strong></li>
        </ul>
      </div>
    </div>
  );
}

function Metric({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="text-sm text-muted-foreground">{title}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}
