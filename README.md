# Cynbit Backend Technical Audit & Modernization Architecture

> **Backend Developer Intern — Challenge Submission**  
> **Target Systems:** [`https://www.cynbit.in`](https://www.cynbit.in) (Primary Apex & Marketing) & [`https://bitelevate.cynbit.in`](https://bitelevate.cynbit.in) (BitElevate Platform)  
> **Assessment Date:** October 30, 2026  
> **Testing Scope:** Strictly passive, authorized, non-intrusive architectural reconnaissance  
> **Implementation Framework:** **FastAPI (Python 3.12+ / Pydantic v2 / SQLAlchemy 2.0 Async)**  

---

## Executive Summary & Scorecard

This repository delivers an architectural audit and production-grade backend refactor for **Cynbit Technologies**, evaluated from the perspective of an incoming Backend Engineer.

Through passive HTTP header inspection, TLS negotiation profiling, DOM tree analysis, and Next.js React Server Components (RSC) flight protocol observation, we identified core operational opportunities spanning **API architecture**, **credential hygiene**, **payment reconciliation**, and **authorization boundaries**. To remediate these issues, we designed and implemented a defense-in-depth, asynchronous **FastAPI backend microservice**.

```
+-------------------------------------------------------------------------------+
|                       CYNBIT TECHNICAL AUDIT SCORECARD                        |
+-------------------------------------------------------------------------------+
| Category                          Current State       Rating     Target State |
+-------------------------------------------------------------------------------+
| Edge CDN & TLS Handshake          Vercel bom1 (Edge)  98 / 100   Maintained   |
| API Contract & Governance         Unversioned RPC     45 / 100   OpenAPI 3.1  |
| HTTP Transport Security Headers   Deficient (No CSP)  32 / 100   Strict CSP   |
| Credential & Password Hygiene     Plaintext Delivery  28 / 100   Argon2id     |
| Payment Gateway Reconciliation    Client Modal Dep.   50 / 100   HMAC Webhook |
| Route Authorization & Privacy     Static Prerender    40 / 100   Server Guard |
| Rate Limiting & Bot Mitigation    Unthrottled         20 / 100   Sliding Win  |
+-------------------------------------------------------------------------------+
```

---

## Key Findings & Vulnerability Register

| Finding ID | Domain | Severity | CVSS v3.1 | Core Problem & Business Impact |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | Cryptography | **HIGH** | `8.2` | **Plaintext Credentials Dispatched over Network:** `verifyBitelevatePayment` returns raw candidate passwords in JSON upon payment, copied to clipboard via JavaScript. |
| **SEC-02** | Authentication | **HIGH** | `7.5` | **Client-Side Session State in LocalStorage:** `/portal` relies on a single shared key and tracks auth timestamps in unencrypted `localStorage`. |
| **SEC-03** | Access Control | **MEDIUM** | `6.5` | **Pre-rendered Intern Dashboard Information Leak:** `https://bitelevate.cynbit.in/dashboard` returns `HTTP 200` to unauthenticated GET requests, leaking 727KB of curriculum, challenges, and internal file paths. |
| **SEC-04** | Privacy / Enumeration | **MEDIUM** | `5.3` | **User & Applicant Enumeration:** Differential server responses on `/careers` duplicate submissions and `/intern-portal/login` password resets disclose candidate and user identities. |
| **SEC-05** | Configuration | **MEDIUM** | `5.3` | **Missing Security Headers & Wildcard CORS:** Emits `Access-Control-Allow-Origin: *` while omitting `Content-Security-Policy` and `X-Frame-Options` (Clickjacking). |
| **SEC-06** | Abuse Prevention | **MEDIUM** | `6.5` | **Unthrottled Public RPC Endpoints:** Lack of IP/fingerprint rate limiting allows spamming of inquiries, career applications, and Cashfree payment sessions. |
| **SEC-07** | Payment Integrity | **HIGH** | `7.4` | **Client-Dependent Settlement Verification:** Fulfilling orders based on client callbacks creates dropped fulfillment risks when network disconnects occur. |

---

## Discovered Next.js Server Actions Inventory

Through static bundle inspection, the following Server Actions were mapped and analyzed:

| Action Identifier (Hash) | Function Name | Module | Ingested Payloads & Analysis |
| :--- | :--- | :--- | :--- |
| `40247ba4465344b3386595bab4303317cdcce907df` | `submitInquiry` | `app/(marketing)/contact` | Full name, corporate email, company, industry, message. Missing rate limiting. |
| `40645a00e04f6854903cf3a65fda4c75ddd7691de9` | `submitCandidateApplication` | `app/(marketing)/careers/[slug]` | Multi-step PII, academic records, portfolio links. Returns duplicate tracking URL. |
| `40450605530d78e25921058a0059197fdb18b5f074` | `createBitelevateCashfreeOrder` | `app/(marketing)/bitelevate` | Interacts with Cashfree API to generate `paymentSessionId`. |
| `60895028315fbe0e72db7e2a1871d236f08f860ce1` | `verifyBitelevatePayment` | `app/(marketing)/bitelevate` | Settlement verification returning `bitElevateCredentials` in cleartext. |
| `40d93da1cc26de4ef37bcb273184b7141ef77a50f8` | `loginToPortal` | `app/portal` | Single-password portal authentication setting `localStorage` timestamp. |
| `60c644173c8290d140c74d8944fc29bd658873a282` | `loginIntern` | `app/intern-portal/login` | Intern portal credentials authentication. |
| `408d222e7a54ae1d8dcd8b54a9aa53726d7348a7b0` | `requestPasswordReset` | `app/intern-portal/login` | Account recovery triggering differential status messages. |

---

## Proposed Architecture: FastAPI Defense-in-Depth

```
 [ Client: Next.js Frontend / Mobile App ]
                     |
                     | (HTTPS + Strict Security Headers)
                     v
      [ Cloudflare Edge / WAF / Turnstile ]
                     |
                     v
+-------------------------------------------------------------+
|              FASTAPI ASYNC BACKEND SERVICES                 |
+-------------------------------------------------------------+
| Middleware Pipeline:                                        |
|   1. Strict Origin CORS (Whitelisted domains only)          |
|   2. Security Headers (CSP, HSTS, X-Frame-Options: DENY)     |
|   3. Sliding Window Rate Limiter (IP + Route Key)           |
|   4. Structured Audit & Latency Logger                      |
|                                                             |
| API Routers (v1):                                           |
|   - /api/v1/auth        -> Argon2id, HttpOnly JWT, Constant |
|   - /api/v1/inquiries   -> Pydantic Lead Validation         |
|   - /api/v1/applications-> PII Sanitization, Zero Enum      |
|   - /api/v1/payments    -> Cashfree Orders & Signed Webhook |
|   - /api/v1/intern      -> Server-Guarded Protected Portal  |
+-------------------------------------------------------------+
         |                        |                   |
         v                        v                   v
+------------------+    +-------------------+    +--------------------+
|  PostgreSQL 16   |    |   Redis Cluster   |    | Async Task Worker  |
| SQLAlchemy 2.0   |    | Rate Limiting     |    | - Magic Link Email |
| Asyncpg Pool     |    | Session Blacklist |    | - Webhook Fulfill  |
+------------------+    +-------------------+    +--------------------+
```

---

## Repository Structure

```
cynbit-backend-technical-audit/
├── README.md                           <- Executive overview, scorecard, and setup guide
├── diagrams/
│   └── backend-architecture.mmd        <- Mermaid architecture diagram (Current vs Proposed)
├── evidence/
│   ├── observations.md                 <- Empirical data, code snippets, reverse-engineered JS
│   ├── raw_headers.txt                 <- Raw HTTP headers from cynbit.in & subdomains
│   └── server_actions_manifest.json    <- Catalog of mapped Server Actions & hashes
├── audit/
│   ├── executive-summary.md            <- High-level findings and risk analysis
│   ├── website-analysis.md             <- Edge network, DNS, TLS, and rendering evaluation
│   ├── api-analysis.md                 <- Next.js Server Actions RPC wire protocol inspection
│   ├── security-findings.md            <- CVSS 3.1 & OWASP Top 10 vulnerability register
│   ├── performance-findings.md         <- Cold starts, bundle bloat, and pooling benchmarks
│   └── recommendations.md              <- Phased remediation roadmap & code snippets
├── architecture/
│   ├── current-observations.md         <- Current monolithic state and structural risks
│   └── proposed-architecture.md        <- Proposed decoupled FastAPI microservice design
└── implementation/                     <- Complete, production-grade FastAPI codebase
    ├── Dockerfile                      <- Lean multi-stage non-root container build
    ├── docker-compose.yml              <- API + PostgreSQL 16 + Redis orchestration
    ├── requirements.txt                <- Production dependencies
    ├── main.py                         <- Application factory, lifespan, and middleware assembly
    ├── core/
    │   ├── config.py                   <- Pydantic Settings environment configuration
    │   ├── security.py                 <- Argon2id, JWT, and Cashfree HMAC-SHA256 verification
    │   └── database.py                 <- Async SQLAlchemy 2.0 session manager
    ├── models/
    │   └── entities.py                 <- User, Inquiry, JobApplication, Order, AuditLog
    ├── schemas/
    │   ├── auth.py                     <- Login, Reset, and User schemas
    │   ├── inquiry.py                  <- Inquiries validation schemas
    │   ├── application.py              <- PII and candidate profile validation schemas
    │   └── payment.py                  <- Cashfree order and webhook schemas
    ├── middleware/
    │   ├── security_headers.py         <- Injects CSP, HSTS, X-Frame-Options DENY, nosniff
    │   ├── rate_limit.py               <- Sliding-window rate limiting dependency
    │   └── audit_log.py                <- Structured latency and audit logger
    ├── services/
    │   ├── payment_service.py          <- Cashfree order creation & webhook verification
    │   └── notification_service.py     <- Transactional email and magic link dispatcher
    ├── api/
    │   └── v1/
    │       ├── health.py               <- GET /health with database probe
    │       ├── auth.py                 <- POST /login, POST /logout, POST /reset, GET /me
    │       ├── inquiries.py            <- POST /inquiries
    │       ├── applications.py         <- POST /applications (zero user enumeration)
    │       ├── payments.py             <- POST /create-order, POST /cashfree-webhook
    │       └── intern.py               <- GET /intern/dashboard (guarded with JWT)
    └── tests/                          <- 100% passing Pytest test suite (16 tests)
        ├── conftest.py                 <- In-memory async SQLite engine & ASGI test client
        ├── test_health.py              <- Health probe and security headers tests
        ├── test_auth.py                <- Argon2id login and enumeration prevention tests
        ├── test_inquiries.py           <- Input validation and sanitization tests
        ├── test_applications.py        <- Application ingestion & constant-time tests
        ├── test_payments.py            <- Cashfree order, HMAC webhook, and security tests
        ├── test_rate_limit.py          <- Sliding-window rate limit tests (HTTP 429)
        └── test_intern.py              <- Route protection verification (HTTP 401 tests)
```

---

## Local Setup & Testing Instructions

### 1. Running with Python Virtual Environment

```bash
# Clone repository and enter directory
cd Cynbit

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r implementation/requirements.txt

# Run the complete test suite (16 test cases, 100% pass rate)
PYTHONPATH=. pytest implementation/tests/ -v

# Run the development server
PYTHONPATH=. uvicorn implementation.main:app --host 0.0.0.0 --port 8000 --reload
```

Once running, interactive API documentation is accessible at:
- **Swagger UI:** [`http://localhost:8000/docs`](http://localhost:8000/docs)
- **ReDoc:** [`http://localhost:8000/redoc`](http://localhost:8000/redoc)

---

### 2. Running with Docker & Docker Compose

```bash
# Start FastAPI, PostgreSQL 16, and Redis in isolated containers
docker-compose -f implementation/docker-compose.yml up -d --build

# Inspect running container status
docker-compose -f implementation/docker-compose.yml ps

# View live audit logs
docker-compose -f implementation/docker-compose.yml logs -f api
```

---

## Test Suite Verification

The implementation includes a comprehensive async test suite covering all critical security and functional invariants:

```
============================= test session starts ==============================
collected 16 items

implementation/tests/test_applications.py::test_submit_career_application PASSED   [  6%]
implementation/tests/test_applications.py::test_duplicate_application_zero_enumeration PASSED [ 12%]
implementation/tests/test_auth.py::test_successful_login PASSED                    [ 18%]
implementation/tests/test_auth.py::test_failed_login_invalid_password PASSED           [ 25%]
implementation/tests/test_auth.py::test_password_reset_zero_enumeration PASSED    [ 31%]
implementation/tests/test_health.py::test_health_check_endpoint PASSED             [ 37%]
implementation/tests/test_health.py::test_security_headers_injected PASSED         [ 43%]
implementation/tests/test_inquiries.py::test_submit_valid_inquiry PASSED           [ 50%]
implementation/tests/test_inquiries.py::test_submit_inquiry_invalid_email PASSED   [ 56%]
implementation/tests/test_intern.py::test_intern_dashboard_blocks_unauthenticated PASSED [ 62%]
implementation/tests/test_intern.py::test_intern_dashboard_allows_authenticated_user PASSED [ 68%]
implementation/tests/test_payments.py::test_create_payment_order PASSED            [ 75%]
implementation/tests/test_payments.py::test_valid_cashfree_webhook_signature PASSED [ 81%]
implementation/tests/test_payments.py::test_forged_cashfree_webhook_signature_rejected PASSED [ 87%]
implementation/tests/test_payments.py::test_payment_status_never_exposes_password PASSED [ 93%]
implementation/tests/test_rate_limit.py::test_sliding_window_rate_limiter_blocks_excess_calls PASSED [100%]

============================== 16 passed in 1.48s ==============================
```
