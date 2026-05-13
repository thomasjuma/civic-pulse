# Frontend Agent Guide

## Project overview
- This frontend is a Next.js app for Civic Pulse.
- It displays generated civic article summaries, article detail pages, and a subscription modal for email and WhatsApp updates.
- Main UI code lives in `app/`; reusable client components live in `components/`; API helpers live in `lib/`; shared types live in `types/`.
- The app reads backend data from `NEXT_PUBLIC_API_BASE_URL`, defaulting to `http://localhost:8000`.

## Build and test commands
- Install dependencies from `frontend/`: `npm install`
- Run the dev server: `npm run dev`
- Build production assets: `npm run build`
- Run linting when available: `npm run lint`
- Use Node LTS or newer; `package.json` requires Node `>=20`.

## Code style guidelines
- Use TypeScript for new or changed code.
- Prefer server components for data-loading pages and client components only for browser state or interactions.
- Use Tailwind CSS utilities for component styling; keep `app/globals.css` limited to Tailwind imports and small global base rules.
- Use `lucide-react` icons for interface actions and status indicators.
- Keep UI dense, clear, and civic-service focused; avoid marketing-style hero pages or decorative-only effects.

## Testing instructions
- There is no frontend test runner configured yet; do not invent one without asking.
- For UI behavior changes, run `npm run build` at minimum.
- If adding tests later, prefer Vitest for unit tests and keep tests close to the changed components or helpers.
- Mock backend calls from `lib/api.ts`; do not rely on a live backend for deterministic tests.
- Watch for Next.js generated `next-env.d.ts` changes after builds and avoid committing unrelated generated churn.

## Security considerations
- Never commit `.env.local` or any real API URL containing secrets.
- Only expose public configuration through `NEXT_PUBLIC_*` variables.
- Treat article text, summaries, and image URLs from the backend as untrusted display data.
- Do not collect subscription details outside the existing backend subscriber API flow.
- Keep WhatsApp consent language visible before sending subscriber data to the backend.
