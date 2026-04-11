# Full-Stack Analysis Report

## Summary

- Overall consistency score (0-100): **34**
- Critical issues count: **4**
- Medium issues count: **6**
- Minor issues count: **3**

---

## Critical Issues (Must Fix)

- [Frontend does not call backend APIs at all]
  - Description
    - Frontend renders static/mock data and does not perform `fetch`/`axios` calls to backend routes.
    - This blocks real auth, onboarding, testing, roadmap, progress, and recommendations flows.
  - Affected files
    - `front/src/app/components/Onboarding.tsx:53-56`
    - `front/src/app/components/Roadmap.tsx:21-119`
    - `front/src/app/components/Dashboard.tsx:5-34`
    - `front/src/app/components/Analytics.tsx:5-59`
    - `front/src/app/components/Profile.tsx:5-18`
    - `front/src/app/components/Resources.tsx:17-84`
  - Frontend vs Backend difference
    - Frontend: local arrays/state only, no HTTP integration.
    - Backend: complete REST API exposed under `api/v1` in `main/urls.py:20-26`.
  - Suggested fix
    - Add a shared API client and replace static data with backend calls in each screen.

- [Authentication flow is not wired in frontend for JWT-protected backend]
  - Description
    - Backend uses JWT authentication globally, while frontend does not request/store/send tokens.
    - Protected endpoints will return 401/403 when integration starts.
  - Affected files
    - `main/settings.py:171-175`
    - `accounts/urls.py:7-10`
    - `profiles/views.py:22`
    - `test_system/views.py:19,33`
    - `roadmaps/views.py:23,52`
    - `progress/views.py:24,59`
    - `recommendations/views.py:26`
    - `ai_engine/views.py:32,112`
    - `front/src/app/**/*`
  - Frontend vs Backend difference
    - Frontend: no login/register call path, no `Authorization: Bearer <token>`.
    - Backend: JWT required for almost all business endpoints.
  - Suggested fix
    - Implement login (`POST /api/v1/accounts/login/`) and persist `access` token; attach Bearer token in every authenticated request.

- [Onboarding completion UX does not execute backend-required flow]
  - Description
    - Onboarding currently completes using `setTimeout`, not by updating profile and generating roadmap.
  - Affected files
    - `front/src/app/components/Onboarding.tsx:52-56`
    - `profiles/urls.py:8`
    - `ai_engine/urls.py:7`
  - Frontend vs Backend difference
    - Frontend: fake completion delay.
    - Backend expected flow: update onboarding (`PUT/PATCH /api/v1/profiles/onboard/`) then trigger roadmap (`POST /api/v1/ai/generate/`).
  - Suggested fix
    - Replace timeout with sequential API calls and error handling for 400/401/503 responses.

- [Roadmap/task data model in UI does not match backend contract]
  - Description
    - Frontend `Task.id` is typed as string and task shape differs from backend task serializer.
  - Affected files
    - `front/src/app/components/Roadmap.tsx:5-19`
    - `roadmaps/urls.py:8`
    - `roadmaps/serializers.py:8-43`
  - Frontend vs Backend difference
    - Frontend: `id: string`, `progress`, `deadline`, `resources[]`.
    - Backend: task update route expects integer `pk`; task fields include `is_completed`, `resource_link`, no `progress` percentage field.
  - Suggested fix
    - Align TypeScript interfaces with backend response and compute progress client-side from completion status if needed.

---

## Medium Issues

- [Naming mismatch risk: camelCase UI fields vs snake_case backend serializers]
  - Description
    - Frontend onboarding state uses keys like `careerGoal`; backend expects snake_case (`current_goal`, `english_level`).
  - Affected files
    - `front/src/app/components/Onboarding.tsx:35-43`
    - `profiles/serializers.py:56-57`
  - Frontend vs Backend difference
    - UI naming conventions and backend contract naming are not aligned.
  - Suggested fix
    - Add explicit DTO mapping layer before request submit.

- [Frontend collects onboarding fields not accepted by backend endpoint]
  - Description
    - UI asks for name/university/major/year/skills/interests, but onboarding API accepts only 3 fields.
  - Affected files
    - `front/src/app/components/Onboarding.tsx:35-43`
    - `profiles/serializers.py:56`
  - Frontend vs Backend difference
    - Extra frontend fields would be ignored/rejected if sent directly.
  - Suggested fix
    - Either add backend support for those fields or limit submitted payload strictly to accepted fields.

- [No frontend handling for backend validation/error payloads]
  - Description
    - Backend returns structured errors (`detail`, field errors, 400/401/403/404/502/503), but UI has no API error states.
  - Affected files
    - `accounts/views.py:119-136`
    - `ai_engine/views.py:74-106,121-124,142-147`
    - `roadmaps/views.py:29-32,64-66`
    - `front/src/app/**/*`
  - Frontend vs Backend difference
    - Frontend has no error boundaries/messages tied to API response codes.
  - Suggested fix
    - Standardize API error parser and show user-facing messages per status code.

- [Protected test endpoints require onboarding permission, not represented in UI guards]
  - Description
    - Backend restricts test endpoints to onboarded users via custom permission.
  - Affected files
    - `test_system/views.py:19,33`
    - `test_system/permissions.py:7-18`
    - `front/src/app/App.tsx:45-47`
  - Frontend vs Backend difference
    - Frontend onboarding flag is local UI state; backend permission uses persisted `Profile.is_onboarded`.
  - Suggested fix
    - Gate routes using server truth (`GET /api/v1/profiles/me/`) rather than local boolean.

- [No async task polling integration for AI roadmap generation]
  - Description
    - Backend uses Celery task IDs and status polling endpoint; frontend has no polling logic.
  - Affected files
    - `ai_engine/views.py:66-71,117-141`
    - `ai_engine/urls.py:7-8`
    - `front/src/app/components/Onboarding.tsx:80-109`
  - Frontend vs Backend difference
    - Frontend uses fixed 3-second animation; backend provides task lifecycle states.
  - Suggested fix
    - Poll `GET /api/v1/ai/tasks/{task_id}/` until `SUCCESS`/`FAILURE` with retry/backoff.

- [Dashboard/analytics metrics are static and not aligned to backend stats endpoints]
  - Description
    - UI numbers are hardcoded; backend computes real stats and leaderboard.
  - Affected files
    - `front/src/app/components/Dashboard.tsx:5-34`
    - `front/src/app/components/Analytics.tsx:5-59`
    - `progress/urls.py:7-8`
    - `progress/views.py:21-53,56-71`
  - Frontend vs Backend difference
    - Frontend assumptions can diverge from backend-calculated values.
  - Suggested fix
    - Source dashboard widgets from `/api/v1/progress/my-stats/` and `/api/v1/progress/leaderboard/`.

---

## Minor Issues

- [Potential trailing-slash sensitivity not represented in frontend routing assumptions]
  - Description
    - Django routes are defined with trailing slash; client must preserve exact paths if `APPEND_SLASH` behavior differs by environment.
  - Affected files
    - `main/urls.py:20-26`
    - `accounts/urls.py`, `profiles/urls.py`, `test_system/urls.py`, `ai_engine/urls.py`, `roadmaps/urls.py`, `progress/urls.py`, `recommendations/urls.py`
  - Frontend vs Backend difference
    - No client code yet; risk appears once requests are added.
  - Suggested fix
    - Centralize endpoint constants with trailing slash in one API module.

- [No client-side caching strategy for read-heavy endpoints]
  - Description
    - Endpoints like roadmap, recommendations, and leaderboard are suitable for stale-while-revalidate cache patterns.
  - Affected files
    - `front/src/app/**/*`
    - `roadmaps/urls.py:7`
    - `recommendations/urls.py:8`
    - `progress/urls.py:8`
  - Frontend vs Backend difference
    - Backend supports reads; frontend does not implement data cache layer.
  - Suggested fix
    - Introduce React Query/SWR for caching and background refresh.

- [Resource card schema differs from recommendations API schema]
  - Description
    - UI resource cards use `thumbnail`, `rating`, `duration`, but backend recommendation response does not provide them.
  - Affected files
    - `front/src/app/components/Resources.tsx:5-15,17-84`
    - `recommendations/serializers.py:6-33`
  - Frontend vs Backend difference
    - Frontend expects richer media metadata than backend currently returns.
  - Suggested fix
    - Either extend backend serializer or adjust UI card model/fallback rendering.

---

## API Mapping Table

| Endpoint | Frontend Usage | Backend Implementation | Status |
| -------- | -------------- | ---------------------- | ------ |
| `/api/v1/accounts/register/` | Not used | `POST` (`accounts/urls.py:7`, `accounts/views.py:41`) | Unused by frontend |
| `/api/v1/accounts/login/` | Not used | `POST` (`accounts/urls.py:8`, `accounts/views.py:68`) | Unused by frontend |
| `/api/v1/accounts/verify-email/` | Not used | `GET`, `POST` (`accounts/urls.py:9`, `accounts/views.py:97,106`) | Unused by frontend |
| `/api/v1/accounts/me/` | Not used | `GET` (`accounts/urls.py:10`, `accounts/views.py:153`) | Unused by frontend |
| `/api/v1/profiles/me/` | Not used | `GET`, `PUT`, `PATCH` (`profiles/urls.py:7`, `profiles/views.py:25,28,31`) | Unused by frontend |
| `/api/v1/profiles/onboard/` | Not used | `PUT`, `PATCH` (`profiles/urls.py:8`, `profiles/views.py:53,56`) | Unused by frontend |
| `/api/v1/tests/questions/` | Not used | `GET` (`test_system/urls.py:7`, `test_system/views.py:23`) | Unused by frontend |
| `/api/v1/tests/submit/` | Not used | `POST` (`test_system/urls.py:8`, `test_system/views.py:36`) | Unused by frontend |
| `/api/v1/ai/generate/` | Not used | `POST` (`ai_engine/urls.py:7`, `ai_engine/views.py:38`) | Unused by frontend |
| `/api/v1/ai/tasks/{task_id}/` | Not used | `GET` (`ai_engine/urls.py:8`, `ai_engine/views.py:117`) | Unused by frontend |
| `/api/v1/roadmaps/me/` | Not used | `GET` (`roadmaps/urls.py:7`, `roadmaps/views.py:25`) | Unused by frontend |
| `/api/v1/roadmaps/tasks/{pk}/` | Not used | `PATCH` (`roadmaps/urls.py:8`, `roadmaps/views.py:56`) | Unused by frontend |
| `/api/v1/progress/my-stats/` | Not used | `GET` (`progress/urls.py:7`, `progress/views.py:27`) | Unused by frontend |
| `/api/v1/progress/leaderboard/` | Not used | `GET` (`progress/urls.py:8`, `progress/views.py:63`) | Unused by frontend |
| `/api/v1/recommendations/my/` | Not used | `GET` (`recommendations/urls.py:8`, `recommendations/views.py:29`) | Unused by frontend |

---

## Data Contract Differences

- Onboarding request
  - Backend expects (`profiles/serializers.py:56`):
    - `direction: string`
    - `english_level: string (choice)`
    - `current_goal: string`
  - Frontend onboarding state (`front/src/app/components/Onboarding.tsx:35-43`) currently stores:
    - `name`, `university`, `major`, `year`, `skills`, `interests`, `careerGoal`
  - Differences:
    - Missing direct fields for backend (`direction`, `english_level`, `current_goal`).
    - Extra fields not in backend onboarding serializer.

- Test submission request
  - Backend expects (`test_system/serializers.py:48-57`):
    - `answers: [{ question_id: number, choice_id: number }]`
  - Frontend
    - No implemented API call yet.
  - Difference:
    - Request DTO and submit flow are absent in frontend.

- Roadmap task update request
  - Backend expects (`roadmaps/serializers.py:40-42`):
    - `PATCH /tasks/{pk}/` with `{ is_completed: boolean }`
  - Frontend roadmap task model (`front/src/app/components/Roadmap.tsx:5-12`):
    - `id: string`, `progress`, `deadline`, `resources`
  - Differences:
    - ID type mismatch risk (`string` vs `int` path param).
    - UI fields do not map to backend update payload.

- Recommendations response
  - Backend returns (`recommendations/serializers.py:29-33`):
    - `{ count, results: [{ direction, min_english_level, max_english_level, title, description, url, resource_type, priority }] }`
  - Frontend resource card model (`front/src/app/components/Resources.tsx:5-15`):
    - expects `thumbnail`, `rating`, `duration`, `bookmarked`, `difficulty`, `category`
  - Differences:
    - Response shape mismatch; frontend expects fields backend does not provide.

- Progress/dashboard response
  - Backend `my-stats` returns (`progress/views.py:46-53`, `progress/serializers.py:20-42`):
    - `progress`, `roadmap_completion_percentage`, `completed_tasks_count`, `total_tasks_count`
  - Frontend dashboard/analytics (`front/src/app/components/Dashboard.tsx`, `front/src/app/components/Analytics.tsx`):
    - static arrays and computed mock values.
  - Difference:
    - No contract consumption; UI numbers can drift from backend truth.

---

## Auth Flow Analysis

- Backend auth model
  - JWT is global default auth (`main/settings.py:173-175`).
  - Token type is Bearer (`main/settings.py:220`).
  - Public endpoints: register/login/verify-email (`accounts/views.py:32,59,88`).
  - Protected endpoints: profile/test/roadmap/progress/recommendations/ai (multiple `IsAuthenticated`).

- Frontend auth model
  - No login/register API integration in `front/src`.
  - No token persistence and no auth header attachment logic.
  - No protected-route guard based on backend auth state.

- Key mismatch
  - Backend assumes authenticated JWT-bearing client; frontend currently acts as standalone demo UI.

- Required alignment steps
  - Add auth service for register/login.
  - Store `access` token securely (at minimum memory/session strategy, with refresh handling plan).
  - Inject `Authorization: Bearer <token>` into all protected calls.
  - On app bootstrap, validate auth state with `/api/v1/accounts/me/`.

---

## Recommendations

- Implement a typed API layer in frontend
  - Create a single API client module (base URL, headers, token injection, status handling).
  - Add DTO mappers to convert frontend camelCase to backend snake_case.

- Integrate core journey in order
  - 1) Auth (`register/login/me`)
  - 2) Onboarding (`profiles/onboard`)
  - 3) AI generation (`ai/generate` + `ai/tasks/{task_id}` polling)
  - 4) Roadmap read/update (`roadmaps/me`, `roadmaps/tasks/{pk}`)
  - 5) Progress and recommendations

- Standardize error handling
  - Handle 400/401/403/404/502/503 explicitly with user-visible states.
  - Introduce reusable API error normalization for `detail` and field-level errors.

- Align data contracts before coding UI wiring
  - Confirm whether backend should support extra onboarding/profile fields (`university`, `major`, etc.).
  - If yes, extend backend models/serializers; if no, remove those fields from submit payloads.

- Add frontend async state discipline
  - For each API screen: loading, success, empty, and error states.
  - Use request cancellation and stale data control (SWR/React Query) for read endpoints.

