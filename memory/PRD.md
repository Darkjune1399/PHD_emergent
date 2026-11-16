# PHD - Psychological Health Detector (imported repo, continued)

## Stack
- Next.js 15 (App Router) single-page app in `app/page.js` (+ shadcn UI in `components/ui`)
- Backend: single catch-all API `app/api/[[...path]]/route.js` (MongoDB native driver, UUID ids)
- Auth: username + password (pbkdf2), HMAC-signed bearer token (JWT_SECRET)
- Region data: `lib/regions.js` (Kab. Jember & Banyuwangi: kota -> kecamatan -> kelurahan)

## Implemented features
- Public landing page + articles (CMS with WYSIWYG editor, image upload stored in Mongo base64)
- User: register (with kota/kecamatan/kelurahan/alamat), login, forgot/reset password (MOCKED - token shown on screen)
- Family multi-profile members; age-based instrument routing (SDQ parent 4-10, SDQ self 11-18, PHQ-9 + GHQ-12 >18)
- Automatic scoring, recommendations, red-flag alerts, history, PDF print, emergency referrals dialog, feedback
- Admin panel: dashboard stats (trend range, region comparison), red flag alerts, master questionnaire, age rules,
  user management, regional admins (admin_pa per kota, admin_kua per kecamatan, admin_mudin per kelurahan) with data scoping,
  referrals, feedback, articles, audit logs

## Session log
- Imported from GitHub: recreated missing `.env` (MONGO_URL, DB_NAME, NEXT_PUBLIC_BASE_URL, CORS_ORIGINS, JWT_SECRET), installed deps with yarn, app running.
- Known pre-existing issue: cold-start race in `connectToMongo()` (concurrent first requests -> 500 "Cannot read properties of undefined (reading 'collection')").

- Fixed cold-start race (promise-based connectToMongo + single seed run); removed duplicated seed docs (instruments, articles) in fresh DB.
- NEW: Admin tab "Semua Hasil Asesmen" (all admins, region-scoped): list per assessment + per family account view + detail dialog
  (relationship assessed person <-> account holder, family members, history, answers). Endpoints: GET /admin/assessments,
  GET /admin/assessments/:id, GET /admin/assessment-accounts. Backend 81/81 tests passed.
- Fixed: frontend ADMIN_ROLES missing admin_mudin (mudin admins now see admin panel).

## Backlog
- P1: Export CSV/Excel of all results (filtered)
- P1: Date range filter on results page
- P2: Real password reset delivery (currently MOCKED, token shown on screen)
- P2: GET /admin/alerts/:id has no region scope check (pre-existing)
