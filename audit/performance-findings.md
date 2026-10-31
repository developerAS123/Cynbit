# Performance & Scalability Findings

This report evaluates the observed runtime performance, edge latency, payload efficiency, and backend scalability characteristics of Cynbit's systems.

---

## 1. Edge Delivery & Latency Characteristics

Through active edge timing inspections across Mumbai edge nodes (`bom1`), baseline round-trip metrics were established:

| Request Target | Observed HTTP Status | Edge Cache Header | Time to First Byte (TTFB) | Payload Size |
| :--- | :--- | :--- | :--- | :--- |
| `GET /` (Homepage) | 200 OK | `x-vercel-cache: HIT` | ~45ms | 100.5 KB (HTML) |
| `GET /bitelevate` | 200 OK | `x-vercel-cache: HIT` | ~48ms | 114.2 KB (HTML) |
| `GET /portal` | 200 OK | `x-vercel-cache: HIT` | ~52ms | 12.9 KB (HTML) |
| `GET /intern-portal/dashboard` | 200 OK (Subdomain) | `x-vercel-cache: PRERENDER` | ~60ms | 14.2 KB HTML + **727 KB JS Chunk** |

### 1.1 Edge Caching Efficiency
Static pages benefit from Vercel's global CDN edge caching. Cache hit ratios on public marketing pages are optimal, resulting in low TTFB for repeat domestic requests.

However, the cache-control directive on HTML:
```http
cache-control: public, max-age=0, must-revalidate
```
forces clients to re-validate conditional headers (`ETag`) on every request, adding an unnecessary 30–50ms round-trip latency when a modest `stale-while-revalidate` header could serve responses immediately.

---

## 2. Bundle Bloat & Client Hydration Overhead

The most significant performance bottleneck identified is the client-side bundle size on the learning platform dashboard:

```
+-------------------------------------------------------------------------+
|                  INTERN DASHBOARD JS BUNDLE ANALYSIS                    |
+-------------------------------------------------------------------------+
| Target Chunk: page-6430ee332a6a7642.js                                  |
| Raw Uncompressed Size: 727,015 bytes (~710 KB)                          |
| Gzipped Transfer Size: ~182 KB                                          |
| JavaScript Execution Time (Mid-Tier Mobile CPU): ~450ms - 900ms         |
+-------------------------------------------------------------------------+
```

### 2.1 Why This Hurts Real Users:
1. **Total Blocking Time (TBT) & Interaction to Next Paint (INP):**  
   Shipping 710 KB of monolithic JavaScript forces the browser's main thread to compile, parse, and execute massive object trees before the page becomes responsive. Users on low-end devices or college Wi-Fi experience noticeable UI freezes.
2. **Missing Code Splitting:**  
   The entire curriculum—including exercises for Frontend, Backend, Fullstack, AI, and DevOps tracks—is bundled into a single chunk rather than lazily loaded on demand based on the candidate's active track.

---

## 3. Serverless Lambda Latency vs. Persistent Async Daemon

Under the current architecture, all Server Actions execute as stateless Node.js serverless functions on Vercel:

```
[ Traditional Serverless Node.js (Current) ]
Cold Start (Container Init + Node runtime + DB handshake): 600ms - 1500ms
Connection Pooling: Difficult; risk of exhausting DB connections during traffic surges.

VS.

[ Persistent ASGI FastAPI Daemon (Proposed) ]
Event Loop Ready TTFB: 2ms - 8ms (Async non-blocking I/O)
Connection Pooling: Managed SQLAlchemy 2.0 asyncpg pool (pre-warmed connections).
```

### 3.1 Cold Starts on Transactional Routes
When an applicant clicks "Submit Application Blueprint" or initiates payment after several minutes of inactivity, the underlying serverless container is likely cold. Cold execution overhead introduces a **700ms–1800ms delay** before the payment gateway session or database insertion completes.

### 3.2 Database Connection Flooding
Serverless lambdas scale out horizontally by spinning up isolated containers. During a campus recruitment drive or marketing campaign, hundreds of concurrent submissions instantiate hundreds of serverless instances, each opening separate database connections. Without a persistent connection pooler (such as PgBouncer or FastAPI's internal SQLAlchemy pool), PostgreSQL connection limits are quickly exhausted.

---

## 4. Benchmark & Performance Recommendations

| Bottleneck | Current Performance Impact | Proposed Architecture Solution | Expected Latency Reduction |
| :--- | :--- | :--- | :--- |
| **Monolithic Dashboard Bundle** | 727 KB JS parsed on main thread; high TBT | Route-level code splitting & dynamic React lazy loading | **-75% bundle transfer size** (<180 KB) |
| **Server Action Cold Starts** | 700ms–1500ms latency spikes on form submissions | FastAPI async daemon with pre-forked workers (`uvicorn`) | **-90% request latency** (<35ms TTFB) |
| **Client Revalidation Overhead** | Conditional ETag roundtrip on every page load | CDN header: `stale-while-revalidate=86400, max-age=3600` | **-50ms TTFB for cached visitors** |
| **Database Handshake Cost** | New TCP/TLS connection created per serverless run | Async connection pooling with `pool_size=20, max_overflow=10` | **Zero connection setup overhead** on hot paths |

