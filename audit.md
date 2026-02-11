# Clipsmith Full Application Audit

## Executive Summary

Clipsmith is a social video platform (TikTok-like) built with **FastAPI + Next.js 14**, featuring video upload/processing, creator monetization, analytics, and content moderation. The architecture follows Clean Architecture / DDD principles.

**However, this application is not production-ready.** The audit uncovered **critical vulnerabilities** across security, code quality, and infrastructure that must be addressed.

| Severity | Count |
|----------|-------|
| **CRITICAL** | 12 |
| **HIGH** | 18 |
| **MEDIUM** | 15 |
| **LOW** | 7 |

---

## CRITICAL Findings (Fix Immediately)

### 1. Hardcoded JWT Secret Key
**`backend/infrastructure/security/jwt_adapter.py:6`**
```python
SECRET_KEY = "super-secret-key-change-me"
```
Anyone with access to the code can forge valid JWT tokens and impersonate any user. This is not loaded from environment variables.

### 2. `eval()` on Untrusted Data — Remote Code Execution
**`backend/application/tasks.py:68`**
```python
"fps": eval(video_stream.get("r_frame_rate", "0/1"))
```
If ffprobe output is manipulated, arbitrary Python code executes. Replace with a safe fraction parser.

### 3. `.env.production` Committed to Git
**`.env.production`** contains placeholder secrets (Stripe keys, AWS keys, DB passwords) and is tracked in version control. Even with placeholders, this file pattern will lead to real secrets being committed.

### 4. Syntax Error Breaks Recommendation Engine
**`backend/application/services/recommendation_engine.py:17`**
```python
self Decay Factors = {   # Invalid syntax — space in variable name
```
This crashes on import, taking down the entire recommendation system.

### 5. Duplicate Video Save — Data Corruption
**`backend/application/use_cases/upload_video.py:45-70`**
Video is saved to the database **twice** and enqueued for processing **twice** in the same upload flow. This causes duplicate records and double processing.

### 6. Missing Authorization on Asset/Caption Deletion
**`backend/presentation/api/video_editor_router.py:184, 350`**
```python
# TODO: Check if asset belongs to user   ← NOT IMPLEMENTED
# TODO: Check if caption belongs to user  ← NOT IMPLEMENTED
```
Any authenticated user can delete any other user's assets and captions.

### 7. No Database Transactions on Financial Operations
**`backend/application/services/payment_service.py:118-159`**
Tip completion performs multiple DB writes (update sender, create receiver transaction, update wallet) **without a transaction wrapper**. If any step fails, money is lost or duplicated.

### 8. SQLite Hardcoded for All Environments
**`backend/infrastructure/repositories/database.py:5-6`**
```python
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
```
Does not read `DATABASE_URL` from environment. The docker-compose.production.yml references PostgreSQL, but the code **always uses SQLite**. No migration system (Alembic) exists.

### 9. Monitoring Router Has Fatal Bugs
**`backend/presentation/api/monitoring_router.py:33, 129-130`**
- Missing `import os` — crashes on access
- `while len(lines) < lines` — compares variable to itself
- `file_file.seek(...)` — typo, references nonexistent variable

### 10. Broken Import Crashes Video Editor
**`backend/presentation/api/video_editor_router.py:8`**
```python
from ...presentation.middleware.security import get_current_user
```
The module `security.py` does not exist in the middleware directory. All editor endpoints will crash.

### 11. Prometheus/Grafana Stack is Non-Functional
Production docker-compose includes Prometheus and Grafana but:
- `prometheus-client` not in `requirements.txt`
- Backend exposes no `/metrics` endpoint
- No dashboards or alert rules configured
- Entire monitoring stack is theater

### 12. Elasticsearch Security Disabled in Production
**`docker-compose.production.yml:223`**
```yaml
xpack.security.enabled=false
```
Anyone with network access can read/write all log data.

---

## HIGH Findings

| # | Finding | Location |
|---|---------|----------|
| 13 | `echo=True` logs all SQL queries (leaks sensitive data) | `database.py:9` |
| 14 | Debug `print()` statements in production routes | `video_router.py:312, 362` |
| 15 | `console.log` with PII (emails, payments) in frontend | `mockData.ts:5, 129, 144` |
| 16 | N+1 query: loads 1000 videos + 10000 interactions per feed request, **twice** | `get_personalized_feed.py:53-54, 108-109` |
| 17 | Race condition on view count increment (read-modify-write without lock) | `sqlite_video_repo.py:57-65` |
| 18 | Hardcoded MinIO credentials `minioadmin/minioadmin` | `docker-compose.minio.yml:9-11` |
| 19 | Default Grafana password is `admin` | `docker-compose.production.yml:203` |
| 20 | Default Postgres password fallback in compose | `docker-compose.production.yml:11` |
| 21 | CORS allows all methods and all headers | `main.py:54-60` |
| 22 | CI/CD never builds Docker images | `.github/workflows/ci.yml` |
| 23 | No security scanning (SAST/dependency) in pipeline | `.github/workflows/ci.yml` |
| 24 | Deploy script uses self-signed certificates for production | `scripts/deploy.sh:109-118` |
| 25 | Sentry `traces_sample_rate=1.0` — captures all traces (extreme cost) | `monitoring_service.py:226-243` |
| 26 | All `async` methods in video editor service don't `await` anything | `video_editor_service.py` |
| 27 | Missing CSRF protection | Application-wide |
| 28 | No Content Security Policy or security headers (HSTS, X-Frame-Options, etc.) | Application-wide |
| 29 | `requestAnimationFrame` memory leak on component unmount | `video-editor.tsx:146-165` |
| 30 | Open redirect via unvalidated `return_url`/`refresh_url` in Stripe setup | `payment_router.py:48-59` |

---

## MEDIUM Findings

| # | Finding | Location |
|---|---------|----------|
| 31 | JWT token expiration is 60 minutes (too long) | `authenticate_user.py:23-25` |
| 32 | Token stored in localStorage (vulnerable to XSS) | `auth-store.ts` |
| 33 | PascalCase instance variables violate PEP 8 | `recommendation_engine.py:25-26` |
| 34 | `json`, `os`, `uuid` imported inside functions | `video_editor_router.py:127, 212` |
| 35 | Integration tests are empty `pass` stubs | `test_services.py:323-332` |
| 36 | `debug_hash.py` with hardcoded "password123" in repo | `backend/debug_hash.py` |
| 37 | 611-line VideoEditor component (too complex) | `video-editor.tsx` |
| 38 | 607-line CreatorDashboard component | `CreatorDashboard.tsx` |
| 39 | No database migration system (only `create_all()`) | `database.py:11-12` |
| 40 | Next.js `remotePatterns` only allows localhost images | `next.config.ts:5-11` |
| 41 | No container resource limits in docker-compose | `docker-compose.production.yml` |
| 42 | No frontend testing libraries installed | `frontend/package.json` |
| 43 | Broad `except Exception` everywhere, masking bugs | Multiple files |
| 44 | Missing input validation (length limits, type checks) on form fields | Multiple routers |
| 45 | `check_same_thread=False` on SQLite without proper concurrency handling | `database.py:8` |

---

## LOW Findings

| # | Finding | Location |
|---|---------|----------|
| 46 | Password reset token in URL (logged by browsers/proxies) | `auth_router.py:128` |
| 47 | `any` types in TypeScript (defeats type safety) | `client.ts:9`, `usePayment.ts:48, 81` |
| 48 | Rate limiting on password reset could be stricter | `auth_router.py:99` |
| 49 | Poetry + requirements.txt inconsistency | `backend/` |
| 50 | Multiple Dockerfiles create confusion | Root directory |
| 51 | API errors forwarded directly to users | `client.ts:24-25` |
| 52 | No deploy rollback capability | `scripts/deploy.sh` |

---

## Resolution Status

- [ ] Finding 1 — Hardcoded JWT secret
- [ ] Finding 2 — eval() RCE
- [ ] Finding 3 — .env.production in git
- [ ] Finding 4 — Syntax error in recommendation engine
- [ ] Finding 5 — Duplicate video save
- [ ] Finding 6 — Missing authorization checks
- [ ] Finding 7 — No DB transactions on payments
- [ ] Finding 8 — SQLite hardcoded
- [ ] Finding 9 — Monitoring router bugs
- [ ] Finding 10 — Broken import in video editor
- [ ] Finding 11 — Non-functional Prometheus/Grafana
- [ ] Finding 12 — Elasticsearch security disabled
- [ ] Finding 13 — SQL query logging
- [ ] Finding 14 — Debug print statements
- [ ] Finding 15 — console.log with PII
- [ ] Finding 16 — N+1 queries in feed
- [ ] Finding 17 — Race condition on views
- [ ] Finding 18 — Hardcoded MinIO credentials
- [ ] Finding 19 — Default Grafana password
- [ ] Finding 20 — Default Postgres password
- [ ] Finding 21 — Overly permissive CORS
- [ ] Finding 22 — CI/CD missing Docker build
- [ ] Finding 23 — No security scanning
- [ ] Finding 24 — Self-signed certs
- [ ] Finding 25 — Sentry traces_sample_rate=1.0
- [ ] Finding 26 — Fake async methods
- [ ] Finding 27 — Missing CSRF protection
- [ ] Finding 28 — Missing security headers
- [ ] Finding 29 — Animation memory leak
- [ ] Finding 30 — Open redirect
- [ ] Finding 31 — JWT expiration too long
- [ ] Finding 32 — Token in localStorage
- [ ] Finding 33 — PascalCase variables
- [ ] Finding 34 — Imports inside functions
- [ ] Finding 35 — Stub tests
- [ ] Finding 36 — debug_hash.py
- [ ] Finding 37 — Large VideoEditor component
- [ ] Finding 38 — Large CreatorDashboard component
- [ ] Finding 39 — No migration system
- [ ] Finding 40 — Next.js remotePatterns
- [ ] Finding 41 — No container resource limits
- [ ] Finding 42 — No frontend testing
- [ ] Finding 43 — Broad exception handling
- [ ] Finding 44 — Missing input validation
- [ ] Finding 45 — SQLite thread safety
- [ ] Finding 46 — Reset token in URL
- [ ] Finding 47 — any types in TypeScript
- [ ] Finding 48 — Rate limiting
- [ ] Finding 49 — Poetry inconsistency
- [ ] Finding 50 — Multiple Dockerfiles
- [ ] Finding 51 — API errors forwarded
- [ ] Finding 52 — No rollback capability
