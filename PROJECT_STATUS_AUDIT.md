# 📊 Backend Project Status Audit

## 1. Общий процент готовности (Overall Completion)

**Оценка готовности backend-ядра: 72%**

Оценка рассчитана по фактически реализованной цепочке: **Auth -> Onboarding -> AI queue -> Roadmap persistence -> Task completion -> Dashboard -> Celery jobs**.

- Сильная база уже есть: кастомный `User`, JWT, email verification, API onboarding, тестовая система, AI-сервис, roadmap-слой, gamification и периодические задачи Celery.
- Критичный разрыв пока в сквозной интеграции: в проекте одновременно живут `profiles.Profile` и `test_system.StudentProfile`, а AI-сервис опирается только на `StudentProfile`.
- Очевидный технический долг подтвержден тестами: прогон `python manage.py test accounts profiles test_system ai_engine roadmaps progress` дал **11 падений из 45** (интеграционные и контрактные несоответствия).
- Celery-контур реализован, но бизнес-устойчивость частично зависит от cache/result backend и отсутствует доменная история статусов генерации roadmap.

## 2. Анализ по каждому App (Модулю)

### App: `accounts`

- **Статус:** Готово
- **Реализованный функционал:** email-only `User`, регистрация, логин с JWT, email verification (`uid` + token), endpoint `me`, отправка verification email, автосоздание профиля через сигнал (`accounts/apps.py`).
- **Чего не хватает:** recovery-флоу (reset/change password), явной интеграции с `StudentProfile` как единым onboarding-source, небольшой cleanup в admin/search по полям `username` (учитывая кастомный user без `username`).

### App: `profiles`

- **Статус:** Требует внимания
- **Реализованный функционал:** `Profile`, API `profiles/me` + `profiles/onboard`, сигнал автосоздания профиля (`profiles/signals.py`).
- **Чего не хватает:** прямой связи с AI pipeline; завершение onboarding в `profiles` не приводит к запуску AI; модель дублирует смысл `StudentProfile`, что создает неоднозначный source of truth.

### App: `test_system`

- **Статус:** В процессе
- **Реализованный функционал:** доменная onboarding-модель `StudentProfile` + справочники (`Category`, `Direction`, `Goal`), permission `IsOnboarded`, API категорий/направлений/целей, submit onboarding с попыткой queue Celery, тестовые вопросы и submit attempt с транзакцией.
- **Чего не хватает:** единая стыковка с `profiles` (сейчас permission смотрит только `student_profile.is_onboarding_completed`); OpenAPI-контракт не покрывает onboarding endpoints (`categories/`, `directions/`, `goals/`, `onboarding/submit/`); нет логики обновления `skill_level` по результату теста.

### App: `ai_engine`

- **Статус:** В процессе
- **Реализованный функционал:** LLM provider abstraction, `GeminiProvider` с обработкой connection/timeout/invalid JSON, валидация JSON-схемы, Celery task `generate_roadmap_task`, API запуска и polling task-status с ownership check через cache.
- **Чего не хватает:** устойчивой доменной истории выполнения задач (queued/started/success/failed в БД), fallback при истечении owner-cache (сейчас возможен 404 даже для валидного `task_id`), и главное - согласованного входного профиля (ожидается `StudentProfile`, а часть флоу ведется через `Profile`).

### App: `roadmaps`

- **Статус:** Требует внимания
- **Реализованный функционал:** модели `Roadmap`/`Phase`/`Task`, сервис `RoadmapBuilderService` (нормализация и bulk insert), API активной roadmap, history и task update, автоматическое завершение фазы/roadmap при полном completion.
- **Чего не хватает:** корректный rollback статусов при `is_completed=True -> False` (сейчас нет пересчета `Phase.is_completed` и `Roadmap.is_completed/is_active` в обратную сторону), оптимизация detail-пути (`progress_percentage` вызывает дополнительные `COUNT`), унификация тестовых ожиданий и текстовых fallback-сообщений.

### App: `progress`

- **Статус:** В процессе
- **Реализованный функционал:** `UserProgress`, `StudyTimeLog`, начисление очков/стрика через signal + `GamificationService`, dashboard, leaderboard, Celery-задача мотивационных email.
- **Чего не хватает:** симметричная бизнес-логика при undo completion (баллы не откатываются и это может быть допустимо/недопустимо в зависимости от продуктовой политики), расширенная аналитика временных рядов, явная продуктовая спецификация на recalculation policy.

## 3. Критический анализ Data Flow (Где может порваться цепь?)

### 3.1 Связь onboarding -> Celery trigger AI

- Ветка `test_system.SubmitOnboardingView` действительно триггерит `generate_roadmap_task.delay(...)` после сохранения `StudentProfile`.
- Ветка `profiles.OnboardingView` **не** триггерит Celery и обновляет только `profiles.Profile.is_onboarded`.
- `RoadmapGeneratorService.build_prompt()` берет данные из `StudentProfile` + `TestAttempt`, поэтому пользователь, завершивший onboarding только через `profiles`, получит `400` при AI generate.
- Это подтверждается и тестовым поведением: в `ai_engine/tests.py` несколько сценариев падают с `400` вместо ожидаемых `200/202/502` из-за отсутствия `StudentProfile` контекста.

### 3.2 Обновление статусов при `Task` -> completed

- Переход `False -> True` обработан хорошо: `Task.mark_as_done()` обновляет `completed_at`, закрывает `Phase`, затем закрывает/деактивирует `Roadmap` при полном завершении.
- Переход `True -> False` реализован частично в `TaskUpdateView`: снимается только `Task.is_completed` и `completed_at`.
- Риск: после undo задача может стать незавершенной, но `Phase.is_completed=True` и/или `Roadmap.is_completed=True`, `is_active=False` останутся в старом состоянии.

### 3.3 Корректность запросов прогресса для Dashboard (N+1/FK)

- Критичных N+1 в `progress` API не видно: `MyDashboardStatsView` использует агрегаты, `LeaderboardView` использует `select_related("user")` и лимит.
- FK-проверка принадлежности task в `StudyTimeLogSerializer.validate_task_id()` корректна (`phase__roadmap__user=request.user`).
- Но в `roadmaps` detail есть лишние запросы: `Roadmap.progress_percentage` без annotate делает 2 дополнительных `COUNT`.
- Это подтверждается тестом `roadmaps.tests.RoadmapViewsTests.test_my_roadmap_fetch_is_prefetch_optimized`: фактически 5 запросов против ожидаемых 3.

### 3.4 Обработка ошибок при невалидном JSON от Gemini

- Защита реализована качественно: `GeminiProvider` ловит пустой ответ/JSON decode/type mismatch; `RoadmapGeneratorService` проводит schema-validation через DRF serializer.
- API слой (`GenerateRoadmapAPIView`) корректно маппит ошибки в `400/502/503`.
- Слабое место не в валидации JSON, а в наблюдаемости async-контура: нет persistent job model, поэтому troubleshooting завязан на Celery backend + cache ownership TTL.

### 3.5 Дополнительные точки отказа (подтверждено тестами)

- `test_system.tests.TestSystemAPITests.test_onboarded_user_can_fetch_questions...` падает с `403`: тест помечает onboarding в `Profile`, а permission проверяет `StudentProfile`.
- `ai_engine.tests.RoadmapTaskStatusAPITests.test_status_backend_unavailable...` получает `404` (owner-cache miss) вместо ожидаемого backend error, что показывает чувствительность статуса к cache mapping.
- `roadmaps` тесты указывают на контракты, ушедшие от старых ожиданий (архивация вместо удаления roadmap, локализованные fallback-строки, другое сообщение исключений).

## 4. Задачи на следующий спринт (Action Plan)

### Critical

1. **Унифицировать onboarding source of truth**: выбрать один доменный профиль (`Profile` или `StudentProfile`) и убрать дублирование флагов `is_onboarded` / `is_onboarding_completed`.
2. **Собрать единый orchestration flow**: после успешного onboarding + test submit гарантированно запускать AI generation (event/service orchestration), а не оставлять ручной запуск как единственный путь.
3. **Синхронизировать AI prerequisites с выбранной моделью onboarding**: `RoadmapGeneratorService` должен читать ту же сущность, которую реально заполняет фронт.
4. **Исправить rollback статусов roadmap lifecycle** при undo task completion: пересчет `Phase` и `Roadmap` в обе стороны в транзакции.
5. **Ввести persistent таблицу статусов AI задач** (task id, user, state, error, timestamps) для надежного polling и диагностики вне зависимости от cache TTL.

### High

1. **Обновить и зафиксировать API-контракт OpenAPI**: добавить missing endpoints из `test_system`, выровнять ответы/коды/схемы с фактическими view.
2. **Оптимизировать roadmap detail performance**: annotate counters до сериализации или кешировать прогресс, чтобы убрать лишние `COUNT`.
3. **Привести тестовый набор к актуальной бизнес-политике**: отдельно зафиксировать, что считается правильным (архивация vs удаление, язык сообщений, поведение при cache miss).
4. **Определить политику gamification при undo**: оставить неоткатываемые баллы (анти-абьюз) или реализовать корректный debit.

### Medium

1. **Добавить account recovery API** (`forgot/reset/change password`) для production readiness auth-контура.
2. **Расширить progress analytics** (неделя/месяц, тренд активности, completion velocity).
3. **Очистить admin-часть от ссылок на `username`** в местах, где используется кастомный `User` без `username`.
4. **Усилить observability**: структурные логи по ключевым этапам flow (onboarding complete, AI queued, roadmap persisted, task completion recalculated).


