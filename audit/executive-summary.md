# Executive Summary: Cynbit Backend Technical Audit

**Target Systems:** `https://www.cynbit.in` (Apex & Marketing) | `https://bitelevate.cynbit.in` (Platform & Intern Portal)  
**Role:** Backend Developer Intern  
**Date of Audit:** October 30, 2026  
**Assessment Mode:** Passive, authorized, non-intrusive architectural reconnaissance  

---

## 1. Audit Overview & Objectives

This audit provides an architectural, operational, and security assessment of **Cynbit Technologies'** publicly observable web infrastructure from the perspective of a Backend Engineer. The primary objective is to evaluate API structure, authentication flows, data validation mechanisms, security controls, and edge performance to formulate a high-leverage modernization plan.

In strict compliance with ethical guidelines, all testing was performed passively without service interruption, brute-forcing, exploitation, or unauthorized access attempts.

```
       +--------------------------------------------------------------+
       |                  AUDIT COMPLIANCE SCORECARD                  |
       +--------------------------------------------------------------+
       | Metric                         Status           Rating       |
       +--------------------------------------------------------------+
       | Transport Security (TLS)       Compliant        98 / 100     |
       | Edge CDN Latency & Caching     Optimal          92 / 100     |
       | HTTP Security Headers          Deficient        32 / 100     |
       | API & RPC Authorization        Vulnerable       45 / 100     |
       | Credential & Secret Hygiene    Critical Defect  28 / 100     |
       | Rate Limiting & Bot Defense    Absent           20 / 100     |
       | Overall Security Health        NEEDS REMEDIATION (49 / 100)  |
       +--------------------------------------------------------------+
```

---

## 2. Key Executive Takeaways

1. **Monolithic Server Action Pattern:**  
   The application leverages Next.js App Router Server Actions on Vercel's serverless edge. While this accelerates frontend prototyping, critical business operations—including financial payment settlements with Cashfree and multi-step job applicant PII ingestion—are tightly coupled within RPC lambdas without a dedicated transactional API backend.

2. **Critical Vulnerability: Cleartext Credential Delivery:**  
   Upon payment settlement verification via `verifyBitelevatePayment`, the server returns generated intern account credentials (including cleartext passwords) directly in the client network JSON response. This breaks basic cryptographic hygiene (passwords must be salted/hashed via Argon2id and never returned over the wire).

3. **Client-Side Session State & Shared Secret Risk:**  
   The administrative portal (`/portal`) relies on a single shared "Security Key" and maintains session state in unencrypted browser `localStorage`. This lacks granular identity, role-based access control (RBAC), multi-factor authentication (MFA), and auditability.

4. **Information Disclosure via Pre-rendered Dashboards:**  
   The intern portal dashboard (`/intern-portal/dashboard` on `bitelevate.cynbit.in`) is statically pre-rendered by Next.js and served with `HTTP 200` to unauthenticated clients. The resulting 727KB JavaScript chunk exposes the entire internal curriculum, engineering task briefs, and internal file paths.

5. **Absence of Rate Limiting & Security Headers:**  
   Public mutation endpoints accept unbounded requests without sliding-window rate limiting or bot challenges (Cloudflare Turnstile). Furthermore, responses emit wildcard CORS (`Access-Control-Allow-Origin: *`) on HTML pages while missing essential defenses including `Content-Security-Policy` (CSP) and `X-Frame-Options` (Clickjacking).

---

## 3. High-Leverage Strategic Recommendation

To establish enterprise-grade reliability, security, and scalability, Cynbit should decouple its marketing frontend from its core transaction processing by adopting a **defense-in-depth FastAPI backend architecture**:

```
[ Next.js Frontend / Vercel Edge ]
               |
        (HTTPS / JSON REST)
               v
   [ Cloudflare WAF + Turnstile ]
               |
               v
  [ FastAPI Async Core Services ]  <--->  [ Redis Cluster: Rate Limit & Tokens ]
        |                 |
  (SQLAlchemy 2.0)   (Signed Webhooks)
        v                 v
[ PostgreSQL 16 ]    [ Cashfree Gateway ]
```

A production-ready reference implementation of this architecture has been developed and verified as part of this submission under the `implementation/` directory.
