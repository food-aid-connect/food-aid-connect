# frontend

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Recommended Browser Setup

- Chromium-based browsers (Chrome, Edge, Brave, etc.):
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
  - [Turn on Custom Object Formatter in Chrome DevTools](http://bit.ly/object-formatters)
- Firefox:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - [Turn on Custom Object Formatter in Firefox DevTools](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) to make the TypeScript language service aware of `.vue` types.

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

Install Node.js 22.22.2 or later in the 22.x series, 24.15.0 or later in the
24.x series, or 26.0.0 or newer. The locked `npm-run-all2` dependency, which
runs the frontend build, requires this range.

```sh
npm install
```

### Generate the Flask API client

Install the backend dependencies from `backend/requirements.txt` in a Python
virtual environment and activate it. From the repository root, start Flask:

```sh
python -m flask --app backend/app.py run --host 127.0.0.1 --port 5000
```

Flask defaults to local SQLite when `DATABASE_URL` is unset. Run the server from
the backend revision whose API you want to generate. In another terminal, from
`frontend/`, install the locked packages with `npm ci` and run:

```sh
npm run generate:api
npm run build
```

Generation reads `http://127.0.0.1:5000/openapi.json` and writes the SDK and
types for `/api/` routes to `src/api/generated/`. Commit the regenerated files
after reviewing the diff. The Fetch client uses relative paths such as
`/api/batches` and sends Flask session cookies with `credentials: 'include'`.
Vite proxies those paths to Flask during development. In production, serve the
frontend and API on the same origin or route `/api/` through a reverse proxy.

With a clean Git checkout and Flask running, `npm run check:api` regenerates the
client, type-checks its TypeScript consumers, and fails if generated files differ
from the checked-in version. Review those differences for breaking changes.
This detects generated contract drift and incompatible typed usage. A normal
`npm run build` type-checks the checked-in client and can run offline.

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Type-Check, Compile and Minify for Production

```sh
npm run build
```
