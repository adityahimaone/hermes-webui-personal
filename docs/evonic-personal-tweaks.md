# Evonic Personal Tweaks — Full Inventory

> Snapshot: 2026-08-28 07:15  — VPS `apps/evonic` (evonic.adityahimaone.space:8090)
> Upstream: `anvie/evonic` @ `fc334332` (v1.2.0) — personal tweaks on top.
> Purpose: archive before removing Evonic from VPS. Re-apply needed bits to `hermes-webui-personal` or keep as reference.

## 1. Infra

- **PM2:** `evonic` → `~/apps/evonic/start.sh` → `.venv/bin/python -m cli start --host 0.0.0.0 --port 8090` (fork, pid evonic-8)
- **Nginx:** `evonic.adityahimaone.space` 80→443, proxy `/` → 127.0.0.1:8090, `/ws/` WebSocket upgrade 86400s, cert `/etc/letsencrypt/live/evonic.adityahimaone.space/`
- **Env:** `~/apps/evonic/.env` (SECRET_KEY, ADMIN_PASSWORD_HASH, EVOMEM_KB_ORGANIZER_MIN_INTERVAL_SECONDS, PORT=8090) — keep secret, not committed
- **Git:** remote `origin https://github.com/anvie/evonic.git`, branch `dev` ahead of upstream (local tweaks below)

## 2. Agents (3 active + 2 explorers)

| Agent | Role | SYSTEM.md | KB files | Notes |
|-------|------|-----------|----------|-------|
| **jihyo** | Super Admin Fullstack — all projects (SAAS + Bisadaya + Evonic itself) | 78 lines | 41 files | Fullstack without per-task approval; delegates SAAS→karina KB, Bisadaya→ningning KB |
| **karina** | SAAS Frontend (Gadjian/Hadirr/Baktiku) — `saas/` | 101 lines | 17 files | Frontend lane `view/` + `ruang_eksperimen/{js,scss}` + Gulp Node 14; backend needs approval → Semi Fullstack |
| **ningning** | Bisadaya Frontend (monorepo) | 109 lines | 3 files | `apps/*/src/...` + `packages/ui`, Node 22.18.0 Mac / 22.8.0 Win |
| jihyo_explorer_1/2 | ephemeral explorers | — | — | sessions only |

### Agent SYSTEM.md highlights

- **jihyo:** plan-before-large-task, `git branch --show-current` → confirm → `git pull` → plan → execute; never `rm -rf` without asking; KB index for SAAS (`saas-overview.md`, `styling-and-build-workflow.md`) + Bisadaya (`bisadaya-overview.md`, `feature-workflow-and-design-system.md`); kanban single-task-unless-parallel; Artifacts via `save_artifact`.
- **karina/ningning:** same git workflow + Gulp build after JS/SCSS; read KB before starting; check `packages/ui` / locales / `.agents/` before new code.

### KB inventory

- **jihyo kb (41):** 80-company.md, alterra.md, baktiku.md, bangkit-academy.md, binar-academy.md, bisadaya.md, campus-connect.md, dev-fast-8-com.md, employer.md, evonet.md, evonic-frontend-conventions.md, evonic.md …
  - Full list: 80-company.md, alterra.md, baktiku.md, bangkit-academy.md, binar-academy.md, bisadaya.md, campus-connect.md, dev-fast-8-com.md, employer.md, evonet.md, evonic-frontend-conventions.md, evonic.md, fast-8.md, gadjian.md, hadirr.md, jihyo.md, jobseeker.md, karina.md, local-mac.md, next-portfolio-blog.md, ningning.md, notes.md, nvm.md, packages-ui.md, portal-cs.md, pt-fatiha-sakti.md, reglazed-studio.md, reminder-and-schedule-creation-rules.md, remote-mac-development.md, resume-aditya-himawan-2026.md, rtk.md, saas.md, shadcn-ui.md, storybook.md, tailscale.md, task-completion-conventions.md, tesseract.md, universitas-amikom.md, unzyp.md, user.md, workflow-works.md
- **karina kb (17):** baktiku.md, cs-gadjian.md, gadjian-cs-add-customer-form.md, gadjian-setup.md, gadjian-unique-invoice-page.md, gadjian.md, hadirr.md, local-dev-environment-constraints.md, local-dev-environment-quirks.md, perusahaan-tagihan-js.md, perusahaan-tagihan-new-php.md, portal-gadjian.md, saas-file-index.md, saas-overview.md, styling-and-build-workflow.md, task-4-integrasi-show-data-api-modal-early-renewal-tagihan-c.md, xampp.md
- **ningning kb (3):** _probe-write-test.md, bisadaya-overview.md, feature-workflow-and-design-system.md

> Each KB is markdown with project conventions — preserve if migrating. `obsidian-notes` is a symlink/dir to Obsidian vault.

## 3. Plugins (13)

- `agentapi`
- `auto_improver`
- `data`
- `github_webhook`
- `kanban`
- `mcp_client`
- `model-router`
- `panel`
- `plugin_creator`
- `saas_dev_tools`
- `session-recap`
- `token_monitor`
- `workflow_guard`

- **saas_dev_tools** (personal, untracked): Yii2/PHP helpers — `php_lint`, `composer_check`, `yii_migrate_check`, `gulp_build` — thin bash wrappers, `tools.json` + `backend/tools/*.py`, var `SAAS_WORKSPACE=/Users/adityahimawan/Development/saas`
- Others: `agentapi`, `auto_improver`, `data`, `github_webhook`, `kanban`, `mcp_client`, `model-router`, `panel`, `plugin_creator`, `session-recap`, `token_monitor`, `workflow_guard` — stock Evonic, no personal tweak

## 4. Skills & RTK

- **Skills dir:** 30 dirs — stock: `kanban`, `github`, `panel`, `explorer`, `subagent`, `scheduler`, etc. + personal:
  - `yii2_dev` — Yii2/SAAS conventions (ActiveRecord `45z_*`, `Controller_Foo`, migrations, `user/www/view/` + `static/` gulp)
  - `animation-vocabulary`, `apple-design`, `canvas-design`, `frontend-design`, `hallmark`, `improve-animations`, etc. — design/frontend taste
- **RTK filter:** `backend/token_compressor/filters/builtin/php.toml` — compresses `composer`/`php`/`codecept`/`yii` output (strip install noise, keep errors)
- **Skillsets:** `skillsets/php_yii2.json`
- **Shared:** `shared/agents`, `shared/db`, `shared/run`, `shared/bin`

## 5. Personal code diff (vs upstream fc334332)

### Tracked diff (2 files)

- `.gitignore` — ignore `artifacts/filemap.json`
- `static/js/chat-ui.js` — harden `_walkSanitize`: only `https://`, `mailto:`, `#`, `/api/` hrefs allowed; `img src` only `https://`/`/api/`/`data:image/`; drop `evHighlightCode` highlights path → plain `<code>.text()`

### Untracked (personal, not committed)

- `backend/token_compressor/filters/builtin/php.toml` — see §4
- `plugins/saas_dev_tools/` — 4 tools (lint/composer/migrate/gulp)
- `skills/yii2_dev/`, `skills/animation-vocabulary/`, `skills/apple-design/`, `skills/canvas-design/`, `skills/frontend-*`, `skills/hallmark/`, etc. + `skillsets/php_yii2.json`
- `start.sh` — PM2 wrapper

> No DB migration needed — personal tweaks are additive, no schema change.

## 6. Workspaces & Data

- **No `workspaces/` dir** on VPS (agents use `~/apps/evonic/agents/<name>/` directly + `sessions/`, `kb/`, `chat.db`)
- **Data:** `data/db/`, `data/uploads/`, `agents/*/chat.db` + `kb/`, `plan/kanban-task-*.md`, `artifacts/`, `logs/`
- **State:** `state/`, `shared/db`, `shared/run`

## 7. What to keep when removing Evonic

1. **Archive first:** `tar czf ~/evonic-backup-$(date +%Y%m%d).tar.gz -C ~/apps evonic --exclude=.venv --exclude=__pycache__ --exclude=logs` + dump `agents/*/kb/` + `agents/*/SYSTEM.md`
2. **Migrate to hermes-webui-personal if needed:**
   - `saas_dev_tools` → port as WebUI plugin or keep as local skill
   - `yii2_dev` skill → `~/.hermes/skills/` or WebUI skill
   - `php.toml` RTK filter → `~/.hermes/hermes-agent/backend/token_compressor/filters/builtin/`
   - `chat-ui.js` sanitize hardening → apply to WebUI `static/` if same pattern
3. **Teardown:** `pm2 delete evonic` → `sudo rm /etc/nginx/sites-enabled/evonic` → `sudo nginx -t && sudo systemctl reload nginx` → `rm -rf ~/apps/evonic` (after backup verified)
4. **DNS:** optionally remove `evonic.adityahimaone.space` A record or keep for redirect

## 8. Restore

```bash
# from backup
tar xzf ~/evonic-backup-YYYYMMDD.tar.gz -C ~/apps
cd ~/apps/evonic && .venv/bin/python -m cli start --host 0.0.0.0 --port 8090
pm2 start start.sh --name evonic --cwd ~/apps/evonic
sudo ln -s /etc/nginx/sites-available/evonic /etc/nginx/sites-enabled/evonic && sudo nginx -t && sudo systemctl reload nginx
```

---

*Generated from live VPS inventory — not from docs. Verify `agents/*/SYSTEM.md` + `kb/` content before deleting.*
