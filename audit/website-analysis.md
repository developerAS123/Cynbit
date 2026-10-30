# Website & Infrastructure Analysis

This report examines Cynbit's public website architecture, edge network topology, routing configuration, asset delivery mechanisms, and observable attack surfaces.

---

## 1. Network Topology & Edge CDN Architecture

Passive DNS resolution and HTTP/2 handshakes reveal that Cynbit operates on **Vercel's Anycast Edge Network**:

```
                       +---------------------------------------+
                       |           Client Request              |
                       +---------------------------------------+
                                           |
                                           v
                       +---------------------------------------+
                       |         Vercel Anycast Network        |
                       |  64.29.17.1 / 216.198.79.1 (Anycast)  |
                       +---------------------------------------+
                                           |
                                           v
                       +---------------------------------------+
                       |        Edge Pop: bom1 (Mumbai)        |
                       | TLS 1.3 / TLS_AES_128_GCM_SHA256      |
                       +---------------------------------------+
                                           |
                    +----------------------+----------------------+
                    |                                             |
                    v                                             v
     +------------------------------+              +------------------------------+
     | Static Edge Cache (S-S-R/SSG)|              |   Serverless Node.js Lambdas |
     | x-vercel-cache: HIT / PREREND|              |  Next.js Server Actions RPC  |
     +------------------------------+              +------------------------------+
```

### 1.1 IP & DNS Routing
- **Primary Domain (`cynbit.in`, `www.cynbit.in`):** Resolves to `64.29.17.1` and `216.198.79.1`.
- **Subdomain (`bitelevate.cynbit.in`):** Resolves to `64.29.17.65` and `216.198.79.65`.
- **Edge PoP (`x-vercel-id: bom1::*`):** Traffic terminates at the Mumbai edge point-of-presence, yielding low physical latency (<25ms RTT) for domestic visitors in India.
- **TLS Configuration:** Compliant Let's Encrypt RSA 2048 certificate, valid through late 2026 / early 2027, enforcing TLS 1.3 cipher negotiation with forward secrecy.

---

## 2. Frontend Framework & Rendering Strategies

Analysis of the DOM tree and response headers confirms the application is built on **Next.js (App Router)**:

1. **React Server Components (RSC):**  
   The HTTP responses include headers specific to Next.js App Router:
   ```http
   vary: rsc, next-router-state-tree, next-router-prefetch, next-router-segment-prefetch
   x-nextjs-prerender: 1
   x-nextjs-stale-time: 300
   ```
   Navigation between views leverages RSC flight streams (`?_rsc=1`), reducing payload transfer size for static view switches.

2. **Static Site Generation (SSG) & Incremental Static Regeneration (ISR):**  
   Marketing pages (e.g., `/`, `/story`, `/team`, `/services`, `/blog/*`) are pre-rendered into static HTML and cached across edge nodes (`x-vercel-cache: HIT`, `cache-control: public, max-age=0, must-revalidate`).

3. **Dynamic Client Component Islands:**  
   Interactive elements (the inquiry form on `/contact`, the application wizard on `/careers/[slug]`, and the checkout flow on `/bitelevate`) are hydrated via client-side JavaScript chunks loaded asynchronously.

---

## 3. Site Navigation Structure & robots.txt Evaluation

Inspection of `https://www.cynbit.in/robots.txt` exposed the following rules:

```robots
User-agent: *
Allow: /

# Sitemap Location
Sitemap: https://cynbit.in/sitemap.xml

# Crawl Delay
Crawl-delay: 1

# Disallow specific non-SEO pages
Disallow: /api/
Disallow: /admin/
Disallow: /portal/
```

### Backend Implications of robots.txt
- **Sensitive Route Disclosure:** Search engine robots directives explicitly highlight sensitive administrative routes (`/api/`, `/admin/`, `/portal/`).
- **Route Status Verification:**
  - `GET /admin`: Returns `HTTP 404 Not Found` (either unmapped or rewritten).
  - `GET /portal`: Returns `HTTP 200 OK` (renders active Cynbit Portal login).
  - `GET /intern-portal/dashboard`: Returns `HTTP 307 Temporary Redirect` to `https://bitelevate.cynbit.in/dashboard`.
  - `GET https://bitelevate.cynbit.in/dashboard`: Returns `HTTP 200 OK` (pre-rendered intern dashboard).

---

## 4. Attack Surface Identification

Through route enumeration and bundle mapping, five distinct user-facing transaction surfaces were cataloged:

| Surface / Flow | URL Route | Backend Interaction Type | Data Ingested |
| :--- | :--- | :--- | :--- |
| **Lead Generation** | `/contact` | Server Action (`submitInquiry`) | Full Name, Corporate Email, Company, Industry, Message |
| **Job Applicant Portal** | `/careers/[slug]` | Server Action (`submitCandidateApplication`) | Sensitive PII, Phone, WhatsApp, DoB, Residential Address, Academic Records, URLs |
| **Internship Enrollment** | `/bitelevate` | Server Action (`createBitelevateCashfreeOrder`) | Applicant Name, College, Email, Phone, Payment Transaction ID |
| **Payment Verification** | `/bitelevate` | Server Action (`verifyBitelevatePayment`) | Cashfree Session Token, Order ID (returns plaintext credentials) |
| **Admin Portal Auth** | `/portal` | Server Action (`loginToPortal`) | Master Security Key (single secret) |
| **Intern Portal Auth** | `/intern-portal/login` | Server Action (`loginIntern`) | User Email + Password |

Each of these entry points represents an architectural dependency that must be reinforced with robust input validation, rate limiting, and centralized auditing.
