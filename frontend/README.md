# Cadence frontend

Vue 3 + TypeScript + Vite, with Pinia, Vue Router, an axios service layer,
and a shared component set. See the root `README.md` for what the app as
a whole does; this one is the frontend's own setup and layout.

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
npm run test:e2e             # playwright test - see e2e/ below
```

## End-to-end tests

`e2e/` holds Playwright specs that drive the real app in a real browser
against a real backend - unlike `tests/unit`, nothing here is mocked.
`playwright.config.ts` starts both servers itself: the frontend (`npm run
dev`) and the API, via `../backend/scripts/run_e2e_server.sh`, which
migrates and seeds its own `cadence_e2e` database from scratch on every
run so a run here never depends on (or pollutes) local dev data or
`pytest`'s own database. First run only: `npx playwright install
chromium`.

## Layout

```
src/
├─ app/                  # shell: main.ts, App.vue, router, DashboardView
├─ features/
│  ├─ auth/               # types, api client, Pinia store, login/register views
│  ├─ learning/             # curriculum player, roadmap, skill map
│  ├─ exams/                 # exam overview, attempt runner, result, history
│  ├─ notation/                # the staff editor (VexFlow) and its ~20 components/composables
│  ├─ projects/                  # standalone composition workspace, score viewer
│  ├─ feedback/                    # AI feedback display components
│  └─ billing/                      # pricing view
├─ shared/
│  ├─ components/base/     # BaseButton, BaseInput, BaseCard
│  └─ utils/                # toApiProblem (axios error -> Problem Details), markdown, download
├─ services/
│  ├─ http.ts                # axios instance: auth header + 401 refresh-and-retry
│  └─ token-storage.ts        # in-memory access token, persisted refresh token
├─ types/                      # cross-feature API types
└─ styles/                      # Tailwind entry
tests/unit/                      # Vitest + @vue/test-utils (component-level, APIs mocked)
e2e/                               # Playwright (real browser, real backend)
```

Same layering convention as the backend: a feature owns its `api/` (DTOs +
mapping to domain types) and `stores/`; `shared/` and `services/` never
import from a feature.

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
