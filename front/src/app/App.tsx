import { lazy, Suspense } from "react";

import { AuthScreen } from "../components/features/auth-screen";
import { OnboardingIntroPanel } from "../components/features/onboarding-intro-panel";
import { OnboardingPanel } from "../components/features/onboarding-panel";
import { VerifyEmailPage } from "../components/features/verify-email-page.tsx";
import { AppShell } from "../components/layout/app-shell";
import { Button } from "../components/ui/button";
import { ErrorState } from "../components/ui/error-state";
import { LoadingState } from "../components/ui/loading-state";
import { NotificationCenter } from "../components/ui/notification-center";
import { SectionErrorBoundary } from "../components/ui/section-error-boundary";
import { SkipLink } from "../components/ui/skip-link";
import { useSectionShortcuts } from "../hooks/use-section-shortcuts";
import { getErrorMessage } from "../lib/error-utils";
import { preloadSection } from "./section-preload";
import { useAppController } from "./use-app-controller";

function isAuthRoute(pathname: string): boolean {
  return (
    pathname === "/login" ||
    pathname === "/register" ||
    pathname === "/check-email" ||
    pathname === "/onboarding-intro"
  );
}

const DashboardOverview = lazy(() =>
  import("../components/features/dashboard-overview").then((module) => ({ default: module.DashboardOverview })),
);
const RoadmapPanel = lazy(() =>
  import("../components/features/roadmap-panel").then((module) => ({ default: module.RoadmapPanel })),
);
const TasksPanel = lazy(() =>
  import("../components/features/tasks-panel").then((module) => ({ default: module.TasksPanel })),
);
const ProgressPanel = lazy(() =>
  import("../components/features/progress-panel").then((module) => ({ default: module.ProgressPanel })),
);
const MotivationPanel = lazy(() =>
  import("../components/features/motivation-panel").then((module) => ({ default: module.MotivationPanel })),
);

export default function App() {
  const controller = useAppController();
  const currentPathname = window.location.pathname;
  const normalizedPathname = currentPathname.replace(/\/+$/, "") || "/";

  useSectionShortcuts({
    enabled: controller.isAuthenticated && !controller.showOnboarding,
    onSelectSection: controller.setSection,
  });

  if (controller.isBootstrapping) {
    return <LoadingState label="Ilova ishga tushirilmoqda..." />;
  }

  if (normalizedPathname === "/verify-email") {
    return (
      <>
        <SkipLink />
        <VerifyEmailPage
          onVerifyEmail={controller.verifyEmail}
          onResendVerification={controller.resendVerification}
          isVerifyingEmail={controller.isVerifyingEmail}
          isResendingVerification={controller.isResendingVerification}
        />
        <NotificationCenter />
      </>
    );
  }

  if (normalizedPathname === "/onboarding-intro") {
    return (
      <>
        <SkipLink />
        <div className="min-h-screen bg-background px-4 py-10 sm:px-6 lg:px-8">
          {controller.isAuthenticated && controller.showOnboarding ? (
            controller.showOnboardingIntro ? (
              <OnboardingIntroPanel
                userName={controller.user?.fullName ?? controller.user?.email}
                onContinue={controller.continueOnboardingFromIntro}
              />
            ) : (
              <OnboardingPanel
                isSubmitting={controller.isOnboardingSubmitting}
                profile={controller.onboardingProfile}
                isProfileLoading={controller.onboardingLoading}
                onSubmitStep={controller.submitOnboardingStep}
              />
            )
          ) : (
            <OnboardingIntroPanel
              userName={controller.user?.fullName ?? controller.user?.email}
              continueLabel="Kirish va davom etish"
              onContinue={() => {
                window.localStorage.setItem("auth.pendingIntroSeen", "1");
                window.location.assign(`/login?verified=1&next=onboarding`);
              }}
            />
          )}
        </div>
        <NotificationCenter />
      </>
    );
  }

  if (normalizedPathname === "/onboarding" && !controller.isAuthenticated) {
    return (
      <>
        <SkipLink />
        <OnboardingIntroPanel
          onContinue={() => window.location.assign("/login?verified=1&next=onboarding")}
          continueLabel="Kirish va davom etish"
        />
        <NotificationCenter />
      </>
    );
  }

  if (isAuthRoute(normalizedPathname) || !controller.isAuthenticated) {
    return (
      <>
        <SkipLink />
        <AuthScreen
          onLogin={controller.login}
          onRegister={controller.register}
          onVerifyEmail={controller.verifyEmail}
          onResendVerification={controller.resendVerification}
          isLoading={controller.isAuthLoading}
          isVerifyingEmail={controller.isVerifyingEmail}
          isResendingVerification={controller.isResendingVerification}
          errorMessage={controller.authError}
        />
        <NotificationCenter />
      </>
    );
  }

  if (controller.showOnboarding) {
    return (
      <>
        <SkipLink />
        <div className="min-h-screen bg-background px-4 py-10 sm:px-6 lg:px-8">
          {controller.showOnboardingIntro ? (
            <OnboardingIntroPanel
              userName={controller.user?.fullName ?? controller.user?.email}
              onContinue={controller.continueOnboardingFromIntro}
            />
          ) : (
            <OnboardingPanel
              isSubmitting={controller.isOnboardingSubmitting}
              profile={controller.onboardingProfile}
              isProfileLoading={controller.onboardingLoading}
              onSubmitStep={controller.submitOnboardingStep}
            />
          )}
        </div>
        <NotificationCenter />
      </>
    );
  }

  if (controller.workspaceLoading) {
    return <LoadingState label="O'quv ish maydoni yuklanmoqda..." />;
  }

  if (controller.workspaceError) {
    return (
      <>
        <SkipLink />
        <div className="min-h-screen bg-background px-4 py-10 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl">
            <ErrorState
              title="Ish maydonini yuklab bo'lmadi"
              message={getErrorMessage(controller.workspaceError)}
              action={
                <Button
                  type="button"
                  onClick={() => window.location.reload()}
                  variant="danger"
                >
                  Qayta yuklash
                </Button>
              }
            />
          </div>
        </div>
        <NotificationCenter />
      </>
    );
  }

  return (
    <>
      <SkipLink />
      <AppShell
        section={controller.section}
        onSectionChange={controller.setSection}
        onSectionPrefetch={preloadSection}
        user={controller.user}
        onRefreshCurrentSection={controller.refreshCurrentSection}
        isRefreshingCurrentSection={controller.isRefreshingCurrentSection}
        onLogout={controller.logout}
        isLoggingOut={controller.isLoggingOut}
      >
        <SectionErrorBoundary>
          <Suspense fallback={<LoadingState label="Bo'lim yuklanmoqda..." />}>
            {controller.section === "dashboard" ? (
              <DashboardOverview
                userName={controller.user?.fullName ?? controller.user?.email ?? "Foydalanuvchi"}
                roadmap={controller.roadmap}
                tasks={controller.tasks}
                motivationCard={controller.motivationCard}
                recommendations={controller.recommendations}
                recommendationsLoading={controller.recommendationsLoading}
                recommendationsError={controller.recommendationsError}
                weeklyPoints={controller.weeklyPoints.map((point) => ({
                  weekLabel: point.weekLabel,
                  completedTasks: point.completedTasks,
                  totalTasks: point.totalTasks,
                  learningMinutes: point.learningMinutes,
                  completionRate: point.completionRate,
                }))}
                weeklyAverage={controller.weeklyAverage}
                monthlyAverage={controller.monthlyAverage}
              />
            ) : null}

            {controller.section === "roadmap" ? (
              <RoadmapPanel
                roadmap={controller.roadmap}
                isLoading={controller.roadmapLoading}
                errorMessage={controller.roadmapError}
                onGenerate={controller.generateRoadmap}
                isGenerating={controller.isGeneratingRoadmap}
                onRetry={controller.refetchRoadmap}
              />
            ) : null}

            {controller.section === "tasks" ? (
              <TasksPanel
                tasks={controller.tasks}
                dateLabel={controller.dateLabel}
                isLoading={controller.tasksLoading}
                errorMessage={controller.tasksError}
                isCompleting={controller.isCompletingTask}
                onComplete={controller.completeTask}
                onRetry={controller.refetchTasks}
              />
            ) : null}

            {controller.section === "progress" ? (
              <ProgressPanel
                weekly={controller.weeklyPoints.map((point) => ({
                  label: point.weekLabel,
                  completionRate: point.completionRate,
                  completedTasks: point.completedTasks,
                  totalTasks: point.totalTasks,
                  learningMinutes: point.learningMinutes,
                }))}
                monthly={controller.monthlyPoints.map((point) => ({
                  label: point.monthLabel,
                  completionRate: point.completionRate,
                  completedTasks: point.completedTasks,
                  totalTasks: point.totalTasks,
                  learningMinutes: point.learningMinutes,
                }))}
                weeklyAverage={controller.weeklyAverage}
                monthlyAverage={controller.monthlyAverage}
                isLoading={controller.progressLoading}
                errorMessage={controller.progressError}
                onRetry={controller.refetchProgress}
              />
            ) : null}

            {controller.section === "motivation" ? (
              <MotivationPanel
                card={controller.motivationCard}
                isLoading={controller.motivationLoading}
                errorMessage={controller.motivationError}
                isSendingEvent={controller.isSendingMotivationEvent}
                onEvent={controller.sendMotivationEvent}
                onRetry={controller.refetchMotivation}
              />
            ) : null}
          </Suspense>
        </SectionErrorBoundary>
      </AppShell>
      <NotificationCenter />
    </>
  );
}
