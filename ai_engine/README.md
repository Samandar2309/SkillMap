# AI Engine

Service-layer app that generates a validated roadmap JSON using Gemini.

## Endpoint

- `POST /api/v1/ai/generate/`

## Environment Variables

- `GEMINI_API_KEY` (required)
- `GEMINI_MODEL` (optional, default: `gemini-1.5-flash`)

## Notes

- This app has no models and stores no roadmap data.
- It validates LLM output using DRF serializers before returning JSON.

