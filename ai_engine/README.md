# AI Engine

Service-layer app that generates a validated roadmap JSON using Groq.

## Endpoint

- `POST /api/v1/ai/generate/`

## Environment Variables

- `GROQ_API_KEY` (required)
- `GROQ_MODEL` (optional, default: `llama-3.1-70b-versatile`)

## Notes

- This app has no models and stores no roadmap data.
- It validates LLM output using DRF serializers before returning JSON.

