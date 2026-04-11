import { Trophy, Flame, Star, Target } from 'lucide-react';
import type { ReactNode } from 'react';

import type { DashboardStatsView } from '../api/mappers';
import type { LeaderboardEntry } from '../api/types';

interface DashboardProps {
  stats: DashboardStatsView | null;
  leaderboard: LeaderboardEntry[];
  loading: boolean;
  error: string;
}

export function Dashboard({ stats, leaderboard, loading, error }: DashboardProps) {
  if (loading) {
    return <div className="p-8">Dashboard yuklanmoqda...</div>;
  }

  if (error) {
    return <div className="p-8 text-red-500">{error}</div>;
  }

  if (!stats) {
    return <div className="p-8 text-muted-foreground">Statistika topilmadi.</div>;
  }

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="mb-2">Bosh sahifa</h1>
        <p className="text-muted-foreground">Backend progress endpoint asosida real ko'rsatkichlar</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card icon={<Star className="w-5 h-5" />} label="Jami XP" value={String(stats.totalPoints)} />
        <Card icon={<Flame className="w-5 h-5" />} label="Joriy streak" value={String(stats.currentStreak)} />
        <Card icon={<Target className="w-5 h-5" />} label="Bajarilgan task" value={`${stats.completedTasksCount}/${stats.totalTasksCount}`} />
        <Card icon={<Trophy className="w-5 h-5" />} label="Roadmap progress" value={`${stats.roadmapCompletionPercentage}%`} />
      </div>

      <div className="rounded-xl border border-border p-5">
        <h3 className="mb-4">Leaderboard</h3>
        {leaderboard.length === 0 && <p className="text-sm text-muted-foreground">Hozircha ma'lumot yo'q.</p>}
        <div className="space-y-2">
          {leaderboard.map((entry, index) => (
            <div key={entry.email} className="flex items-center justify-between rounded-lg bg-muted px-3 py-2">
              <span className="text-sm">#{index + 1} {entry.email}</span>
              <span className="text-sm font-medium">{entry.total_points} XP</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Card({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="mb-3 flex items-center gap-2 text-primary">
        {icon}
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}
