# Proposed Architecture: Decoupled, Resilient FastAPI Backend

This document details the target enterprise architecture proposed for Cynbit Technologies, replacing the monolithic Server Actions model with a decoupled, high-performance, security-hardened **FastAPI backend**.

---

## 1. Architectural Topology Overview

```
 [ Client Applications: Web / Mobile / CLI ]
                      |
                      | (HTTPS / TLS 1.3)
                      v
       [ Cloudflare Edge / WAF / Turnstile ]
                      |
                      v
       [ Reverse Proxy / Load Balancer: Nginx / Traefik ]
                      |
                      v
+-------------------------------------------------------------+
|              FASTAPI ASYNC BACKEND SERVICES                 |
+-------------------------------------------------------------+
| Middleware Pipeline:                                        |
|   - Strict Whitelisted CORS (cynbit.in only)                |
|   - Security Headers (CSP, HSTS, X-Frame-Options: DENY)     |
|   - Sliding Window Rate Limiter (IP + Route Key)           |
|   - Request Timing & Structured Audit Logger                |
|                                                             |
| API Routers (v1):                                           |
|   - /api/v1/auth        -> Argon2id, HttpOnly JWT, MFA      |
|   - /api/v1/inquiries   -> Pydantic Lead Ingestion          |
|   - /api/v1/careers     -> Applicant PII Vault, Constant-Time|
|   - /api/v1/payments    -> Cashfree Orders & Signed Webhook |
|   - /api/v1/intern      -> RBAC Protected Portal API        |
+-------------------------------------------------------------+
         |                        |                   |
         v                        v                   v
+------------------+    +-------------------+    +--------------------+
|   PostgreSQL 16  |    |   Redis Cluster   |    | Async Task Worker  |
| SQLAlchemy 2.0   |    | Rate Limiting     |    | (Celery / ARQ)     |
| Asyncpg Pool     |    | Session Blacklist |    | - Email Magic Links|
| Encrypted PII    |    | Cache Store       |    | - Order Fulfill    |
+------------------+    +-------------------+    +--------------------+
```

---

## 2. Core Architectural Pillars

### 2.1 Complete Presentation vs. Transaction Separation
- **Presentation Layer (Next.js):** Retained solely for marketing pages, SEO, and visual client components. The frontend acts as an unprivileged client communicating via standard JSON REST endpoints over HTTPS.
- **Transactional Backend (FastAPI):** All mutations, payment transactions, PII ingestion, and authentication run on a standalone, independently scaleable Python service.

### 2.2 Security-First Authentication & Identity
1. **Argon2id Hashing:** Password hashing uses RFC 9106 Argon2id (`time_cost=3`, `memory_cost=65536` KiB, `parallelism=4`).
2. **HttpOnly Cookie Authentication:** Upon login, the backend sets an `access_token` cookie configured with:
   - `HttpOnly = True` (inaccessible to JavaScript; immune to XSS)
   - `Secure = True` (transmitted exclusively over TLS)
   - `SameSite = "Strict"` (blocks Cross-Site Request Forgery)
3. **Role-Based Access Control (RBAC):** Every route verifies caller scopes (`applicant`, `intern`, `mentor`, `admin`) via FastAPI dependency injection.

### 2.3 Resilient, Event-Driven Payment Reconciliation
Instead of relying on fragile client-side callbacks:
1. **Server-to-Server Order Creation:** The backend communicates directly with Cashfree's REST API using secure server credentials stored in encrypted environment variables.
2. **Signed Asynchronous Webhooks:** Cashfree issues an HTTP POST to `/api/v1/payments/cashfree-webhook`.
3. **Cryptographic HMAC-SHA256 Verification:** The backend computes an HMAC digest using the merchant secret key and performs a constant-time comparison against the `x-webhook-signature` header.
4. **Idempotency & Atomic Settlement:** Database transactions update order status atomically, queuing an asynchronous background task to dispatch the magic onboarding link to the customer's email.

### 2.4 Scalable Database Connection Pooling
- **Engine:** PostgreSQL 16 using **SQLAlchemy 2.0** and **asyncpg**.
- **Pooling Strategy:** Pre-warmed persistent connection pool (`pool_size=20`, `max_overflow=10`, `pool_recycle=3600`).
- **Benefit:** Eliminates serverless connection exhaustion and delivers <2ms database query round-trip latency.

### 2.5 Centralized Sliding-Window Rate Limiting
- Every public endpoint is protected by a token bucket / sliding-window rate limiter keyed by client IP and route path.
- Lead submissions: 5 requests / minute.
- Career applications: 3 requests / 5 minutes.
- Auth attempts: 5 requests / 15 minutes (with exponential backoff).

