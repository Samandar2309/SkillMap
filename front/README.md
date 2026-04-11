# SkillMap Frontend

Production-oriented React + Vite frontend integrated with Django backend API (`/api/v1`).

## Integrated Features

- JWT auth: register, login, verify email, current user
- Onboarding + AI roadmap generation with polling
- Roadmap fetch and task completion updates
- Dashboard stats + leaderboard
- Recommendations list
- Test questions + test submit

## Environment

Create `front/.env` (optional):

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

If omitted, frontend uses default `http://localhost:8000/api/v1`.

## Run

```powershell
Set-Location "d:\SkillMap\front"
npm install
npm run dev
```

## Build

```powershell
Set-Location "d:\SkillMap\front"
npm run build
```
