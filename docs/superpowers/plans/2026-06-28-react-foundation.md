# React Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing React/Vite application the reproducible, tested production frontend.

**Architecture:** Keep the React UI, IndexedDB schema, and Worker API contract intact. Repair the engineering foundation around them, isolate camera resource handling behind testable helpers, and align CI and documentation with the deployed architecture.

**Tech Stack:** React 18, TypeScript, Vite 8, Vitest 4, ESLint 8, Cloudflare Workers

---

### Task 1: Frontend quality baseline

**Files:**
- Modify: `flet_app/package.json`
- Create: `flet_app/.eslintrc.cjs`
- Create: `flet_app/src/test/setup.ts`

- [ ] Add Vitest and jsdom using the existing TypeScript toolchain.
- [ ] Add an ESLint configuration for TypeScript and React hooks.
- [ ] Verify `npm run lint` and an empty Vitest run execute deterministically.

### Task 2: Camera lifecycle regression coverage

**Files:**
- Create: `flet_app/src/components/cameraLifecycle.ts`
- Create: `flet_app/src/components/cameraLifecycle.test.ts`
- Modify: `flet_app/src/components/CameraView.tsx`

- [ ] Write failing tests proving every stream track is stopped and missing canvas context resets processing.
- [ ] Implement the minimal lifecycle helpers and integrate them into `CameraView`.
- [ ] Run focused tests, then all frontend tests.

### Task 3: Reproducible build and deploy

**Files:**
- Modify: `flet_app/vite.config.ts`
- Modify: `build.sh`

- [ ] Reproduce the production build failure.
- [ ] Make Vite input/output paths deterministic across Windows and Linux.
- [ ] Replace lockfile deletion and `npm install` with `npm ci`.
- [ ] Verify a clean production build.

### Task 4: CI and repository hygiene

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `.gitignore`

- [ ] Add React install, lint, test, and build jobs to CI.
- [ ] Preserve Worker syntax/security verification.
- [ ] Ignore dependency, build, browser profile, cache, TypeScript metadata, archive, and Windows metadata files.
- [ ] Report already tracked generated files without deleting user files in this task.

### Task 5: Documentation alignment

**Files:**
- Modify: `README.md`
- Modify: `docs/technical-stack.md`

- [ ] Document React/Vite as the production frontend and Flet as legacy.
- [ ] Document `VITE_API_URL`, local development, verification, and Pages deployment.
- [ ] Cross-check every documented command against the final verification run.

### Task 6: Completion audit

- [ ] Run `npm run lint`.
- [ ] Run `npm test -- --run`.
- [ ] Run `npm run build`.
- [ ] Run `node --check worker/index.js`.
- [ ] Run the Worker security test where Python dependencies permit.
- [ ] Inspect the final diff and confirm every success criterion in `docs/spec-react-foundation.md`.
