# Backend Functionality Report

---

## 🧠 System Overview

- Тип системы: **EdTech + AI-assisted learning platform** на Django REST Framework.
- Основная цель: провести пользователя от регистрации и онбординга до aptitude-теста, генерации персонального roadmap через LLM (Gemini), отслеживания прогресса и выдачи рекомендаций.
- Архитектура: модульный монолит с приложениями `accounts`, `profiles`, `test_system`, `ai_engine`, `roadmaps`, `progress`, `recommendations`.
- Аутентификация: глобально настроен JWT (`rest_framework_simplejwt.authentication.JWTAuthentication`), публичные исключения задаются в конкретных view.
- Асинхронность: Celery (`main/celery.py`) + polling endpoint для статуса задачи генерации roadmap.

Ключевые модули:
- `accounts`: регистрация, вход, верификация email, текущий пользователь.
- `profiles`: профиль и онбординг (направление, уровень английского, цель).
- `test_system`: вопросы/ответы aptitude-теста, расчет score.
- `ai_engine`: запуск и мониторинг фоновой генерации roadmap через LLM.
- `roadmaps`: хранение roadmap (roadmap/phases/tasks), чтение и отметка выполнения задач.
- `progress`: очки/стрики/дашборд/лидерборд, автоначисление за выполнение задач.
- `recommendations`: персональные подборки ресурсов по направлению и уровню английского.

---

## 🚀 Features

### Feature: Authentication & Account Management

- Description:
  - Регистрация по email+password (без username).
  - Верификация email через токенизированную ссылку (`uid` + `token`).
  - Логин только для `is_verified=True`.
  - Получение данных текущего пользователя.
- Endpoints:
  - `POST /api/v1/accounts/register/`
  - `POST /api/v1/accounts/login/`
  - `GET /api/v1/accounts/verify-email/`
  - `POST /api/v1/accounts/verify-email/`
  - `GET /api/v1/accounts/me/`
- Logic:
  - `RegisterSerializer` валидирует уникальность email и совпадение паролей.
  - После регистрации отправляется verification email (`accounts/utils.py`).
  - `LoginSerializer` отклоняет неактивных и неверифицированных пользователей.
  - Выдача JWT (access/refresh) через `RefreshToken.for_user`.

### Feature: Profile & Onboarding

- Description:
  - Автосоздание пустого профиля при создании пользователя (через signals).
  - Просмотр/редактирование профиля.
  - Завершение онбординга с обязательными полями.
- Endpoints:
  - `GET /api/v1/profiles/me/`
  - `PUT /api/v1/profiles/me/`
  - `PATCH /api/v1/profiles/me/`
  - `PUT /api/v1/profiles/onboard/`
  - `PATCH /api/v1/profiles/onboard/`
- Logic:
  - `OnboardingSerializer` требует `direction`, `english_level`, `current_goal`.
  - Onboarding выставляет `is_onboarded=True`.

### Feature: Aptitude Test System

- Description:
  - Получение активных вопросов с вариантами ответов.
  - Отправка ответов и транзакционное сохранение попытки.
- Endpoints:
  - `GET /api/v1/tests/questions/`
  - `POST /api/v1/tests/submit/`
- Logic:
  - Доступ только для onboarded пользователей (`IsOnboarded`).
  - Валидация: вопрос не дублируется, choice принадлежит question, все question/choice валидны.
  - Создается `TestAttempt`, затем bulk insert в `UserResponse`, суммируются points.

### Feature: AI Roadmap Generation (Async)

- Description:
  - Запуск фоновой генерации roadmap через Gemini.
  - Отдельный endpoint для polling статуса Celery-задачи.
- Endpoints:
  - `POST /api/v1/ai/generate/`
  - `GET /api/v1/ai/tasks/{task_id}/`
- Logic:
  - Перед постановкой в очередь проверяются prerequisites: есть профиль и хотя бы одна `TestAttempt`.
  - Генератор формирует prompt с goal/english_level/score.
  - Gemini должен вернуть JSON определенной структуры.
  - Результат провалидации передается в `RoadmapBuilderService` для записи roadmap.
  - В `generate` обрабатываются: брокер недоступен, timeout, provider connection, invalid JSON schema.

### Feature: Roadmap Management

- Description:
  - Получение текущего roadmap пользователя (вложенные phases/tasks).
  - Обновление состояния выполнения task (`is_completed`).
- Endpoints:
  - `GET /api/v1/roadmaps/me/`
  - `PATCH /api/v1/roadmaps/tasks/{pk}/`
- Logic:
  - Пользователь видит только свой roadmap.
  - Патчить можно только свои задачи (`filter(phase__roadmap__user=request.user)`).
  - Обновление задачи идет под транзакцией и `select_for_update`.

### Feature: Progress & Gamification

- Description:
  - Трекинг очков, текущей/лучшей серии активности.
  - Дашборд прогресса и лидерборд.
- Endpoints:
  - `GET /api/v1/progress/my-stats/`
  - `GET /api/v1/progress/leaderboard/`
- Logic:
  - При выполнении task (False -> True) сигнал начисляет +10 points.
  - Streak-логика:
    - тот же день: только очки;
    - следующий день: инкремент серии;
    - пропуск: сброс current_streak в 1.
  - `my-stats` считает % завершения roadmap по задачам.

### Feature: Personalized Recommendations

- Description:
  - Персональные рекомендации ресурсов по профилю пользователя.
- Endpoints:
  - `GET /api/v1/recommendations/my/`
- Logic:
  - Фильтрация по `direction` и диапазону `english_level`.
  - Если нет материалов по направлению - fallback на `general`.
  - Если БД пуста - используется встроенный `DEFAULT_CATALOG`.
  - Сортировка по `priority` (меньше = выше приоритет).

---

## 🔗 API Endpoints

### Platform/Infra Endpoints

| URL | Method | Request Body | Response | Auth |
|---|---|---|---|---|
| `/admin/` | GET | - | Django admin UI | Session/admin auth |
| `/api/schema/` | GET | - | OpenAPI schema | No |
| `/swagger/` | GET | - | Swagger UI | No |
| `/redoc/` | GET | - | ReDoc UI | No |

### Accounts

| URL | Method | Request Body | Response Format | Authentication Required |
|---|---|---|---|---|
| `/api/v1/accounts/register/` | POST | `{ email, password, password_confirm }` | `201 { message, user: { id, email, is_verified, created_at } }` | No |
| `/api/v1/accounts/login/` | POST | `{ email, password }` | `200 { refresh, access, user }` | No |
| `/api/v1/accounts/verify-email/` | GET | Query params: `uid`, `token` | `200/400 { detail }` | No |
| `/api/v1/accounts/verify-email/` | POST | `{ uid, token }` | `200/400 { detail }` | No |
| `/api/v1/accounts/me/` | GET | - | `200 { id, email, is_verified, created_at }` | Yes |

### Profiles

| URL | Method | Request Body | Response Format | Authentication Required |
|---|---|---|---|---|
| `/api/v1/profiles/me/` | GET | - | `200 Profile` | Yes |
| `/api/v1/profiles/me/` | PUT | `Profile` (editable fields: `direction`, `english_level`, `current_goal`) | `200 Profile` | Yes |
| `/api/v1/profiles/me/` | PATCH | Partial profile fields | `200 Profile` | Yes |
| `/api/v1/profiles/onboard/` | PUT | `{ direction, english_level, current_goal }` | `200 Profile` | Yes |
| `/api/v1/profiles/onboard/` | PATCH | Partial onboarding data (serializer enforces required non-empty values in validation) | `200 Profile` | Yes |

`Profile` response fields: `{ id, user, direction, english_level, current_goal, is_onboarded, created_at, updated_at }`.

### Test System

| URL | Method | Request Body | Response Format | Authentication Required |
|---|---|---|---|---|
| `/api/v1/tests/questions/` | GET | - | `200 [{ id, text, skill_category, choices: [{ id, text }] }]` | Yes (`IsAuthenticated` + `IsOnboarded`) |
| `/api/v1/tests/submit/` | POST | `{ answers: [{ question_id, choice_id }] }` | `201 { attempt_id, total_score }` | Yes (`IsAuthenticated` + `IsOnboarded`) |

### AI Engine

| URL | Method | Request Body | Response Format | Authentication Required |
|---|---|---|---|---|
| `/api/v1/ai/generate/` | POST | - | `202 { task_id, status: "queued" }` or error `{ detail }` | Yes |
| `/api/v1/ai/tasks/{task_id}/` | GET | - | `200 { task_id, state, status, result?, error? }` | Yes |

### Roadmaps

| URL | Method | Request Body | Response Format | Authentication Required |
|---|---|---|---|---|
| `/api/v1/roadmaps/me/` | GET | - | `200 Roadmap` or `404 { detail, code }` | Yes |
| `/api/v1/roadmaps/tasks/{pk}/` | PATCH | `{ is_completed: boolean }` | `200 { id, phase, title, description, resource_link, is_completed }` | Yes |

`Roadmap` response вложенный: `{ id, user, title, estimated_months, is_completed, created_at, phases[] }`, где каждая `phase` содержит `tasks[]`.

### Progress

| URL | Method | Request Body | Response Format | Authentication Required |
|---|---|---|---|---|
| `/api/v1/progress/my-stats/` | GET | - | `200 { progress, roadmap_completion_percentage, completed_tasks_count, total_tasks_count }` | Yes |
| `/api/v1/progress/leaderboard/` | GET | - | `200 [{ email, total_points, current_streak }]` (top 10) | Yes |

### Recommendations

| URL | Method | Request Body | Response Format | Authentication Required |
|---|---|---|---|---|
| `/api/v1/recommendations/my/` | GET | - | `200 { count, results: [resource] }` or `400 { detail }` | Yes |

---

## 🗂 Data Models

### `accounts.User`
- Fields:
  - `email` (unique, login identifier)
  - `is_verified` (email verification state)
  - `created_at`
  - inherited: `password`, `is_active`, `is_staff`, `is_superuser`, etc.
- Relationships:
  - one-to-one with `profiles.Profile` (`user.profile`)
  - one-to-one with `progress.UserProgress` (`user.progress`)
  - one-to-one with `roadmaps.Roadmap` (`user.roadmap`)
  - one-to-many with `test_system.TestAttempt` (`user.test_attempts`)

### `profiles.Profile`
- Fields: `user`, `direction`, `english_level`, `current_goal`, `is_onboarded`, `created_at`, `updated_at`.
- Relationships: `OneToOne(User)`.

### `test_system.Question`
- Fields: `text`, `skill_category`, `is_active`.
- Relationships: one-to-many `choices`.

### `test_system.Choice`
- Fields: `question`, `text`, `points`.
- Relationships: `ForeignKey(Question)`.

### `test_system.TestAttempt`
- Fields: `user`, `total_score`, `created_at`.
- Relationships: `ForeignKey(User)`, one-to-many `responses`.

### `test_system.UserResponse`
- Fields: `attempt`, `question`, `selected_choice`.
- Relationships: `ForeignKey(TestAttempt/Question/Choice)`.
- Constraint: unique (`attempt`, `question`).

### `roadmaps.Roadmap`
- Fields: `user`, `title`, `estimated_months`, `is_completed`, `created_at`.
- Relationships: `OneToOne(User)`, one-to-many `phases`.

### `roadmaps.Phase`
- Fields: `roadmap`, `title`, `order`, `is_completed`.
- Relationships: `ForeignKey(Roadmap)`, one-to-many `tasks`.
- Constraint: unique (`roadmap`, `order`).

### `roadmaps.Task`
- Fields: `phase`, `title`, `description`, `resource_link`, `is_completed`.
- Relationships: `ForeignKey(Phase)`.

### `progress.UserProgress`
- Fields: `user`, `total_points`, `current_streak`, `longest_streak`, `last_activity_date`.
- Relationships: `OneToOne(User)`.

### `recommendations.RecommendationResource`
- Fields: `direction`, `min_english_level`, `max_english_level`, `title`, `description`, `url`, `resource_type`, `priority`, `is_active`, `created_at`, `updated_at`.
- Relationships: standalone catalog entity.
- Indexes: `direction/is_active`, `min_english_level/max_english_level`.

---

## ⚙️ Business Logic

### Onboarding Flow
- Профиль создается автоматически при регистрации через post-save signal.
- Пользователь завершает onboarding через `/profiles/onboard/`.
- После успешного обновления выставляется `is_onboarded=True`.
- До онбординга доступ к test-system закрыт кастомным permission `IsOnboarded`.

### Roadmap Generation
- Endpoint `/ai/generate/` не принимает body, использует контекст текущего пользователя.
- `RoadmapGeneratorService.build_prompt()` берет:
  - `profile.current_goal`
  - `profile.english_level`
  - `latest TestAttempt.total_score`
- Gemini вызывается через `GeminiProvider.generate_json()` и должен вернуть JSON.
- JSON валидируется сериализатором `GeneratedRoadmapSerializer`.
- `RoadmapBuilderService.build_from_json()`:
  - поддерживает mapping разных ключей от разных LLM-схем;
  - нормализует фазы/задачи;
  - вычисляет `estimated_months` (явное значение или через `duration_weeks`);
  - удаляет старый roadmap пользователя и создает новый;
  - пишет phases/tasks через bulk_create.

### AI Usage
- В текущей реализации используется провайдер Gemini (`google.generativeai`).
- В prompt жестко задана структура JSON и ограничения (>=3 phases, >=3 tasks в фазе).
- Ошибки LLM абстрагированы кастомными исключениями:
  - `LLMConnectionError`
  - `LLMTimeoutError`
  - `InvalidJSONOutputError`

### Progress Calculation
- Dashboard (`/progress/my-stats/`) агрегирует:
  - количество всех задач roadmap,
  - количество завершенных задач,
  - процент завершения (`completed / total * 100`, округление до 2 знаков).
- Начисление очков не в endpoint, а в signals при изменении `Task.is_completed` с `False` на `True`.

### Recommendations Generation
- Источник данных:
  - сначала активные записи `RecommendationResource` из БД,
  - иначе встроенный `DEFAULT_CATALOG`.
- Логика фильтрации:
  1. Нормализация направления и уровня языка.
  2. Фильтр по направлению (или fallback на `general`).
  3. Фильтр по диапазону `min_english_level..max_english_level`.
  4. Сортировка по `priority`.

---

## 🔐 Authentication & Permissions

- JWT:
  - Глобально включен `JWTAuthentication` в `REST_FRAMEWORK`.
  - Логин возвращает `refresh` + `access` токены.
- Публичные endpoints:
  - `/api/v1/accounts/register/`
  - `/api/v1/accounts/login/`
  - `/api/v1/accounts/verify-email/` (GET/POST)
  - `/api/schema/`, `/swagger/`, `/redoc/`
- Защищенные endpoints:
  - все `/api/v1/*` кроме публичных account endpoints выше.
- Доп. permission:
  - `IsOnboarded` для test-system endpoints.
- Ролевой модели (RBAC) в коде нет:
  - нет отдельных ролей типа mentor/admin/student на уровне API-permission (кроме Django admin).
- Throttling:
  - глобально `AnonRateThrottle`, `UserRateThrottle`, `ScopedRateThrottle`;
  - `throttle_scope="auth"` на register/login/verify-email и AI endpoints.

---

## 🔄 Async Processes

- Фоновая задача:
  - `ai_engine.tasks.generate_roadmap_task(user_id)`.
- Lifecycle (через Celery `AsyncResult`):
  - `PENDING` -> `STARTED`/`RETRY` -> `SUCCESS` или `FAILURE`.
- Поллинг статуса:
  - `GET /api/v1/ai/tasks/{task_id}/` возвращает `{task_id, state, status, result?, error?}`.
- Поведение в dev/prod:
  - `DEBUG=True`: broker/result backend memory.
  - иначе ожидается Redis (по env).
  - `CELERY_TASK_ALWAYS_EAGER` может переводить выполнение в eager-режим.

---

## 🔁 System Flow

1. Пользователь регистрируется через `/api/v1/accounts/register/`.
2. Система отправляет email с verification link (`uid` + `token`).
3. Пользователь подтверждает email через `/api/v1/accounts/verify-email/`.
4. Пользователь логинится (`/api/v1/accounts/login/`) и получает JWT.
5. Пользователь заполняет onboarding (`/api/v1/profiles/onboard/`).
6. Пользователь проходит aptitude test:
   - получает вопросы (`/api/v1/tests/questions/`),
   - отправляет ответы (`/api/v1/tests/submit/`),
   - формируется `TestAttempt.total_score`.
7. Пользователь запускает AI-генерацию roadmap (`/api/v1/ai/generate/`).
8. Frontend делает polling статуса (`/api/v1/ai/tasks/{task_id}/`) до `SUCCESS`.
9. После генерации пользователь получает roadmap (`/api/v1/roadmaps/me/`).
10. Пользователь отмечает выполнение задач (`/api/v1/roadmaps/tasks/{pk}/`).
11. Сигналы начисляют points/streak, дашборд обновляется (`/api/v1/progress/my-stats/`), лидерборд показывает топ (`/api/v1/progress/leaderboard/`).
12. Пользователь получает персональные рекомендации (`/api/v1/recommendations/my/`).

---

## 📊 Strengths

- Четкая декомпозиция по доменным приложениям.
- Сквозной путь пользователя реализован от регистрации до рекомендаций.
- Защита доступа корректно разделена (public/private + `IsOnboarded`).
- Транзакции и `select_for_update` используются в критичных местах (submit test, task update, roadmap build, progress update).
- Асинхронная генерация roadmap с polling снижает блокировку API при долгих LLM-вызовах.
- `RoadmapBuilderService` устойчив к вариативности LLM-схем (mapping ключей и fallback значения).

---

## ⚠️ Weaknesses

- OpenAPI-спека (`openapi.yaml`) неполностью синхронизирована с реальным кодом:
  - отсутствует `/api/v1/ai/tasks/{task_id}/`,
  - часть response/request схем отмечена как `No response body`, хотя в коде есть структурированные payload.
- Дублирующиеся сигналы создания профиля: `accounts/signals.py` и `profiles/signals.py` делают похожую работу (риск избыточности/поддержки).
- Модель `Roadmap` допускает только один roadmap на пользователя (`OneToOne`): нет истории поколений roadmap.
- Нет endpoint для refresh токена/logout в `accounts` (при том что refresh выдается).
- Нет привязки Celery task ownership к пользователю в status endpoint (любой аутентифицированный пользователь с валидным `task_id` может запросить статус).
- Часть тестов в `ai_engine/tests.py` отражает старое синхронное поведение (например ожидание `200` с roadmap в `/ai/generate/`), что указывает на рассинхронизацию тестов и текущей реализации async API.
