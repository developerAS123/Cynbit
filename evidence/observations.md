# Empirical Evidence & Passive Technical Observations

This document records the empirical technical evidence collected during the passive architectural audit of **Cynbit Technologies** (`https://www.cynbit.in` and associated subdomains).

> **Testing Methodology & Compliance Note:**
> All testing was strictly **passive, authorized, non-intrusive, and read-only**. No brute-force attacks, fuzzing, denial-of-service, or automated vulnerability scanners were run against Cynbit infrastructure. Findings were derived through standard HTTP header inspection, TLS negotiation analysis, static bundle inspection, and React Server Components (RSC) wire protocol observation.

---

## 1. Target Infrastructure & Network Topology

| Attribute | Observed Target Value | Analysis & Implication |
| :--- | :--- | :--- |
| **Primary Domain** | `https://www.cynbit.in` (and `https://cynbit.in`) | Main public enterprise web application |
| **Associated Subdomain** | `https://bitelevate.cynbit.in` | BitElevate intern portal & learning dashboard |
| **Hosting & Edge Provider** | **Vercel Anycast CDN** (`server: Vercel`) | Serverless edge deployment, Next.js optimized |
| **Edge Server Node** | `bom1::*` (Mumbai, India) | Edge routing closest to the subcontinent |
| **Anycast IPv4 Addresses** | `64.29.17.1`, `216.198.79.1`, `64.29.17.65`, `216.198.79.65` | Managed Vercel Anycast edge network |
| **TLS Implementation** | TLS 1.3 / `TLS_AES_128_GCM_SHA256` / Let's Encrypt RSA 2048 | Modern TLS configuration with valid certificate chain |
| **Application Framework** | **Next.js 14/15 App Router** | React Server Components (RSC) + Server Actions |

---

## 2. HTTP Response Headers & Security Posture

### 2.1 Primary Domain Root (`https://www.cynbit.in/`)

```http
HTTP/2 200 OK
date: Fri, 30 Oct 2026 13:57:28 GMT
server: Vercel
content-type: text/html; charset=utf-8
content-length: 100498
access-control-allow-origin: *
cache-control: public, max-age=0, must-revalidate
strict-transport-security: max-age=63072000
vary: rsc, next-router-state-tree, next-router-prefetch, next-router-segment-prefetch
x-matched-path: /
x-nextjs-prerender: 1
x-nextjs-stale-time: 300
x-vercel-cache: HIT
x-vercel-id: bom1::nl49r-1793368648416-6c68c5c512a3
```

### 2.2 Security Header Gap Analysis

| Header | Observed Status | Risk / Security Exposure |
| :--- | :--- | :--- |
| `Access-Control-Allow-Origin` | **`*` (Wildcard)** | Permissive wildcard CORS on HTML responses allows arbitrary cross-origin script contexts to read response contents if authenticated fetch is misconfigured. |
| `Content-Security-Policy` (CSP) | **MISSING** | No restriction on script injection sources, frame ancestors, or unauthorized external asset loads. Facilitates Cross-Site Scripting (XSS). |
| `X-Frame-Options` | **MISSING** | The application can be embedded in an `<iframe>` by arbitrary external domains, creating an acute **Clickjacking** risk on forms and login screens. |
| `X-Content-Type-Options` | **MISSING** | Missing `nosniff` enables MIME-type confusion attacks in legacy and strict browser clients. |
| `Referrer-Policy` | **MISSING** | Browsers default to full URL leakage in cross-origin requests, potentially exposing internal routing tokens and tracking query parameters. |
| `Permissions-Policy` | **MISSING** | Browser features (camera, microphone, geolocation) are not explicitly restricted at the HTTP response level. |
| `Strict-Transport-Security` | `max-age=63072000` | **PRESENT (Compliant)**: Enforces TLS for 2 years across modern browsers. |

---

## 3. Discovered Server Action RPC Endpoints

In Next.js App Router, asynchronous server-side RPC functions called from client components are compiled with encrypted/hashed function identifiers (`createServerReference`). Through static bundle analysis of public client chunks, the following backend Server Actions were mapped:

| Action Identifier (Hash) | Function Name | Invocation Location | High-Level Backend Behavior |
| :--- | :--- | :--- | :--- |
| `40247ba4465344b3386595bab4303317cdcce907df` | `submitInquiry` | `app/(marketing)/contact/page-*.js` | Ingests business contact inquiries (`fullName`, `email`, `company`, `industry`, `message`). |
| `40645a00e04f6854903cf3a65fda4c75ddd7691de9` | `submitCandidateApplication` | `app/(marketing)/careers/[slug]/page-*.js` | Ingests job applicant PII (`fullName`, `email`, `phone`, `whatsapp`, `dob`, `gender`, `educationData`, `portfolioUrl`, `linkedinUrl`). Returns duplicate status & tracking URL. |
| `40450605530d78e25921058a0059197fdb18b5f074` | `createBitelevateCashfreeOrder` | `app/(marketing)/bitelevate/page-*.js` | Initiates checkout order with Cashfree payment gateway, returns `paymentSessionId`, `orderId`, and session `token`. |
| `60895028315fbe0e72db7e2a1871d236f08f860ce1` | `verifyBitelevatePayment` | `app/(marketing)/bitelevate/page-*.js` | Verifies Cashfree payment settlement. **Exposes plain-text credentials in response.** |
| `40d93da1cc26de4ef37bcb273184b7141ef77a50f8` | `loginToPortal` | `app/portal/page-*.js` | Single-field password/key authentication for `/portal`. |
| `60c644173c8290d140c74d8944fc29bd658873a282` | `loginIntern` | `app/intern-portal/login/page-*.js` | Intern authentication using `(email, password)`. |
| `408d222e7a54ae1d8dcd8b54a9aa53726d7348a7b0` | `requestPasswordReset` | `app/intern-portal/login/page-*.js` | Initiates password reset flow with differential status messaging. |

---

## 4. Deep-Dive Code Snippets from Public Bundles

### 4.1 Plaintext Credential Exposure on Payment Verification

From bundle `_next/static/chunks/app/(marketing)/bitelevate/page-e1cc18fdcf688572.js`:

```javascript
// Step 1: Client initiates Cashfree order via Server Action
let e = await m(t); // m = createBitelevateCashfreeOrder
if (!e.success || !e.orderId || !e.token) { ... }

// Step 2: Client loads Cashfree SDK and presents modal
let t = window.Cashfree({ mode: "production" === e.environment ? "production" : "sandbox" });
await t.checkout({ paymentSessionId: e.paymentSessionId, redirectTarget: "_modal" });

// Step 3: Client calls Server Action to verify payment
let a = await c(e.token, e.orderId); // c = verifyBitelevatePayment
if (a.success) {
    b(!0);
    // VULNERABILITY: Raw plaintext credentials received in JSON response
    a.bitElevateCredentials && y(a.bitElevateCredentials);
}
```

And in the UI presentation block:

```javascript
let a = "BitElevate Intern Portal Credentials\nLogin URL: https://cynbit.in/intern-portal/login\nUser ID: "
        .concat(g.email, "\nPassword: ").concat(g.password);
navigator.clipboard.writeText(a);
```

**Observation:** The backend server generates or fetches the candidate's account password and returns it in cleartext across the network JSON payload (`g.password`). This violates cryptographic security standards (passwords should be hashed using Argon2id/bcrypt and never returned to the client).

---

### 4.2 Insecure Session Storage & Shared Secret in `/portal`

From bundle `_next/static/chunks/app/portal/page-ba479285e84c64b5.js`:

```javascript
let l = (0, s.createServerReference)("40d93da1cc26de4ef37bcb273184b7141ef77a50f8", s.callServer, void 0, s.findSourceMapURL, "loginToPortal");

async function c(r) {
    r.preventDefault();
    let t = new FormData();
    t.append("password", e); // Only a single password field!
    let a = await l(t);
    if (a.success) {
        try {
            // VULNERABILITY: Activity timestamp stored in unencrypted client-side localStorage
            localStorage.setItem("cynbit_portal_last_activity", Date.now().toString());
        } catch (e) {}
        window.location.href = "/dashboard";
    } else {
        s(a.error || "Login failed");
    }
}
```

**Observation:**
1. Authentication relies on a single shared "Security Key" without multi-factor authentication (MFA) or distinct identity tracking.
2. Session validity relies on client-side `localStorage` rather than server-issued `HttpOnly`, `Secure`, `SameSite=Strict` cookies.

---

### 4.3 727KB Pre-rendered Intern Dashboard Exposure

Request to `https://bitelevate.cynbit.in/dashboard`:

```http
HTTP/2 200 OK
server: Vercel
x-matched-path: /intern-portal/dashboard
x-nextjs-prerender: 1
x-vercel-cache: PRERENDER
content-length: 14194
```

Loading bundle: `_next/static/chunks/app/intern-portal/dashboard/page-6430ee332a6a7642.js` (Size: **727,015 bytes**).

**Observation:**
- When an unauthenticated client sends a direct HTTP `GET` request to `https://bitelevate.cynbit.in/dashboard`, the Vercel CDN returns `HTTP 200 OK` from its static prerender cache (`x-vercel-cache: PRERENDER`).
- The 727KB JavaScript chunk contains the **entire proprietary curriculum**, internal engineering task specifications, deliverable requirements, and even hardcoded internal references (e.g. `fetch('http://localhost:8000/health')`, `backend/app/main.py`).
- No server-side authentication middleware intercepts this request to return an HTTP 302/307 redirect before serving the proprietary bundle.

---

### 4.4 User Enumeration via Differential Responses

1. **Career Application Submission (`submitCandidateApplication`):**
   ```javascript
   if (s.isDuplicate && s.trackingUrl) {
       // Returns: "You have already submitted an active application for this position.
       // Your profile is currently under review by our engineering team."
       // Accompanied by unique tracking portal URL!
   }
   ```
   *Impact:* An external party submitting an email address can immediately discover whether that specific individual has applied for a position at Cynbit.

2. **Intern Password Reset (`requestPasswordReset`):**
   ```javascript
   s.success ? C({ type: "success", text: s.message || "A password reset link has been dispatched to your email inbox." })
             : C({ type: "error", text: s.error || "Unable to send reset link. Please check your email address." });
   ```
   *Impact:* The backend returns distinct error messaging when an email is not present in the user database, allowing automated account enumeration scripts to harvest valid user emails.
