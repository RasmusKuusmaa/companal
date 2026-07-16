# Cadence frontend foundation

Vue 3 + TypeScript + Vite, with Pinia, Vue Router, an axios service layer,
and a small reusable component set. No feature pages yet — see `src/app/views`
and `src/features/auth/views` for the placeholder routes that prove the
wiring works.

## Setup

```bash
npm install
cp .env.example .env.local   # defaults are fine for local dev against the backend
npm run dev
```

Expects the FastAPI backend running on `http://localhost:8000` (see
`../backend`); `vite.config.ts` proxies `/api` to it in dev.

## Scripts

```bash
npm run dev          # dev server with HMR
npm run build         # type-check (vue-tsc) + production build
npm run type-check     # vue-tsc only
npm run lint            # eslint --fix
npm run format            # prettier --write
npm run test                # vitest run
```

## Layout

```
src/
├─ app/                  # shell: main.ts, App.vue, router, app-level placeholder views
├─ features/
│  └─ auth/               # types, api client, Pinia store, placeholder login route
├─ shared/
│  ├─ components/base/     # BaseButton, BaseInput, BaseCard
│  └─ utils/                # toApiProblem (axios error -> Problem Details)
├─ services/
│  ├─ http.ts                # axios instance: auth header + 401 refresh-and-retry
│  └─ token-storage.ts        # in-memory access token, persisted refresh token
├─ types/                      # cross-feature API types
└─ styles/                      # Tailwind entry
tests/unit/                      # Vitest + @vue/test-utils
```

Same layering convention as the backend: a feature owns its `api/` (DTOs +
mapping to domain types) and `stores/`; `shared/` and `services/` never
import from a feature. Auth is the only populated feature so far — the next
slice (courses, projects, score-editor, ...) follows this same shape.

### Why the auth store looks the way it does

- **Access token: in-memory only.** Never touches `localStorage`, so it
  can't be read by an XSS payload. It's lost on reload and silently
  re-acquired via `bootstrap()`.
- **Refresh token: persisted in `localStorage`.** Pragmatic default so a
  reload doesn't force a full re-login. The stronger option — an httpOnly
  cookie set by the backend — isn't available yet because the backend's
  `/auth/login` doesn't exist as an endpoint yet, only the JWT
  infrastructure it'll use.
- **`services/http.ts` doesn't import the Pinia store.** It reads/writes
  tokens through `services/token-storage.ts` instead, to avoid a circular
  import (`http.ts -> auth store -> auth api -> http.ts`) and to keep the
  401-refresh-retry logic working even before Pinia is installed.
