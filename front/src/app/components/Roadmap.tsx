import { useMemo } from 'react';

import type { RoadmapView } from '../api/mappers';

interface RoadmapProps {
  roadmap: RoadmapView | null;
  loading: boolean;
  error: string;
  onToggleTask: (taskId: number, nextCompleted: boolean) => Promise<void>;
}

export function Roadmap({ roadmap, loading, error, onToggleTask }: RoadmapProps) {
  const completion = useMemo(() => {
    if (!roadmap) {
      return 0;
    }
    const tasks = roadmap.phases.flatMap((p) => p.tasks);
    if (tasks.length === 0) {
      return 0;
    }
    const completed = tasks.filter((t) => t.isCompleted).length;
    return Math.round((completed / tasks.length) * 100);
  }, [roadmap]);

  if (loading) {
    return <div className="p-8">Roadmap yuklanmoqda...</div>;
  }

  if (error) {
    return <div className="p-8 text-red-500">{error}</div>;
  }

  if (!roadmap) {
    return <div className="p-8 text-muted-foreground">Roadmap hali mavjud emas. AI generation ni ishga tushiring.</div>;
  }

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="mb-2">{roadmap.title}</h1>
        <p className="text-muted-foreground">
          Taxminiy muddat: {roadmap.estimatedMonths} oy | Umumiy progress: {completion}%
        </p>
      </div>

      {roadmap.phases.map((phase) => (
        <div key={phase.id} className="rounded-xl border border-border p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3>
              {phase.order}. {phase.title}
            </h3>
            <span className="text-sm text-muted-foreground">{phase.isCompleted ? 'Completed' : 'In progress'}</span>
          </div>

          <div className="space-y-2">
            {phase.tasks.map((task) => (
              <label key={task.id} className="flex items-start gap-3 rounded-lg bg-muted p-3">
                <input
                  type="checkbox"
                  checked={task.isCompleted}
                  onChange={() => void onToggleTask(task.id, !task.isCompleted)}
                />
                <div className="flex-1">
                  <p className="font-medium">{task.title}</p>
                  {task.description && <p className="text-sm text-muted-foreground">{task.description}</p>}
                  {task.resourceLink && (
                    <a className="text-sm text-primary underline" href={task.resourceLink} target="_blank" rel="noreferrer">
                      Resurs havolasi
                    </a>
                  )}
                </div>
              </label>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
