# Security Findings & Vulnerability Register

This report categorizes observable security vulnerabilities and architectural design weaknesses discovered during the passive technical audit of Cynbit Technologies.

---

## Vulnerability Summary Matrix

| ID | Title | Severity | CVSS v3.1 | CWE | OWASP Top 10 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | Cleartext Password Delivery in API Settlement Response | **HIGH** | `8.2` | CWE-312 / CWE-319 | A02:2021 – Cryptographic Failures |
| **SEC-02** | Insecure Authentication & Session State in Client LocalStorage | **HIGH** | `7.5` | CWE-287 / CWE-798 | A07:2021 – Identification & Auth Failures |
| **SEC-03** | Broken Access Control via Static Pre-rendered Dashboard Leak | **MEDIUM** | `6.5` | CWE-200 / CWE-285 | A01:2021 – Broken Access Control |
| **SEC-04** | User & Applicant Enumeration via Differential Responses | **MEDIUM** | `5.3` | CWE-203 / CWE-204 | A04:2021 – Insecure Design |
| **SEC-05** | Missing Security Headers & Wildcard CORS Configuration | **MEDIUM** | `5.3` | CWE-942 / CWE-693 | A05:2021 – Security Misconfiguration |
| **SEC-06** | Unrestricted RPC Endpoints & Lack of Rate Limiting / Bot Defense | **MEDIUM** | `6.5` | CWE-799 / CWE-400 | A04:2021 – Insecure Design |
| **SEC-07** | Insecure Payment Settlement Flow Dependent on Client Callback | **HIGH** | `7.4` | CWE-345 / CWE-353 | A08:2021 – Software & Data Integrity |

---

## Detailed Findings

### SEC-01: Cleartext Password Delivery in API Settlement Response
- **Severity:** HIGH (CVSS 8.2: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N`)
- **CWE:** CWE-312 (Cleartext Storage of Sensitive Information), CWE-319 (Cleartext Transmission of Sensitive Information)
- **Observable Behavior:**
  When candidate payment is verified via `verifyBitelevatePayment`, the server dispatches a JSON payload containing generated credentials in plaintext:
  ```json
  {
    "success": true,
    "bitElevateCredentials": {
      "email": "candidate@example.com",
      "password": "PLAINTEXT_SECRET"
    }
  }
  ```
  The client frontend executes `navigator.clipboard.writeText(...)` to place this password in the operating system clipboard.
- **Impact:**
  Plaintext passwords traverse middleboxes, browser cache/logs, and clipboard memory. Furthermore, it indicates passwords may either be stored in plaintext or reversible encryption in the database, directly violating cryptographic standards (e.g., NIST SP 800-63B).
- **Remediation:**
  1. Never generate, return, or transmit raw passwords over the network.
  2. Implement an asynchronous **Email Onboarding Flow**: upon payment settlement, generate a high-entropy, cryptographically secure single-use token (`secrets.token_urlsafe(32)`), store its SHA-256 hash with an expiry timestamp (e.g., 24 hours), and dispatch an onboarding link to the user's email.
  3. Have the user choose their own password, hashed with **Argon2id** (memory: 64MB, iterations: 3, parallelism: 4).

---

### SEC-02: Insecure Authentication & Session State in Client LocalStorage
- **Severity:** HIGH (CVSS 7.5: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`)
- **CWE:** CWE-287 (Improper Authentication), CWE-798 (Use of Hard-coded Credentials), CWE-384 (Session Fixation)
- **Observable Behavior:**
  In `app/portal/page-ba479285e84c64b5.js`:
  ```javascript
  let a = await l(t); // loginToPortal
  if (a.success) {
      localStorage.setItem("cynbit_portal_last_activity", Date.now().toString());
      window.location.href = "/dashboard";
  }
  ```
  The portal accepts a single shared "Security Key" without user-specific identification or MFA. Session longevity is verified on the client via `localStorage`.
- **Impact:**
  1. A shared password prevents individual non-repudiation and audit logging.
  2. Any cross-site script (XSS) can immediately read or tamper with `localStorage`.
- **Remediation:**
  1. Replace the shared security key with user-specific identity accounts and Role-Based Access Control (RBAC).
  2. Issue short-lived JSON Web Tokens (JWT) stored exclusively in `HttpOnly`, `Secure`, `SameSite=Strict` cookies, completely inaccessible to JavaScript.

---

### SEC-03: Broken Access Control via Static Pre-rendered Dashboard Leak
- **Severity:** MEDIUM (CVSS 6.5: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`)
- **CWE:** CWE-200 (Exposure of Sensitive Information), CWE-285 (Improper Authorization)
- **Observable Behavior:**
  Sending an unauthenticated HTTP GET request to `https://bitelevate.cynbit.in/dashboard` returns:
  ```http
  HTTP/2 200 OK
  x-matched-path: /intern-portal/dashboard
  x-nextjs-prerender: 1
  x-vercel-cache: PRERENDER
  ```
  The response serves a **727,015 byte** JavaScript bundle (`page-6430ee332a6a7642.js`) containing the complete engineering curriculum, challenge descriptions, internal file hierarchies (`backend/app/main.py`), and proprietary course data.
- **Impact:**
  Proprietary internal content and training materials are publicly exposed without requiring valid user authentication.
- **Remediation:**
  1. Remove static prerendering (`export const dynamic = 'force-dynamic'`) on authenticated dashboard routes.
  2. Implement server-side edge middleware (`middleware.ts` in Next.js or reverse proxy in FastAPI) that validates session cookies *before* returning any HTML or JavaScript bundles.

---

### SEC-04: User & Applicant Enumeration via Differential Responses
- **Severity:** MEDIUM (CVSS 5.3: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N`)
- **CWE:** CWE-203 (Observable Discrepancy), CWE-204 (Observable Discrepancy in Response)
- **Observable Behavior:**
  1. **Job Applications:** When a candidate's email exists, the backend returns:
     `"You have already submitted an active application for this position. Your profile is currently under review..."` along with a personal tracking portal link.
  2. **Password Resets:** The backend differentiates between valid and invalid emails:
     `"A password reset link has been dispatched..."` vs `"Unable to send reset link. Please check your email address."`
- **Impact:**
  Attackers can mass-query phone numbers and emails to deduce who has applied to Cynbit or who holds an intern account.
- **Remediation:**
  Return uniform, constant-time status messages regardless of whether the email or phone number exists in the database:
  `"If an account or active submission exists for this email address, you will receive confirmation instructions shortly."`

---

### SEC-05: Missing Security Headers & Wildcard CORS Configuration
- **Severity:** MEDIUM (CVSS 5.3: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N`)
- **CWE:** CWE-942 (Overly Permissive CORS), CWE-693 (Protection Mechanism Failure)
- **Observable Behavior:**
  Responses on `cynbit.in` return `access-control-allow-origin: *` while omitting:
  - `Content-Security-Policy` (CSP)
  - `X-Frame-Options`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy`
  - `Permissions-Policy`
- **Impact:**
  Facilitates Clickjacking attacks (framing Cynbit forms inside malicious overlays) and increases XSS exploitability.
- **Remediation:**
  Implement a strict Security Headers middleware enforcing:
  ```http
  Content-Security-Policy: default-src 'self'; script-src 'self' https://sdk.cashfree.com; frame-ancestors 'none';
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  ```

---

### SEC-06: Unrestricted RPC Execution & Lack of Rate Limiting
- **Severity:** MEDIUM (CVSS 6.5: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:L`)
- **CWE:** CWE-799 (Improper Control of Interaction Frequency), CWE-400 (Uncontrolled Resource Consumption)
- **Observable Behavior:**
  Next.js Server Actions on `submitInquiry`, `submitCandidateApplication`, and `createBitelevateCashfreeOrder` accept high-frequency HTTP POST invocations without rate-limit counters or CAPTCHA validation.
- **Impact:**
  Spam inundation, database bloat, serverless execution cost spikes, and potential Cashfree merchant account throttling.
- **Remediation:**
  Integrate a sliding-window rate limiter in Redis (e.g. 5 requests / 60 seconds per IP on sensitive mutation endpoints) and deploy Cloudflare Turnstile on public forms.

---

### SEC-07: Insecure Payment Settlement Flow Dependent on Client Callback
- **Severity:** HIGH (CVSS 7.4: `CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N`)
- **CWE:** CWE-345 (Insufficient Verification of Data Authenticity), CWE-353 (Missing Support for Integrity Check)
- **Observable Behavior:**
  Payment settlement verification relies primarily on a client-triggered Server Action (`verifyBitelevatePayment(token, orderId)`) upon the Cashfree modal closing.
- **Impact:**
  If a customer's internet drops, or if they close their browser immediately after authorization, the client never triggers `verifyBitelevatePayment`. Consequently, the customer is charged, but no credentials or account records are generated. Conversely, relying solely on client callbacks creates race conditions.
- **Remediation:**
  Adopt an **Event-Driven Webhook Reconciliation Architecture**:
  1. Cashfree sends asynchronous server-to-server HTTP POST notifications to a dedicated webhook endpoint (`/api/v1/payments/cashfree-webhook`).
  2. The backend cryptographically validates the signature header using **HMAC-SHA256** with the merchant secret key.
  3. Orders are transitioned to `PAID` idempotently within a transactional database lock.

