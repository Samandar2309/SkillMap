import type {
  DashboardStats,
  Profile,
  Recommendation,
  Roadmap,
} from './types';

export interface ProfileView {
  direction: string;
  englishLevel: string;
  currentGoal: string;
  isOnboarded: boolean;
}

export interface RoadmapTaskView {
  id: number;
  title: string;
  description: string;
  resourceLink: string;
  isCompleted: boolean;
}

export interface RoadmapPhaseView {
  id: number;
  title: string;
  order: number;
  isCompleted: boolean;
  tasks: RoadmapTaskView[];
}

export interface RoadmapView {
  id: number;
  title: string;
  estimatedMonths: number;
  isCompleted: boolean;
  phases: RoadmapPhaseView[];
}

export interface DashboardStatsView {
  totalPoints: number;
  currentStreak: number;
  longestStreak: number;
  roadmapCompletionPercentage: number;
  completedTasksCount: number;
  totalTasksCount: number;
}

export interface RecommendationView {
  title: string;
  description: string;
  url: string;
  resourceType: string;
  direction: string;
  minEnglishLevel: string;
  maxEnglishLevel: string;
  priority: number;
}

export function mapProfile(profile: Profile): ProfileView {
  return {
    direction: profile.direction,
    englishLevel: profile.english_level,
    currentGoal: profile.current_goal,
    isOnboarded: profile.is_onboarded,
  };
}

export function mapRoadmap(roadmap: Roadmap): RoadmapView {
  return {
    id: roadmap.id,
    title: roadmap.title,
    estimatedMonths: roadmap.estimated_months,
    isCompleted: roadmap.is_completed,
    phases: roadmap.phases.map((phase) => ({
      id: phase.id,
      title: phase.title,
      order: phase.order,
      isCompleted: phase.is_completed,
      tasks: phase.tasks.map((task) => ({
        id: task.id,
        title: task.title,
        description: task.description,
        resourceLink: task.resource_link,
        isCompleted: task.is_completed,
      })),
    })),
  };
}

export function mapStats(stats: DashboardStats): DashboardStatsView {
  return {
    totalPoints: stats.progress.total_points,
    currentStreak: stats.progress.current_streak,
    longestStreak: stats.progress.longest_streak,
    roadmapCompletionPercentage: stats.roadmap_completion_percentage,
    completedTasksCount: stats.completed_tasks_count,
    totalTasksCount: stats.total_tasks_count,
  };
}

export function mapRecommendation(item: Recommendation): RecommendationView {
  return {
    title: item.title,
    description: item.description,
    url: item.url,
    resourceType: item.resource_type,
    direction: item.direction,
    minEnglishLevel: item.min_english_level,
    maxEnglishLevel: item.max_english_level,
    priority: item.priority,
  };
}

