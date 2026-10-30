# Current Architecture: Observable Architecture & Risk Analysis

This report documents the architectural patterns, data flows, and structural risks currently observable across Cynbit's production deployments.

---

## 1. Architectural Topology Overview

Cynbit currently operates a **Monolithic Next.js Full-Stack Application** hosted on **Vercel's Global Edge Network**.

```
+-------------------------------------------------------------------------------+
|                           CURRENT SYSTEM TOPOLOGY                             |
+-------------------------------------------------------------------------------+

 [ Clients: Browsers / Mobile Devices ]
                 |
                 | (HTTPS / TLS 1.3)
                 v
   [ Vercel Anycast Edge: Mumbai bom1 ]
                 |
     +-----------+-----------+
     |                       |
 (Static GET)            (Dynamic RPC POST)
     |                       |
     v                       v
[ Static Prerender ]    [ Next.js Server Actions ]
  - Marketing Pages       - submitInquiry
  - 727KB Dashboard       - submitCandidateApplication
    (Unprotected Leak)    - createBitelevateCashfreeOrder
                          - verifyBitelevatePayment (Leaks Passwords)
                          - loginToPortal (Shared Secret)
                             |
                     +-------+-------+
                     |               |
                     v               v
            [ Cashfree SDK ]   [ External Database / Storage ]
            (Client Modal)     (Unpooled Serverless Handshakes)
```

---

## 2. In-Depth Component Analysis

### 2.1 Edge Delivery Layer
- **Provider:** Vercel Edge Anycast (`bom1` PoP).
- **Behavior:** Static assets and marketing pages are aggressively cached. While this yields sub-50ms TTFB for cached marketing pages, it creates serious security oversights when internal dashboard pages (such as `/intern-portal/dashboard`) are marked static by the compiler (`x-nextjs-prerender: 1`), leaking proprietary materials to unauthenticated GET requests.

### 2.2 Application & RPC Layer
- **Implementation:** Next.js Server Actions (React Server Components wire protocol).
- **Mechanism:** Asynchronous RPC calls using hashed function identifiers (e.g. `40645a00...` for `submitCandidateApplication`).
- **Architectural Weaknesses:**
  1. **Monolithic Coupling:** Front-of-the-glass visual styling and mission-critical transactional business logic (financial settlements, PII ingestion, applicant scoring) share the same build lifecycle. A bug in a CSS import or marketing page can break backend mutation handlers.
  2. **Stateless Lambdas without Centralized State:** Because Server Actions execute across ephemeral serverless containers, maintaining rate-limit state, persistent connection pools, or token revocation lists is virtually impossible without an external store like Redis.

### 2.3 Data Storage & Database Interaction
- **Connection Mechanics:** Under serverless execution, each incoming user request can trigger a cold start that opens a new TCP connection to the backend database.
- **Risk:** During a marketing push or campus hiring deadline, concurrent traffic causes connection spikes that can overwhelm database connection limits, leading to connection timeouts and dropped transactions.

### 2.4 Authentication & Identity Management
- **Observed Pattern:**
  - Administrative portal (`/portal`) relies on a single shared key.
  - Intern portal (`/intern-portal/login`) accepts email and password, but payment verification dispatches the plaintext password back to the user's browser.
  - State management uses client-side `localStorage`, making sessions vulnerable to tampering and XSS extraction.

---

## 3. Structural Bottlenecks Summary

| Architectural Area | Observed Pattern | Architectural Vulnerability |
| :--- | :--- | :--- |
| **API Architecture** | Proprietary Server Actions RPC | No versioned REST/OpenAPI contracts; difficult to integrate with mobile apps or third-party webhooks. |
| **Authentication** | Shared key + client `localStorage` | Lack of RBAC, identity isolation, or cryptographically secure HttpOnly session cookies. |
| **Credential Hygiene** | Raw password returned in JSON | Severe cryptographic violation (CWE-312 / CWE-319). |
| **Payment Flow** | Client-side modal settlement | Risk of unpaid fulfillments or unfulfilled orders on network disconnects. |
| **Access Control** | Static prerendering of private dashboards | Proprietary intern curriculum and engineering challenges exposed to the public internet. |
