import type {
  ApiErrorPayload,
  AuthResponse,
  DashboardStats,
  GenerateRoadmapResponse,
  LeaderboardEntry,
  OnboardingRequest,
  Profile,
  Question,
  RecommendationListResponse,
  Roadmap,
  RoadmapTaskStatus,
  TestSubmitRequest,
  TestSubmitResponse,
  User,
} from './types';

const API_BASE_URL =
  (import.meta as ImportMeta & { env?: Record<string, string> }).env?.VITE_API_BASE_URL ||
  'http://localhost:8000/api/v1';

export class ApiError extends Error {
  status: number;
  payload?: ApiErrorPayload;

  constructor(message: string, status: number, payload?: ApiErrorPayload) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  token?: string,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers || {}),
    },
  });

  const isJson = response.headers.get('content-type')?.includes('application/json');
  const payload = isJson ? ((await response.json()) as ApiErrorPayload) : undefined;

  if (!response.ok) {
    const detail = payload?.detail;
    throw new ApiError(detail ? String(detail) : `Request failed with ${response.status}`, response.status, payload);
  }

  if (!isJson) {
    return {} as T;
  }

  return payload as T;
}

export const api = {
  register: (email: string, password: string, passwordConfirm: string) =>
    request<{ message: string; user: User }>('/accounts/register/', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        password_confirm: passwordConfirm,
      }),
    }),

  login: (email: string, password: string) =>
    request<AuthResponse>('/accounts/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  verifyEmail: (uid: string, token: string) =>
    request<{ detail: string }>('/accounts/verify-email/', {
      method: 'POST',
      body: JSON.stringify({ uid, token }),
    }),

  me: (token: string) => request<User>('/accounts/me/', { method: 'GET' }, token),

  getProfile: (token: string) => request<Profile>('/profiles/me/', { method: 'GET' }, token),

  onboard: (token: string, payload: OnboardingRequest) =>
    request<Profile>(
      '/profiles/onboard/',
      {
        method: 'PATCH',
        body: JSON.stringify(payload),
      },
      token,
    ),

  generateRoadmap: (token: string) =>
    request<GenerateRoadmapResponse>('/roadmaps/generate', { method: 'POST' }, token),

  roadmapTaskStatus: (token: string, taskId: string) =>
    request<RoadmapTaskStatus>(`/ai/tasks/${taskId}/`, { method: 'GET' }, token),

  getRoadmap: (token: string) => request<Roadmap>('/roadmaps/active', { method: 'GET' }, token),

  updateTask: (token: string, taskId: number, isCompleted: boolean) =>
    request('/roadmaps/tasks/' + taskId + '/', {
      method: 'PATCH',
      body: JSON.stringify({ is_completed: isCompleted }),
    }, token),

  myStats: (token: string) => request<DashboardStats>('/progress/my-stats/', { method: 'GET' }, token),

  leaderboard: (token: string) =>
    request<LeaderboardEntry[]>('/progress/leaderboard/', { method: 'GET' }, token),

  recommendations: (token: string) =>
    request<RecommendationListResponse>('/recommendations/my/', { method: 'GET' }, token),

  questions: (token: string) => request<Question[]>('/tests/questions/', { method: 'GET' }, token),

  submitTest: (token: string, payload: TestSubmitRequest) =>
    request<TestSubmitResponse>('/tests/submit/', { method: 'POST', body: JSON.stringify(payload) }, token),
};
