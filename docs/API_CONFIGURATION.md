# AI API Configuration

AEGIS X uses an OpenAI-compatible chat completions endpoint.

Preferred: Nebius Token Factory / Nebius AI Cloud with an eligible NVIDIA
open-source model (e.g. a Nemotron model).

## Environment variables
- NEBIUS_API_KEY
- NEBIUS_BASE_URL (default https://api.studio.nebius.ai/v1)
- NEBIUS_MODEL
- (fallback) OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

## Verify integration
1. Set keys in .env
2. Run app, ask a question in Investigation page
3. Confirm ai_status == ok and model name shown
4. Test with wrong key to confirm error handling

## Security
- Never commit .env
- Keys are server-side only