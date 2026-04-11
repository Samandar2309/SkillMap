export interface User {
  id: number;
  email: string;
  is_verified: boolean;
  created_at: string;
}

export interface AuthResponse {
  refresh: string;
  access: string;
  user: User;
}

export interface Profile {
  user: number;
  direction: string;
  english_level: string;
  current_goal: string;
  is_onboarded: boolean;
  created_at: string;
  updated_at: string;
}

export interface OnboardingRequest {
  direction: string;
  english_level: string;
  current_goal: string;
}

export interface RoadmapTask {
  id: number;
  phase: number;
  title: string;
  description: string;
  resource_link: string;
  is_completed: boolean;
}

export interface RoadmapPhase {
  id: number;
  roadmap: number;
  title: string;
  order: number;
  is_completed: boolean;
  tasks: RoadmapTask[];
}

export interface Roadmap {
  id: number;
  user: number;
  title: string;
  estimated_months: number;
  is_completed: boolean;
  created_at: string;
  phases: RoadmapPhase[];
}

export interface DashboardStats {
  progress: {
    total_points: number;
    current_streak: number;
    longest_streak: number;
  };
  roadmap_completion_percentage: number;
  completed_tasks_count: number;
  total_tasks_count: number;
}

export interface LeaderboardEntry {
  email: string;
  total_points: number;
  current_streak: number;
}

export interface Recommendation {
  direction: string;
  min_english_level: string;
  max_english_level: string;
  title: string;
  description: string;
  url: string;
  resource_type: string;
  priority: number;
}

export interface RecommendationListResponse {
  count: number;
  results: Recommendation[];
}

export interface QuestionChoice {
  id: number;
  text: string;
}

export interface Question {
  id: number;
  text: string;
  skill_category: string;
  choices: QuestionChoice[];
}

export interface TestSubmitRequest {
  answers: { question_id: number; choice_id: number }[];
}

export interface TestSubmitResponse {
  attempt_id: number;
  total_score: number;
}

export interface GenerateRoadmapResponse {
  task_id: string;
  status: string;
}

export interface RoadmapTaskStatus {
  task_id: string;
  state: string;
  status: string;
  result?: unknown;
  error?: string;
}

export interface ApiErrorPayload {
  detail?: string;
  [key: string]: unknown;
}

