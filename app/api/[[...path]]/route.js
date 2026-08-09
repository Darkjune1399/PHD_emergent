import { MongoClient } from 'mongodb'
import { v4 as uuidv4 } from 'uuid'
import { NextResponse } from 'next/server'
import crypto from 'crypto'

// ================= MongoDB connection =================
let client
let db
async function connectToMongo() {
  if (!client) {
    client = new MongoClient(process.env.MONGO_URL)
    await client.connect()
    db = client.db(process.env.DB_NAME)
  }
  return db
}

// ================= CORS =================
function handleCORS(response) {
  response.headers.set('Access-Control-Allow-Origin', process.env.CORS_ORIGINS || '*')
  response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH')
  response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  response.headers.set('Access-Control-Allow-Credentials', 'true')
  return response
}
export async function OPTIONS() {
  return handleCORS(new NextResponse(null, { status: 200 }))
}

const JWT_SECRET = process.env.JWT_SECRET || 'psikologi-asesmen-secret-2025'

// ================= Auth helpers (no external libs) =================
function hashPassword(pw) {
  const salt = crypto.randomBytes(16).toString('hex')
  const hash = crypto.pbkdf2Sync(pw, salt, 100000, 64, 'sha512').toString('hex')
  return `${salt}:${hash}`
}
function verifyPassword(pw, stored) {
  if (!stored || !stored.includes(':')) return false
  const [salt, hash] = stored.split(':')
  const h = crypto.pbkdf2Sync(pw, salt, 100000, 64, 'sha512').toString('hex')
  try { return crypto.timingSafeEqual(Buffer.from(h), Buffer.from(hash)) } catch (e) { return false }
}
function signToken(payload) {
  const body = { ...payload, exp: Date.now() + 7 * 24 * 60 * 60 * 1000 }
  const data = Buffer.from(JSON.stringify(body)).toString('base64url')
  const sig = crypto.createHmac('sha256', JWT_SECRET).update(data).digest('base64url')
  return `${data}.${sig}`
}
function verifyToken(token) {
  try {
    const [data, sig] = token.split('.')
    const expected = crypto.createHmac('sha256', JWT_SECRET).update(data).digest('base64url')
    if (sig !== expected) return null
    const payload = JSON.parse(Buffer.from(data, 'base64url').toString())
    if (payload.exp && Date.now() > payload.exp) return null
    return payload
  } catch (e) { return null }
}
async function getUserFromRequest(request, db) {
  const auth = request.headers.get('authorization') || ''
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : null
  if (!token) return null
  const payload = verifyToken(token)
  if (!payload) return null
  const user = await db.collection('users').findOne({ id: payload.id })
  if (!user) return null
  const { _id, passwordHash, ...safe } = user
  return safe
}

function calcAge(dob) {
  const b = new Date(dob)
  const now = new Date()
  let age = now.getFullYear() - b.getFullYear()
  const m = now.getMonth() - b.getMonth()
  if (m < 0 || (m === 0 && now.getDate() < b.getDate())) age--
  return age
}

// ================= INSTRUMENT DEFINITIONS =================
const SDQ_OPTIONS = [
  { label: 'Tidak Benar', value: 0 },
  { label: 'Agak Benar', value: 1 },
  { label: 'Benar', value: 2 },
]
const GHQ_OPTIONS = [
  { label: 'Lebih baik dari biasanya', value: 0 },
  { label: 'Sama seperti biasanya', value: 1 },
  { label: 'Kurang dari biasanya', value: 2 },
  { label: 'Jauh berkurang dari biasanya', value: 3 },
]
const PHQ_OPTIONS = [
  { label: 'Tidak Pernah', value: 0 },
  { label: 'Beberapa hari', value: 1 },
  { label: 'Lebih dari separuh waktu', value: 2 },
  { label: 'Hampir setiap hari', value: 3 },
]

const SDQ_ITEMS = [
  { id: 1, sub: 'Pr', rev: false, parent: 'Peka terhadap perasaan orang lain', self: 'Saya berusaha bersikap baik kepada orang lain, saya peduli dengan perasaan mereka' },
  { id: 2, sub: 'H', rev: false, parent: 'Gelisah, terlalu aktif, tidak dapat diam untuk waktu lama', self: 'Saya gelisah, saya tidak dapat diam untuk waktu lama' },
  { id: 3, sub: 'E', rev: false, parent: 'Sering mengeluh sakit kepala, sakit perut atau mual', self: 'Saya sering merasa sakit kepala, sakit perut atau mual' },
  { id: 4, sub: 'Pr', rev: false, parent: 'Kalau memiliki mainan/makanan/pensil, biasanya mau berbagi dengan anak lain', self: 'Saya biasanya berbagi dengan orang lain (makanan, permainan, pulpen, dll)' },
  { id: 5, sub: 'C', rev: false, parent: 'Sering marah meledak-ledak atau mudah hilang kesabaran', self: 'Saya menjadi sangat marah dan sering tidak dapat mengendalikan kemarahan saya' },
  { id: 6, sub: 'P', rev: false, parent: 'Cenderung menyendiri, lebih suka bermain sendiri', self: 'Saya lebih suka menyendiri daripada bersama orang seusia saya' },
  { id: 7, sub: 'C', rev: true, parent: 'Umumnya bertingkah laku baik, melakukan apa yang disuruh orang dewasa', self: 'Saya biasanya melakukan apa yang diperintahkan' },
  { id: 8, sub: 'E', rev: false, parent: 'Banyak kekhawatiran atau sering tampak khawatir', self: 'Saya banyak merasa cemas atau khawatir' },
  { id: 9, sub: 'Pr', rev: false, parent: 'Suka menolong jika seseorang terluka, kecewa atau merasa sakit', self: 'Saya selalu siap menolong jika ada orang yang terluka, kecewa atau merasa sakit' },
  { id: 10, sub: 'H', rev: false, parent: 'Terus bergerak dengan resah atau menggeliat-geliat', self: 'Saya terus menerus gelisah atau menggeliat' },
  { id: 11, sub: 'P', rev: true, parent: 'Mempunyai paling sedikit satu orang teman baik', self: 'Saya mempunyai satu atau lebih teman baik' },
  { id: 12, sub: 'C', rev: false, parent: 'Sering berkelahi dengan anak lain atau mengintimidasi mereka', self: 'Saya sering bertengkar dengan orang lain, saya dapat memaksa orang lain melakukan keinginan saya' },
  { id: 13, sub: 'E', rev: false, parent: 'Sering merasa tidak bahagia, sedih atau menangis', self: 'Saya sering merasa tidak bahagia, sedih atau menangis' },
  { id: 14, sub: 'P', rev: true, parent: 'Pada umumnya disukai oleh anak-anak lain', self: 'Orang lain seusia saya pada umumnya menyukai saya' },
  { id: 15, sub: 'H', rev: false, parent: 'Mudah teralih perhatiannya, sulit memusatkan perhatian', self: 'Perhatian saya mudah teralih, saya sulit memusatkan perhatian' },
  { id: 16, sub: 'E', rev: false, parent: 'Gugup di situasi baru, mudah kehilangan rasa percaya diri', self: 'Saya merasa gugup dalam situasi baru, saya mudah kehilangan rasa percaya diri' },
  { id: 17, sub: 'Pr', rev: false, parent: 'Bersikap baik terhadap anak-anak yang lebih muda', self: 'Saya bersikap baik pada anak-anak yang lebih muda' },
  { id: 18, sub: 'C', rev: false, parent: 'Sering berbohong atau berbuat curang', self: 'Saya sering dituduh berbohong atau berbuat curang' },
  { id: 19, sub: 'P', rev: false, parent: 'Diganggu, digertak atau diintimidasi oleh anak lain', self: 'Saya diganggu atau dipermainkan oleh orang lain seusia saya' },
  { id: 20, sub: 'Pr', rev: false, parent: 'Sering menawarkan diri membantu orang lain (orang tua, guru, anak lain)', self: 'Saya sering menawarkan diri membantu orang lain (orang tua, guru, anak-anak)' },
  { id: 21, sub: 'H', rev: true, parent: 'Dapat berpikir/mempertimbangkan sebelum bertindak', self: 'Saya berpikir terlebih dahulu tentang akibatnya sebelum berbuat sesuatu' },
  { id: 22, sub: 'C', rev: false, parent: 'Mencuri dari rumah, sekolah atau tempat lain', self: 'Saya mengambil barang yang bukan milik saya dari rumah, sekolah atau tempat lain' },
  { id: 23, sub: 'P', rev: false, parent: 'Lebih mudah berhubungan dengan orang dewasa daripada dengan anak lain', self: 'Saya lebih mudah berhubungan dengan orang dewasa daripada dengan orang seusia saya' },
  { id: 24, sub: 'E', rev: false, parent: 'Banyak yang ditakuti, mudah menjadi takut', self: 'Saya banyak merasa takut, saya mudah menjadi takut' },
  { id: 25, sub: 'H', rev: true, parent: 'Memiliki perhatian yang baik, mampu menyelesaikan tugas hingga selesai', self: 'Saya menyelesaikan pekerjaan yang sedang saya lakukan, saya punya perhatian yang baik' },
]

const GHQ_ITEMS = [
  { id: 1, sub: 'S', text: 'Mampu memusatkan perhatian terhadap apa yang Anda kerjakan?' },
  { id: 2, sub: 'D', text: 'Kehilangan banyak waktu tidur karena rasa cemas/khawatir?' },
  { id: 3, sub: 'S', text: 'Merasa berperan dalam berbagai kegiatan?' },
  { id: 4, sub: 'S', text: 'Merasa mampu mengambil keputusan terhadap berbagai hal?' },
  { id: 5, sub: 'D', text: 'Merasa selalu berada di bawah tekanan?' },
  { id: 6, sub: 'D', text: 'Merasa tidak dapat mengatasi kesulitan/masalah?' },
  { id: 7, sub: 'S', text: 'Mampu menikmati kegiatan sehari-hari?' },
  { id: 8, sub: 'S', text: 'Mampu menghadapi masalah yang Anda alami?' },
  { id: 9, sub: 'D', text: 'Merasa tidak bahagia dan tertekan/depresi?' },
  { id: 10, sub: 'D', text: 'Kehilangan kepercayaan diri?' },
  { id: 11, sub: 'D', text: 'Berpikir bahwa diri Anda tidak berharga/berguna?' },
  { id: 12, sub: 'S', text: 'Merasa cukup bahagia dengan keadaan sekarang?' },
]

const PHQ_ITEMS = [
  { id: 1, text: 'Kurang berminat atau bergairah dalam melakukan apapun' },
  { id: 2, text: 'Merasa murung, sedih, atau putus asa' },
  { id: 3, text: 'Sulit tidur/mudah terbangun, atau terlalu banyak tidur' },
  { id: 4, text: 'Merasa lelah atau kurang bertenaga' },
  { id: 5, text: 'Kurang nafsu makan atau terlalu banyak makan' },
  { id: 6, text: 'Kurang percaya diri, merasa gagal atau mengecewakan diri/keluarga' },
  { id: 7, text: 'Sulit berkonsentrasi (mis. membaca koran atau menonton TV)' },
  { id: 8, text: 'Bergerak/berbicara sangat lambat sehingga diperhatikan orang lain; atau sebaliknya resah/gelisah sehingga lebih sering bergerak dari biasanya' },
  { id: 9, text: 'Merasa lebih baik mati atau ingin melukai diri sendiri dengan cara apapun' },
]

const SUB_NAMES = {
  E: 'Gejala Emosional', C: 'Masalah Perilaku', H: 'Hiperaktivitas/Inatensi',
  P: 'Masalah Teman Sebaya', Pr: 'Perilaku Prososial',
}

function instrumentsForAge(age) {
  if (age >= 4 && age <= 10) return [{ code: 'sdq_parent', name: 'SDQ - Laporan Orang Tua/Guru' }]
  if (age >= 11 && age <= 18) return [{ code: 'sdq_self', name: 'SDQ - Laporan Diri (Remaja)' }]
  if (age > 18) return [
    { code: 'phq9', name: 'PHQ-9 (Skrining Depresi)' },
    { code: 'ghq12', name: 'GHQ-12 (Kesehatan Mental Umum)' },
  ]
  return []
}

function getQuestionnaire(code) {
  if (code === 'sdq_parent' || code === 'sdq_self') {
    const variant = code === 'sdq_parent' ? 'parent' : 'self'
    return {
      code, family: 'sdq',
      name: code === 'sdq_parent' ? 'SDQ - Laporan Orang Tua/Guru' : 'SDQ - Laporan Diri (Remaja)',
      instruction: 'Untuk setiap pernyataan, pilih jawaban yang paling menggambarkan kondisi dalam 6 bulan terakhir.',
      options: SDQ_OPTIONS,
      items: SDQ_ITEMS.map(i => ({ id: i.id, text: i[variant] })),
    }
  }
  if (code === 'ghq12') {
    return {
      code, family: 'ghq12', name: 'GHQ-12 (Kesehatan Mental Umum)',
      instruction: 'Bagaimana kondisi Anda akhir-akhir ini? Pilih jawaban yang paling sesuai.',
      options: GHQ_OPTIONS, items: GHQ_ITEMS.map(i => ({ id: i.id, text: i.text })),
    }
  }
  if (code === 'phq9') {
    return {
      code, family: 'phq9', name: 'PHQ-9 (Skrining Depresi)',
      instruction: 'Selama 2 minggu terakhir, seberapa sering Anda terganggu oleh masalah berikut?',
      options: PHQ_OPTIONS, items: PHQ_ITEMS.map(i => ({ id: i.id, text: i.text })),
    }
  }
  return null
}

// ================= SCORING =================
const SDQ_CUT = {
  child: { E: [3, 4], C: [2, 3], H: [5, 6], P: [3, 4], total: [13, 15] },
  teen: { E: [5, 6], C: [3, 4], H: [5, 6], P: [3, 5], total: [15, 19] },
}
function catScale(score, normalMax, ambangMax) {
  if (score <= normalMax) return 'Normal'
  if (score <= ambangMax) return 'Ambang'
  return 'Abnormal'
}
function catProsocial(score) {
  if (score >= 6) return 'Normal'
  if (score === 5) return 'Ambang'
  return 'Abnormal'
}

function scoreSDQ(answers, age, variant) {
  const subs = { E: 0, C: 0, H: 0, P: 0, Pr: 0 }
  for (const item of SDQ_ITEMS) {
    const v = Number(answers[item.id] ?? 0)
    const s = item.rev ? (2 - v) : v
    subs[item.sub] += s
  }
  const total = subs.E + subs.C + subs.H + subs.P
  const band = age < 11 ? 'child' : 'teen'
  const cut = SDQ_CUT[band]
  const categories = {
    E: catScale(subs.E, cut.E[0], cut.E[1]),
    C: catScale(subs.C, cut.C[0], cut.C[1]),
    H: catScale(subs.H, cut.H[0], cut.H[1]),
    P: catScale(subs.P, cut.P[0], cut.P[1]),
    Pr: catProsocial(subs.Pr),
  }
  const totalCategory = catScale(total, cut.total[0], cut.total[1])
  const redFlag = totalCategory === 'Abnormal' || ['E', 'C', 'H', 'P'].some(k => categories[k] === 'Abnormal')

  const recs = []
  if (totalCategory === 'Normal') recs.push('Secara umum kondisi berada dalam batas normal. Pertahankan komunikasi hangat dan pola pengasuhan yang positif.')
  else if (totalCategory === 'Ambang') recs.push('Total Skor Kesulitan berada pada kategori AMBANG (borderline). Disarankan pemantauan lebih lanjut dan mempertimbangkan konsultasi dengan psikolog/konselor sekolah.')
  else recs.push('Total Skor Kesulitan berada pada kategori ABNORMAL. Sangat disarankan untuk berkonsultasi dengan psikolog atau tenaga kesehatan jiwa profesional.')
  const flagged = ['E', 'C', 'H', 'P', 'Pr'].filter(k => categories[k] !== 'Normal')
  if (flagged.length) recs.push('Aspek yang perlu perhatian: ' + flagged.map(k => `${SUB_NAMES[k]} (${categories[k]})`).join(', ') + '.')

  const subDetail = ['E', 'C', 'H', 'P', 'Pr'].map(k => ({ key: k, name: SUB_NAMES[k], score: subs[k], category: categories[k] }))

  return {
    family: 'sdq', band, variant, subscales: subs, categories, subDetail,
    totalDifficulties: total, totalCategory, overallCategory: totalCategory,
    trendScore: total, trendMax: 40, trendLabel: 'Total Kesulitan',
    redFlag, suicideRisk: false, recommendations: recs,
  }
}

function scorePHQ(answers) {
  let total = 0
  for (let i = 1; i <= 9; i++) total += Number(answers[i] ?? 0)
  const item9 = Number(answers[9] ?? 0)
  let severity = 'Minimal'
  if (total >= 20) severity = 'Berat'
  else if (total >= 15) severity = 'Sedang-Berat'
  else if (total >= 10) severity = 'Sedang'
  else if (total >= 5) severity = 'Ringan'
  const suicideRisk = item9 > 0
  const redFlag = suicideRisk || total >= 20
  const recMap = {
    'Minimal': 'Gejala depresi minimal/tidak ada. Pertahankan gaya hidup sehat, tidur cukup, dan aktivitas fisik teratur.',
    'Ringan': 'Depresi ringan. Disarankan self-care & pemantauan; pertimbangkan konsultasi bila gejala menetap lebih dari 2 minggu.',
    'Sedang': 'Depresi sedang. Disarankan berkonsultasi dengan psikolog/dokter untuk penanganan lebih lanjut.',
    'Sedang-Berat': 'Depresi sedang-berat. Sangat disarankan segera berkonsultasi dengan profesional kesehatan jiwa.',
    'Berat': 'Depresi berat. Diperlukan penanganan profesional segera.',
  }
  const recs = [recMap[severity]]
  if (suicideRisk) recs.unshift('PERHATIAN: Terdapat laporan pikiran untuk lebih baik mati atau menyakiti diri sendiri. Segera hubungi kontak darurat/profesional. Hotline SEJIWA / Kemenkes: 119 ext 8.')
  return {
    family: 'phq9', total, item9, severity, overallCategory: severity,
    trendScore: total, trendMax: 27, trendLabel: 'Skor PHQ-9',
    redFlag, suicideRisk, recommendations: recs,
  }
}

function scoreGHQ(answers) {
  let total = 0, distress = 0, dysfunction = 0
  for (const item of GHQ_ITEMS) {
    const v = Number(answers[item.id] ?? 0)
    total += v
    if (item.sub === 'D') distress += v
    else dysfunction += v
  }
  const problem = total >= 18
  const overallCategory = problem ? 'Indikasi Masalah Psikologis' : 'Normal'
  const recs = problem
    ? ['Skor total >= 18 mengindikasikan adanya distres psikologis. Disarankan menerapkan teknik manajemen stres dan berkonsultasi dengan tenaga profesional.']
    : ['Skor total < 18. Tidak ditemukan indikasi masalah psikopatologis yang signifikan. Tetap jaga kesehatan mental Anda.']
  return {
    family: 'ghq12', total, distress, dysfunction, overallCategory,
    trendScore: total, trendMax: 36, trendLabel: 'Skor GHQ-12',
    redFlag: problem, suicideRisk: false, recommendations: recs,
  }
}

function alertTypeFor(result) {
  if (result.suicideRisk) return { type: 'Ide Bunuh Diri / Melukai Diri', severity: 'Kritis' }
  if (result.family === 'phq9' && result.total >= 20) return { type: 'Depresi Berat (PHQ-9)', severity: 'Tinggi' }
  if (result.family === 'sdq') return { type: 'SDQ Abnormal', severity: 'Tinggi' }
  if (result.family === 'ghq12') return { type: 'Distres Psikologis (GHQ-12)', severity: 'Sedang' }
  return { type: 'Risiko Tinggi', severity: 'Tinggi' }
}

// ================= ROUTER =================
async function handleRoute(request, { params }) {
  const { path = [] } = await params
  const route = `/${path.join('/')}`
  const method = request.method

  try {
    const db = await connectToMongo()

    if (route === '/' && method === 'GET') {
      return handleCORS(NextResponse.json({ message: 'Sistem Asesmen Kesehatan Psikologis - API aktif' }))
    }

    // ---------- AUTH ----------
    if (route === '/auth/register' && method === 'POST') {
      const body = await request.json()
      const { name, email, password } = body
      if (!name || !email || !password) return handleCORS(NextResponse.json({ error: 'Nama, email, dan password wajib diisi' }, { status: 400 }))
      const existing = await db.collection('users').findOne({ email: email.toLowerCase() })
      if (existing) return handleCORS(NextResponse.json({ error: 'Email sudah terdaftar' }, { status: 400 }))
      const user = { id: uuidv4(), name, email: email.toLowerCase(), passwordHash: hashPassword(password), role: 'user', status: 'active', createdAt: new Date() }
      await db.collection('users').insertOne(user)
      const token = signToken({ id: user.id, role: user.role })
      return handleCORS(NextResponse.json({ token, user: { id: user.id, name: user.name, email: user.email, role: user.role } }))
    }

    if (route === '/auth/login' && method === 'POST') {
      const body = await request.json()
      const { email, password } = body
      const user = await db.collection('users').findOne({ email: (email || '').toLowerCase() })
      if (!user || !verifyPassword(password, user.passwordHash)) return handleCORS(NextResponse.json({ error: 'Email atau password salah' }, { status: 401 }))
      if (user.status === 'suspended') return handleCORS(NextResponse.json({ error: 'Akun Anda ditangguhkan' }, { status: 403 }))
      const token = signToken({ id: user.id, role: user.role })
      return handleCORS(NextResponse.json({ token, user: { id: user.id, name: user.name, email: user.email, role: user.role } }))
    }

    if (route === '/auth/me' && method === 'GET') {
      const user = await getUserFromRequest(request, db)
      if (!user) return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      return handleCORS(NextResponse.json({ user }))
    }

    // ---------- MEMBERS ----------
    if (route === '/members' && method === 'GET') {
      const user = await getUserFromRequest(request, db)
      if (!user) return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      const members = await db.collection('members').find({ userId: user.id }).sort({ createdAt: 1 }).toArray()
      const cleaned = members.map(({ _id, ...m }) => ({ ...m, age: calcAge(m.dob), instruments: instrumentsForAge(calcAge(m.dob)) }))
      return handleCORS(NextResponse.json(cleaned))
    }

    if (route === '/members' && method === 'POST') {
      const user = await getUserFromRequest(request, db)
      if (!user) return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      const body = await request.json()
      const { fullName, gender, dob, relationship } = body
      if (!fullName || !gender || !dob || !relationship) return handleCORS(NextResponse.json({ error: 'Semua field wajib diisi' }, { status: 400 }))
      const member = { id: uuidv4(), userId: user.id, fullName, gender, dob, relationship, createdAt: new Date() }
      await db.collection('members').insertOne(member)
      const { _id, ...m } = member
      return handleCORS(NextResponse.json({ ...m, age: calcAge(m.dob), instruments: instrumentsForAge(calcAge(m.dob)) }))
    }

    if (route.startsWith('/members/') && method === 'PUT') {
      const user = await getUserFromRequest(request, db)
      if (!user) return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      const id = path[1]
      const body = await request.json()
      const update = {}
      for (const k of ['fullName', 'gender', 'dob', 'relationship']) if (body[k] !== undefined) update[k] = body[k]
      await db.collection('members').updateOne({ id, userId: user.id }, { $set: update })
      const m = await db.collection('members').findOne({ id, userId: user.id })
      if (!m) return handleCORS(NextResponse.json({ error: 'Anggota tidak ditemukan' }, { status: 404 }))
      const { _id, ...rest } = m
      return handleCORS(NextResponse.json({ ...rest, age: calcAge(rest.dob), instruments: instrumentsForAge(calcAge(rest.dob)) }))
    }

    if (route.startsWith('/members/') && method === 'DELETE') {
      const user = await getUserFromRequest(request, db)
      if (!user) return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      const id = path[1]
      await db.collection('members').deleteOne({ id, userId: user.id })
      await db.collection('assessments').deleteMany({ memberId: id, userId: user.id })
      return handleCORS(NextResponse.json({ ok: true }))
    }

    // ---------- QUESTIONNAIRE ----------
    if (route.startsWith('/questionnaire/') && method === 'GET') {
      const code = path[1]
      const q = getQuestionnaire(code)
      if (!q) return handleCORS(NextResponse.json({ error: 'Kuesioner tidak ditemukan' }, { status: 404 }))
      return handleCORS(NextResponse.json(q))
    }

    // ---------- ASSESSMENTS ----------
    if (route === '/assessments' && method === 'POST') {
      const user = await getUserFromRequest(request, db)
      if (!user) return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      const body = await request.json()
      const { memberId, instrumentCode, answers } = body
      const member = await db.collection('members').findOne({ id: memberId, userId: user.id })
      if (!member) return handleCORS(NextResponse.json({ error: 'Anggota tidak ditemukan' }, { status: 404 }))
      const age = calcAge(member.dob)
      const q = getQuestionnaire(instrumentCode)
      if (!q) return handleCORS(NextResponse.json({ error: 'Kuesioner tidak valid' }, { status: 400 }))
      let result
      if (q.family === 'sdq') result = scoreSDQ(answers, age, instrumentCode === 'sdq_parent' ? 'parent' : 'self')
      else if (q.family === 'phq9') result = scorePHQ(answers)
      else if (q.family === 'ghq12') result = scoreGHQ(answers)
      const assessment = {
        id: uuidv4(), userId: user.id, userEmail: user.email,
        memberId, memberName: member.fullName, memberAge: age, memberGender: member.gender,
        instrumentCode, instrumentName: q.name, family: q.family,
        answers, result, createdAt: new Date(),
      }
      await db.collection('assessments').insertOne(assessment)
      if (result.redFlag) {
        const { type, severity } = alertTypeFor(result)
        await db.collection('alerts').insertOne({
          id: uuidv4(), assessmentId: assessment.id, userId: user.id, userEmail: user.email,
          memberName: member.fullName, memberAge: age, instrumentCode, instrumentName: q.name,
          type, severity, category: result.overallCategory, status: 'New', createdAt: new Date(),
        })
      }
      const { _id, ...clean } = assessment
      return handleCORS(NextResponse.json(clean))
    }

    if (route === '/assessments' && method === 'GET') {
      const user = await getUserFromRequest(request, db)
      if (!user) return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      const url = new URL(request.url)
      const memberId = url.searchParams.get('memberId')
      const filter = { userId: user.id }
      if (memberId) filter.memberId = memberId
      const list = await db.collection('assessments').find(filter).sort({ createdAt: -1 }).toArray()
      const cleaned = list.map(({ _id, ...a }) => a)
      return handleCORS(NextResponse.json(cleaned))
    }

    if (route.startsWith('/assessments/') && method === 'GET') {
      const user = await getUserFromRequest(request, db)
      if (!user) return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      const id = path[1]
      const a = await db.collection('assessments').findOne({ id, userId: user.id })
      if (!a) return handleCORS(NextResponse.json({ error: 'Tidak ditemukan' }, { status: 404 }))
      const { _id, ...clean } = a
      return handleCORS(NextResponse.json(clean))
    }

    // ---------- REFERRALS ----------
    if (route === '/referrals' && method === 'GET') {
      const list = await db.collection('referrals').find({}).toArray()
      let cleaned = list.map(({ _id, ...r }) => r)
      if (cleaned.length === 0) {
        cleaned = [
          { id: 'default-1', name: 'Hotline SEJIWA (Kemenkes)', type: 'Hotline Darurat', contact: '119 ext 8', note: 'Konseling & pencegahan bunuh diri 24 jam' },
          { id: 'default-2', name: 'LISA Suicide Prevention Helpline', type: 'Hotline', contact: '021-9696-9293', note: 'Dukungan krisis' },
        ]
      }
      return handleCORS(NextResponse.json(cleaned))
    }

    return handleCORS(NextResponse.json({ error: `Route ${route} not found` }, { status: 404 }))
  } catch (error) {
    console.error('API Error:', error)
    return handleCORS(NextResponse.json({ error: 'Internal server error', detail: String(error) }, { status: 500 }))
  }
}

export const GET = handleRoute
export const POST = handleRoute
export const PUT = handleRoute
export const DELETE = handleRoute
export const PATCH = handleRoute
