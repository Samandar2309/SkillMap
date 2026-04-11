import { useCallback, useEffect, useMemo, useState } from 'react';
import { ThemeProvider } from 'next-themes';

import { api, ApiError } from './api/client';
import { mapProfile, mapRecommendation, mapRoadmap, mapStats, type DashboardStatsView, type ProfileView, type RecommendationView, type RoadmapView } from './api/mappers';
import type { LeaderboardEntry, Question, User } from './api/types';
import { AuthPanel } from './components/AuthPanel';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { Roadmap } from './components/Roadmap';
import { Resources } from './components/Resources';
import { Analytics } from './components/Analytics';
import { Profile } from './components/Profile';
import { Onboarding } from './components/Onboarding';
import { TestCenter } from './components/TestCenter';

type ViewId = 'dashboard' | 'roadmap' | 'resources' | 'analytics' | 'profile' | 'tests';

const ACCESS_KEY = 'skillmap_access_token';

function parseError(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'Noma\'lum xatolik yuz berdi.';
}

async function pollTaskUntilDone(token: string, taskId: string): Promise<void> {
  const maxAttempts = 12;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const status = await api.roadmapTaskStatus(token, taskId);
    if (status.state === 'SUCCESS') {
      return;
    }
    if (status.state === 'FAILURE') {
      throw new Error(status.error || 'AI roadmap generation muvaffaqiyatsiz yakunlandi.');
    }
    const timeoutMs = Math.min(1000 * 2 ** (attempt - 1), 8000);
    await new Promise((resolve) => setTimeout(resolve, timeoutMs));
  }
  throw new Error('AI roadmap generation timeout. Keyinroq qayta urinib ko\'ring.');
}

function AppContent() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [mounted, setMounted] = useState(false);

  const [token, setToken] = useState<string | null>(localStorage.getItem(ACCESS_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<ProfileView | null>(null);

  const [roadmap, setRoadmap] = useState<RoadmapView | null>(null);
  const [stats, setStats] = useState<DashboardStatsView | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendationView[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);

  const [currentView, setCurrentView] = useState<ViewId>('dashboard');

  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState('');

  const [appLoading, setAppLoading] = useState(false);
  const [appError, setAppError] = useState('');

  const [onboardingLoading, setOnboardingLoading] = useState(false);
  const [onboardingError, setOnboardingError] = useState('');

  const [questionsLoading, setQuestionsLoading] = useState(false);
  const [questionsError, setQuestionsError] = useState('');

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) {
      return;
    }
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [mounted, theme]);

  const loadQuestions = useCallback(async () => {
    if (!token) {
      return;
    }
    setQuestionsLoading(true);
    setQuestionsError('');
    try {
      const data = await api.questions(token);
      setQuestions(data);
    } catch (error) {
      setQuestionsError(parseError(error));
    } finally {
      setQuestionsLoading(false);
    }
  }, [token]);

  const loadIntegratedData = useCallback(async (authToken: string) => {
    setAppLoading(true);
    setAppError('');

    try {
      const [me, profileData, statsData, leaderboardData, recommendationsData] = await Promise.all([
        api.me(authToken),
        api.getProfile(authToken),
        api.myStats(authToken),
        api.leaderboard(authToken),
        api.recommendations(authToken),
      ]);

      setUser(me);
      setProfile(mapProfile(profileData));
      setStats(mapStats(statsData));
      setLeaderboard(leaderboardData);
      setRecommendations(recommendationsData.results.map(mapRecommendation));

      try {
        const roadmapData = await api.getRoadmap(authToken);
        setRoadmap(mapRoadmap(roadmapData));
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          setRoadmap(null);
        } else {
          throw error;
        }
      }

      if (profileData.is_onboarded) {
        await loadQuestions();
      }
    } catch (error) {
      setAppError(parseError(error));
    } finally {
      setAppLoading(false);
    }
  }, [loadQuestions]);

  useEffect(() => {
    if (!token) {
      return;
    }
    void loadIntegratedData(token);
  }, [token, loadIntegratedData]);

  const login = useCallback(async (email: string, password: string) => {
    setAuthLoading(true);
    setAuthError('');
    try {
      const response = await api.login(email, password);
      localStorage.setItem(ACCESS_KEY, response.access);
      setToken(response.access);
    } catch (error) {
      setAuthError(parseError(error));
    } finally {
      setAuthLoading(false);
    }
  }, []);

  const register = useCallback(async (email: string, password: string, passwordConfirm: string) => {
    setAuthLoading(true);
    setAuthError('');
    try {
      await api.register(email, password, passwordConfirm);
      setAuthError('Ro\'yxatdan o\'tish muvaffaqiyatli. Endi login qiling va email verify qiling.');
    } catch (error) {
      setAuthError(parseError(error));
    } finally {
      setAuthLoading(false);
    }
  }, []);

  const verifyEmail = useCallback(async (uid: string, verifyToken: string) => {
    setAuthLoading(true);
    setAuthError('');
    try {
      const response = await api.verifyEmail(uid, verifyToken);
      setAuthError(response.detail);
    } catch (error) {
      setAuthError(parseError(error));
    } finally {
      setAuthLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(ACCESS_KEY);
    setToken(null);
    setUser(null);
    setProfile(null);
    setRoadmap(null);
    setStats(null);
    setLeaderboard([]);
    setRecommendations([]);
    setQuestions([]);
  }, []);

  const submitOnboarding = useCallback(async (payload: { direction: string; english_level: string; current_goal: string }) => {
    if (!token) {
      return;
    }

    setOnboardingLoading(true);
    setOnboardingError('');
    try {
      const updatedProfile = await api.onboard(token, payload);
      setProfile(mapProfile(updatedProfile));

      const generated = await api.generateRoadmap(token);
      await pollTaskUntilDone(token, generated.task_id);

      const roadmapData = await api.getRoadmap(token);
      setRoadmap(mapRoadmap(roadmapData));
      await loadIntegratedData(token);
      setCurrentView('roadmap');
    } catch (error) {
      setOnboardingError(parseError(error));
    } finally {
      setOnboardingLoading(false);
    }
  }, [loadIntegratedData, token]);

  const toggleTask = useCallback(async (taskId: number, nextCompleted: boolean) => {
    if (!token) {
      return;
    }
    await api.updateTask(token, taskId, nextCompleted);
    const roadmapData = await api.getRoadmap(token);
    setRoadmap(mapRoadmap(roadmapData));
    const statsData = await api.myStats(token);
    setStats(mapStats(statsData));
  }, [token]);

  const submitTest = useCallback(async (answers: { question_id: number; choice_id: number }[]) => {
    if (!token) {
      throw new Error('Authorization yo\'q.');
    }
    const response = await api.submitTest(token, { answers });
    const statsData = await api.myStats(token);
    setStats(mapStats(statsData));
    return { totalScore: response.total_score };
  }, [token]);

  const showOnboarding = useMemo(() => !!user && !!profile && !profile.isOnboarded, [profile, user]);

  if (!mounted) {
    return null;
  }

  if (!token) {
    return (
      <AuthPanel
        onLogin={login}
        onRegister={register}
        onVerify={verifyEmail}
        loading={authLoading}
        error={authError}
      />
    );
  }

  if (showOnboarding) {
    return <Onboarding loading={onboardingLoading} error={onboardingError} onSubmit={submitOnboarding} />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar
        currentView={currentView}
        onViewChange={(view) => setCurrentView(view as ViewId)}
        theme={theme}
        toggleTheme={() => setTheme((prev) => (prev === 'light' ? 'dark' : 'light'))}
        onLogout={logout}
      />
      <main className="flex-1 overflow-y-auto">
        {appError && <div className="m-4 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">{appError}</div>}
        {currentView === 'dashboard' && (
          <Dashboard stats={stats} leaderboard={leaderboard} loading={appLoading} error={appError} />
        )}
        {currentView === 'roadmap' && (
          <Roadmap roadmap={roadmap} loading={appLoading} error={appError} onToggleTask={toggleTask} />
        )}
        {currentView === 'resources' && (
          <Resources recommendations={recommendations} loading={appLoading} error={appError} />
        )}
        {currentView === 'analytics' && <Analytics stats={stats} loading={appLoading} error={appError} />}
        {currentView === 'profile' && <Profile user={user} profile={profile} loading={appLoading} error={appError} />}
        {currentView === 'tests' && (
          <TestCenter
            questions={questions}
            loading={questionsLoading}
            error={questionsError}
            onReload={loadQuestions}
            onSubmit={submitTest}
          />
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="light">
      <AppContent />
    </ThemeProvider>
  );
}