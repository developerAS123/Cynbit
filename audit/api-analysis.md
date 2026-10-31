# Observable API & RPC Analysis

This report analyzes Cynbit's backend communication mechanisms, wire protocol behaviors, payload structures, and data handling procedures.

---

## 1. Next.js Server Actions Wire Protocol

Unlike traditional RESTful architectures exposing versioned endpoints (e.g., `/api/v1/inquiries`), Cynbit implements **Next.js Server Actions RPC**.

### 1.1 Request Wire Mechanics
When a user interacts with a form, the browser issues an asynchronous HTTP `POST` request to the current page path, embedding an internal action reference header:

```http
POST /contact HTTP/2
Host: www.cynbit.in
Next-Action: 40247ba4465344b3386595bab4303317cdcce907df
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...

------WebKitFormBoundary...
Content-Disposition: form-data; name="1_$ACTION_ID_40247ba4465344b3386595bab4303317cdcce907df"

------WebKitFormBoundary...
Content-Disposition: form-data; name="fullName"

Alex Rivera
------WebKitFormBoundary...
Content-Disposition: form-data; name="email"

alex@example.com
------WebKitFormBoundary...
```

### 1.2 Response Wire Mechanics
The serverless function computes the result and streams a serialized React Server Component flight response (`content-type: text/x-component`):

```http
HTTP/2 200 OK
content-type: text/x-component
vary: RSC, Next-Router-State-Tree, Next-Router-Prefetch

0:{"success":true}
```

---

## 2. In-Depth Analysis of Individual Endpoints

### 2.1 Lead Ingestion: `submitInquiry` (`40247ba4...`)
- **Input Payload:** `fullName`, `email`, `company`, `industry`, `message`.
- **Validation Gaps:**
  - Client-side checks use standard HTML5 attributes (`required`, `type="email"`).
  - No observable payload size restrictions (large string payloads in `message` can cause memory exhaustion on serverless lambdas).
  - Lack of bot prevention (no CAPTCHA, Turnstile, or honeypot fields).

### 2.2 Career Application Ingestion: `submitCandidateApplication` (`40645a00...`)
- **Input Payload:**
  - Identifiers: `fullName`, `email`, `phone`, `whatsapp`, `dob`, `gender`
  - Academic Profile: `educationData` (JSON string serialized on the client containing `qualificationLevel`, `degree`, `customDegree`, `specialization`, `university`, `graduationYear`, `gradeType`, `gradeValue`)
  - Operational details: `noticePeriod`, `skills`, `currentCity`, `permanentAddress`
  - Portfolio/Links: `portfolioUrl`, `linkedinUrl`, `professionalProfileUrl`
  - Statement: `message`
- **Architectural Observations:**
  - **Client-Side JSON Stringification:** The client manually constructs and stringifies `educationData`:
    ```javascript
    r.append("educationData", JSON.stringify(y));
    ```
    If the backend parses this with a raw `JSON.parse()` without strict schema validation, malformed payloads can trigger unhandled runtime exceptions.
  - **Duplicate Detection Leak:** When an email matches an existing record, the server returns `{ isDuplicate: true, trackingUrl: "/portal/track/..." }`. This directly exposes applicant identity and hiring status to any party who enters an applicant's email.

### 2.3 Payment Gateway Ingestion: `createBitelevateCashfreeOrder` (`404506...`)
- **Gateway Integration:** Integrates with **Cashfree Payments India**.
- **Request Parameters:** Customer name, email, phone number, program track.
- **Response Structure:** `{ success: boolean, orderId: string, token: string, paymentSessionId: string, environment: "production" | "sandbox" }`.
- **Architectural Vulnerability:**
  - The client invokes Cashfree SDK modal checkout directly in the browser:
    ```javascript
    let t = window.Cashfree({ mode: "production" === e.environment ? "production" : "sandbox" });
    await t.checkout({ paymentSessionId: e.paymentSessionId, redirectTarget: "_modal" });
    ```
  - If a bot floods `createBitelevateCashfreeOrder` without completing checkout, it creates thousands of orphaned orders on Cashfree, potentially exhausting merchant gateway quotas or incurring operational fees.

### 2.4 Payment Settlement & Verification: `verifyBitelevatePayment` (`608950...`)
- **Parameters Received:** `(token, orderId)`.
- **Observed Response Structure:**
  ```json
  {
    "success": true,
    "orderStatus": "PAID",
    "bitElevateCredentials": {
      "email": "candidate@domain.com",
      "password": "GENERATED_PLAINTEXT_PASSWORD"
    }
  }
  ```
- **Architectural Breakdown:**
  - Returning credentials over the network to a client-side JavaScript callback violates core principles of zero-trust backend architecture.
  - In a standard secure architecture, account creation must be decoupled: the backend issues a **cryptographically signed, time-limited magic setup token** sent exclusively to the user's verified email address, prompting them to set their own salted/hashed password over TLS.

---

## 3. Comparative Evaluation: Server Actions vs. Dedicated FastAPI Backend

| Architectural Dimension | Cynbit Current (Next.js Server Actions) | Proposed (FastAPI Microservice Backend) |
| :--- | :--- | :--- |
| **Protocol Standards** | Proprietary Next.js flight RPC (`text/x-component`) | Standard OpenAPI 3.1 / JSON REST endpoints |
| **Client Interoperability**| Locked exclusively to Next.js client frontend | Usable by web, iOS, Android, and internal CLI tools |
| **Payload Validation** | Ad-hoc JavaScript validation in server action files | Declarative Pydantic v2 schemas with automated rejection |
| **Rate Limiting** | Difficult to coordinate across stateless Vercel lambdas | Centralized Redis Token Bucket / Sliding Window middleware |
| **Performance Overhead** | Serverless cold starts (300ms - 1500ms on Node.js) | Sub-millisecond ASGI async event loop (`uvicorn`) |
| **Security Surface** | Large JS bundles exposing hashes and action references | Minimized attack surface; strict HTTP security headers & CORS |
| **Developer Ergonomics** | Fast initial prototype, slow enterprise refactor | Clear domain separation, testable services, automatic docs (`/docs`) |

Migrating transaction-critical business logic to a dedicated FastAPI backend delivers transparent API governance, automated Swagger/OpenAPI documentation, and robust defense-in-depth.

