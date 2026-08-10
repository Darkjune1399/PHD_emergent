import { MongoClient } from 'mongodb'
import { v4 as uuidv4 } from 'uuid'
import { NextResponse } from 'next/server'
import crypto from 'crypto'

// ================= MongoDB connection =================
let client
let db
let seeded = false
async function connectToMongo() {
  if (!client) {
    client = new MongoClient(process.env.MONGO_URL)
    await client.connect()
    db = client.db(process.env.DB_NAME)
  }
  if (!seeded) { await ensureSeed(db); seeded = true }
  return db
}

function handleCORS(response) {
  response.headers.set('Access-Control-Allow-Origin', process.env.CORS_ORIGINS || '*')
  response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH')
  response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  response.headers.set('Access-Control-Allow-Credentials', 'true')
  return response
}
export async function OPTIONS() { return handleCORS(new NextResponse(null, { status: 200 })) }

const JWT_SECRET = process.env.JWT_SECRET || 'psikologi-asesmen-secret-2025'
const ADMIN_ROLES = ['super_admin', 'admin_medis', 'admin_teknis']

// ================= Auth helpers =================
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
function isAdmin(user) { return user && ADMIN_ROLES.includes(user.role) }

function calcAge(dob) {
  const b = new Date(dob); const now = new Date()
  let age = now.getFullYear() - b.getFullYear()
  const m = now.getMonth() - b.getMonth()
  if (m < 0 || (m === 0 && now.getDate() < b.getDate())) age--
  return age
}
async function audit(db, actor, action, detail) {
  await db.collection('audit_logs').insertOne({ id: uuidv4(), actorId: actor?.id, actorName: actor?.name, actorRole: actor?.role, action, detail, createdAt: new Date() })
}

// ================= DEFAULT SEED DATA =================
const SDQ_OPTIONS = [{ label: 'Tidak Benar', value: 0 }, { label: 'Agak Benar', value: 1 }, { label: 'Benar', value: 2 }]
const GHQ_OPTIONS = [{ label: 'Lebih baik dari biasanya', value: 0 }, { label: 'Sama seperti biasanya', value: 1 }, { label: 'Kurang dari biasanya', value: 2 }, { label: 'Jauh berkurang dari biasanya', value: 3 }]
const PHQ_OPTIONS = [{ label: 'Tidak Pernah', value: 0 }, { label: 'Beberapa hari', value: 1 }, { label: 'Lebih dari separuh waktu', value: 2 }, { label: 'Hampir setiap hari', value: 3 }]

const SDQ_DEF = [
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
const GHQ_DEF = [
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
const PHQ_DEF = [
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
const SUB_NAMES = { E: 'Gejala Emosional', C: 'Masalah Perilaku', H: 'Hiperaktivitas/Inatensi', P: 'Masalah Teman Sebaya', Pr: 'Perilaku Prososial' }

function sdqDoc(code, variant, cutoffs) {
  return {
    code, family: 'sdq', name: code === 'sdq_parent' ? 'SDQ - Laporan Orang Tua/Guru' : 'SDQ - Laporan Diri (Remaja)',
    instruction: 'Untuk setiap pernyataan, pilih jawaban yang paling menggambarkan kondisi dalam 6 bulan terakhir.',
    options: SDQ_OPTIONS,
    items: SDQ_DEF.map(i => ({ id: i.id, text: i[variant], sub: i.sub, reversed: i.rev })),
    cutoffs,
    recommendations: {
      Normal: 'Secara umum kondisi berada dalam batas normal. Pertahankan komunikasi hangat dan pola pengasuhan yang positif.',
      Ambang: 'Total Skor Kesulitan berada pada kategori AMBANG (borderline). Disarankan pemantauan lebih lanjut dan mempertimbangkan konsultasi dengan psikolog/konselor sekolah.',
      Abnormal: 'Total Skor Kesulitan berada pada kategori ABNORMAL. Sangat disarankan untuk berkonsultasi dengan psikolog atau tenaga kesehatan jiwa profesional.',
    },
  }
}
function defaultInstruments() {
  return [
    sdqDoc('sdq_parent', 'parent', { E: [3, 4], C: [2, 3], H: [5, 6], P: [3, 4], total: [13, 15], prosocial: [6, 5] }),
    sdqDoc('sdq_self', 'self', { E: [5, 6], C: [3, 4], H: [5, 6], P: [3, 5], total: [15, 19], prosocial: [6, 5] }),
    {
      code: 'phq9', family: 'phq9', name: 'PHQ-9 (Skrining Depresi)',
      instruction: 'Selama 2 minggu terakhir, seberapa sering Anda terganggu oleh masalah berikut?',
      options: PHQ_OPTIONS, items: PHQ_DEF.map(i => ({ id: i.id, text: i.text })),
      suicideItem: 9,
      severityBands: [
        { max: 4, label: 'Minimal', rec: 'Gejala depresi minimal/tidak ada. Pertahankan gaya hidup sehat, tidur cukup, dan aktivitas fisik teratur.' },
        { max: 9, label: 'Ringan', rec: 'Depresi ringan. Disarankan self-care & pemantauan; pertimbangkan konsultasi bila gejala menetap lebih dari 2 minggu.' },
        { max: 14, label: 'Sedang', rec: 'Depresi sedang. Disarankan berkonsultasi dengan psikolog/dokter untuk penanganan lebih lanjut.' },
        { max: 19, label: 'Sedang-Berat', rec: 'Depresi sedang-berat. Sangat disarankan segera berkonsultasi dengan profesional kesehatan jiwa.' },
        { max: 27, label: 'Berat', rec: 'Depresi berat. Diperlukan penanganan profesional segera.' },
      ],
      redFlagSeverities: ['Berat'],
    },
    {
      code: 'ghq12', family: 'ghq12', name: 'GHQ-12 (Kesehatan Mental Umum)',
      instruction: 'Bagaimana kondisi Anda akhir-akhir ini? Pilih jawaban yang paling sesuai.',
      options: GHQ_OPTIONS, items: GHQ_DEF.map(i => ({ id: i.id, text: i.text, sub: i.sub })),
      threshold: 18,
      recommendations: {
        problem: 'Skor total >= ambang mengindikasikan adanya distres psikologis. Disarankan menerapkan teknik manajemen stres dan berkonsultasi dengan tenaga profesional.',
        normal: 'Skor total di bawah ambang. Tidak ditemukan indikasi masalah psikopatologis yang signifikan. Tetap jaga kesehatan mental Anda.',
      },
    },
  ]
}
function defaultAgeRules() {
  return { id: 'default', rules: [
    { minAge: 4, maxAge: 10, codes: ['sdq_parent'], label: 'Anak (4-10 th)' },
    { minAge: 11, maxAge: 18, codes: ['sdq_self'], label: 'Remaja (11-18 th)' },
    { minAge: 19, maxAge: 200, codes: ['phq9', 'ghq12'], label: 'Dewasa (>18 th)' },
  ] }
}
async function ensureSeed(db) {
  const admin = await db.collection('users').findOne({ role: 'super_admin' })
  if (!admin) {
    await db.collection('users').insertOne({ id: uuidv4(), name: 'Super Admin', email: 'admin@siap.id', passwordHash: hashPassword('admin123'), role: 'super_admin', status: 'active', createdAt: new Date() })
  }
  const instCount = await db.collection('instruments').countDocuments()
  if (instCount === 0) await db.collection('instruments').insertMany(defaultInstruments())
  const ar = await db.collection('age_rules').findOne({ id: 'default' })
  if (!ar) await db.collection('age_rules').insertOne(defaultAgeRules())
  const refCount = await db.collection('referrals').countDocuments()
  if (refCount === 0) await db.collection('referrals').insertMany([
    { id: uuidv4(), name: 'Hotline SEJIWA (Kemenkes)', type: 'Hotline Darurat', contact: '119 ext 8', note: 'Konseling & pencegahan bunuh diri 24 jam' },
    { id: uuidv4(), name: 'LISA Suicide Prevention Helpline', type: 'Hotline', contact: '021-9696-9293', note: 'Dukungan krisis' },
  ])
}

async function getInstrument(db, code) {
  const doc = await db.collection('instruments').findOne({ code })
  if (!doc) return null
  const { _id, ...rest } = doc
  return rest
}
function publicQuestionnaire(inst) {
  return { code: inst.code, family: inst.family, name: inst.name, instruction: inst.instruction, options: inst.options, items: inst.items.map(i => ({ id: i.id, text: i.text })) }
}
async function instrumentsForAge(db, age) {
  const ar = await db.collection('age_rules').findOne({ id: 'default' })
  const rules = ar?.rules || []
  const match = rules.find(r => age >= r.minAge && age <= r.maxAge)
  if (!match) return []
  const out = []
  for (const code of match.codes) {
    const inst = await db.collection('instruments').findOne({ code })
    if (inst) out.push({ code, name: inst.name })
  }
  return out
}

// ================= SCORING (config-driven) =================
function catScale(score, normalMax, ambangMax) { if (score <= normalMax) return 'Normal'; if (score <= ambangMax) return 'Ambang'; return 'Abnormal' }
function catProsocial(score, normalMin, ambangVal) { if (score >= normalMin) return 'Normal'; if (score === ambangVal) return 'Ambang'; return 'Abnormal' }

function computeScore(inst, answers) {
  if (inst.family === 'sdq') {
    const maxVal = Math.max(...inst.options.map(o => o.value))
    const subs = { E: 0, C: 0, H: 0, P: 0, Pr: 0 }
    for (const item of inst.items) { const v = Number(answers[item.id] ?? 0); subs[item.sub] += item.reversed ? (maxVal - v) : v }
    const total = subs.E + subs.C + subs.H + subs.P
    const c = inst.cutoffs
    const categories = {
      E: catScale(subs.E, c.E[0], c.E[1]), C: catScale(subs.C, c.C[0], c.C[1]),
      H: catScale(subs.H, c.H[0], c.H[1]), P: catScale(subs.P, c.P[0], c.P[1]),
      Pr: catProsocial(subs.Pr, c.prosocial[0], c.prosocial[1]),
    }
    const totalCategory = catScale(total, c.total[0], c.total[1])
    const redFlag = totalCategory === 'Abnormal' || ['E', 'C', 'H', 'P'].some(k => categories[k] === 'Abnormal')
    const recs = [inst.recommendations[totalCategory]]
    const flagged = ['E', 'C', 'H', 'P', 'Pr'].filter(k => categories[k] !== 'Normal')
    if (flagged.length) recs.push('Aspek yang perlu perhatian: ' + flagged.map(k => `${SUB_NAMES[k]} (${categories[k]})`).join(', ') + '.')
    const subDetail = ['E', 'C', 'H', 'P', 'Pr'].map(k => ({ key: k, name: SUB_NAMES[k], score: subs[k], category: categories[k] }))
    return { family: 'sdq', subscales: subs, categories, subDetail, totalDifficulties: total, totalCategory, overallCategory: totalCategory, trendScore: total, trendMax: 40, trendLabel: 'Total Kesulitan', redFlag, suicideRisk: false, recommendations: recs }
  }
  if (inst.family === 'phq9') {
    let total = 0
    for (const item of inst.items) total += Number(answers[item.id] ?? 0)
    const item9 = Number(answers[inst.suicideItem] ?? 0)
    const band = inst.severityBands.find(b => total <= b.max) || inst.severityBands[inst.severityBands.length - 1]
    const severity = band.label
    const suicideRisk = item9 > 0
    const redFlag = suicideRisk || (inst.redFlagSeverities || []).includes(severity)
    const recs = [band.rec]
    if (suicideRisk) recs.unshift('PERHATIAN: Terdapat laporan pikiran untuk lebih baik mati atau menyakiti diri sendiri. Segera hubungi kontak darurat/profesional. Hotline SEJIWA / Kemenkes: 119 ext 8.')
    return { family: 'phq9', total, item9, severity, overallCategory: severity, trendScore: total, trendMax: 27, trendLabel: 'Skor PHQ-9', redFlag, suicideRisk, recommendations: recs }
  }
  if (inst.family === 'ghq12') {
    let total = 0, distress = 0, dysfunction = 0
    for (const item of inst.items) { const v = Number(answers[item.id] ?? 0); total += v; if (item.sub === 'D') distress += v; else dysfunction += v }
    const problem = total >= inst.threshold
    const overallCategory = problem ? 'Indikasi Masalah Psikologis' : 'Normal'
    const recs = [problem ? inst.recommendations.problem : inst.recommendations.normal]
    return { family: 'ghq12', total, distress, dysfunction, overallCategory, trendScore: total, trendMax: 36, trendLabel: 'Skor GHQ-12', redFlag: problem, suicideRisk: false, recommendations: recs }
  }
  return null
}
function alertTypeFor(result) {
  if (result.suicideRisk) return { type: 'Ide Bunuh Diri / Melukai Diri', severity: 'Kritis' }
  if (result.family === 'phq9') return { type: 'Depresi Berat (PHQ-9)', severity: 'Tinggi' }
  if (result.family === 'sdq') return { type: 'SDQ Abnormal', severity: 'Tinggi' }
  if (result.family === 'ghq12') return { type: 'Distres Psikologis (GHQ-12)', severity: 'Sedang' }
  return { type: 'Risiko Tinggi', severity: 'Tinggi' }
}
function levelOf(cat) {
  const c = (cat || '').toLowerCase()
  if (['normal', 'minimal'].includes(c)) return 'Normal'
  if (['ambang', 'ringan', 'sedang'].includes(c)) return 'Ambang'
  return 'Abnormal'
}

// ================= ROUTER =================
async function handleRoute(request, { params }) {
  const { path = [] } = await params
  const route = `/${path.join('/')}`
  const method = request.method
  try {
    const db = await connectToMongo()
    if (route === '/' && method === 'GET') return handleCORS(NextResponse.json({ message: 'SIAP API aktif' }))

    // ---------- AUTH ----------
    if (route === '/auth/register' && method === 'POST') {
      const { name, email, password } = await request.json()
      if (!name || !email || !password) return handleCORS(NextResponse.json({ error: 'Nama, email, dan password wajib diisi' }, { status: 400 }))
      const existing = await db.collection('users').findOne({ email: email.toLowerCase() })
      if (existing) return handleCORS(NextResponse.json({ error: 'Email sudah terdaftar' }, { status: 400 }))
      const user = { id: uuidv4(), name, email: email.toLowerCase(), passwordHash: hashPassword(password), role: 'user', status: 'active', createdAt: new Date() }
      await db.collection('users').insertOne(user)
      const token = signToken({ id: user.id, role: user.role })
      return handleCORS(NextResponse.json({ token, user: { id: user.id, name: user.name, email: user.email, role: user.role } }))
    }
    if (route === '/auth/login' && method === 'POST') {
      const { email, password } = await request.json()
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
      const out = []
      for (const m of members) { const { _id, ...rest } = m; const age = calcAge(rest.dob); out.push({ ...rest, age, instruments: await instrumentsForAge(db, age) }) }
      return handleCORS(NextResponse.json(out))
    }
    if (route === '/members' && method === 'POST') {
      const user = await getUserFromRequest(request, db)
      if (!user) return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      const { fullName, gender, dob, relationship } = await request.json()
      if (!fullName || !gender || !dob || !relationship) return handleCORS(NextResponse.json({ error: 'Semua field wajib diisi' }, { status: 400 }))
      const member = { id: uuidv4(), userId: user.id, fullName, gender, dob, relationship, createdAt: new Date() }
      await db.collection('members').insertOne(member)
      const { _id, ...m } = member; const age = calcAge(m.dob)
      return handleCORS(NextResponse.json({ ...m, age, instruments: await instrumentsForAge(db, age) }))
    }
    if (route.startsWith('/members/') && method === 'PUT') {
      const user = await getUserFromRequest(request, db)
      if (!user) return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      const id = path[1]; const body = await request.json(); const update = {}
      for (const k of ['fullName', 'gender', 'dob', 'relationship']) if (body[k] !== undefined) update[k] = body[k]
      await db.collection('members').updateOne({ id, userId: user.id }, { $set: update })
      const m = await db.collection('members').findOne({ id, userId: user.id })
      if (!m) return handleCORS(NextResponse.json({ error: 'Anggota tidak ditemukan' }, { status: 404 }))
      const { _id, ...rest } = m; const age = calcAge(rest.dob)
      return handleCORS(NextResponse.json({ ...rest, age, instruments: await instrumentsForAge(db, age) }))
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
      const inst = await getInstrument(db, path[1])
      if (!inst) return handleCORS(NextResponse.json({ error: 'Kuesioner tidak ditemukan' }, { status: 404 }))
      return handleCORS(NextResponse.json(publicQuestionnaire(inst)))
    }

    // ---------- ASSESSMENTS ----------
    if (route === '/assessments' && method === 'POST') {
      const user = await getUserFromRequest(request, db)
      if (!user) return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      const { memberId, instrumentCode, answers } = await request.json()
      const member = await db.collection('members').findOne({ id: memberId, userId: user.id })
      if (!member) return handleCORS(NextResponse.json({ error: 'Anggota tidak ditemukan' }, { status: 404 }))
      const age = calcAge(member.dob)
      const inst = await getInstrument(db, instrumentCode)
      if (!inst) return handleCORS(NextResponse.json({ error: 'Kuesioner tidak valid' }, { status: 400 }))
      const result = computeScore(inst, answers)
      const assessment = { id: uuidv4(), userId: user.id, userEmail: user.email, memberId, memberName: member.fullName, memberAge: age, memberGender: member.gender, instrumentCode, instrumentName: inst.name, family: inst.family, answers, result, createdAt: new Date() }
      await db.collection('assessments').insertOne(assessment)
      if (result.redFlag) {
        const { type, severity } = alertTypeFor(result)
        await db.collection('alerts').insertOne({ id: uuidv4(), assessmentId: assessment.id, userId: user.id, userEmail: user.email, memberName: member.fullName, memberAge: age, instrumentCode, instrumentName: inst.name, type, severity, category: result.overallCategory, status: 'New', createdAt: new Date() })
      }
      const { _id, ...clean } = assessment
      return handleCORS(NextResponse.json(clean))
    }
    if (route === '/assessments' && method === 'GET') {
      const user = await getUserFromRequest(request, db)
      if (!user) return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      const url = new URL(request.url); const memberId = url.searchParams.get('memberId')
      const filter = { userId: user.id }; if (memberId) filter.memberId = memberId
      const list = await db.collection('assessments').find(filter).sort({ createdAt: -1 }).toArray()
      return handleCORS(NextResponse.json(list.map(({ _id, ...a }) => a)))
    }
    if (route.startsWith('/assessments/') && method === 'GET') {
      const user = await getUserFromRequest(request, db)
      if (!user) return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      const a = await db.collection('assessments').findOne({ id: path[1], userId: user.id })
      if (!a) return handleCORS(NextResponse.json({ error: 'Tidak ditemukan' }, { status: 404 }))
      const { _id, ...clean } = a
      return handleCORS(NextResponse.json(clean))
    }

    if (route === '/referrals' && method === 'GET') {
      const list = await db.collection('referrals').find({}).toArray()
      return handleCORS(NextResponse.json(list.map(({ _id, ...r }) => r)))
    }

    // =================== ADMIN ===================
    if (route.startsWith('/admin/')) {
      const user = await getUserFromRequest(request, db)
      if (!user) return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      if (!isAdmin(user)) return handleCORS(NextResponse.json({ error: 'Akses ditolak (bukan admin)' }, { status: 403 }))

      if (route === '/admin/stats' && method === 'GET') {
        const assessments = await db.collection('assessments').find({}).toArray()
        const total = assessments.length
        const dist = { Normal: 0, Ambang: 0, Abnormal: 0 }
        assessments.forEach(a => { dist[levelOf(a.result?.overallCategory)]++ })
        // trend last 14 days
        const days = {}
        for (let i = 13; i >= 0; i--) { const d = new Date(); d.setDate(d.getDate() - i); const key = d.toISOString().slice(0, 10); days[key] = 0 }
        assessments.forEach(a => { const key = new Date(a.createdAt).toISOString().slice(0, 10); if (key in days) days[key]++ })
        const trend = Object.entries(days).map(([date, count]) => ({ date: date.slice(5), count }))
        const alerts = await db.collection('alerts').find({}).toArray()
        const alertStatus = { New: 0, 'Under Review': 0, Referred: 0, Resolved: 0 }
        alerts.forEach(a => { if (a.status in alertStatus) alertStatus[a.status]++ })
        const totalUsers = await db.collection('users').countDocuments({ role: 'user' })
        const totalMembers = await db.collection('members').countDocuments()
        return handleCORS(NextResponse.json({ total, distribution: dist, trend, alertStatus, newAlerts: alertStatus['New'], totalUsers, totalMembers }))
      }

      if (route === '/admin/alerts' && method === 'GET') {
        const url = new URL(request.url); const status = url.searchParams.get('status')
        const filter = {}; if (status && status !== 'all') filter.status = status
        const list = await db.collection('alerts').find(filter).sort({ createdAt: -1 }).toArray()
        return handleCORS(NextResponse.json(list.map(({ _id, ...a }) => a)))
      }
      if (route.startsWith('/admin/alerts/') && method === 'PATCH') {
        const id = path[2]; const { status, note } = await request.json()
        const valid = ['New', 'Under Review', 'Referred', 'Resolved']
        if (!valid.includes(status)) return handleCORS(NextResponse.json({ error: 'Status tidak valid' }, { status: 400 }))
        await db.collection('alerts').updateOne({ id }, { $set: { status, note: note || '', updatedAt: new Date(), handledBy: user.name } })
        await audit(db, user, 'Ubah Status Alert', `Alert ${id} -> ${status}`)
        const a = await db.collection('alerts').findOne({ id })
        const { _id, ...clean } = a
        return handleCORS(NextResponse.json(clean))
      }
      if (route.startsWith('/admin/alerts/') && method === 'GET') {
        const a = await db.collection('alerts').findOne({ id: path[2] })
        if (!a) return handleCORS(NextResponse.json({ error: 'Tidak ditemukan' }, { status: 404 }))
        const assessment = await db.collection('assessments').findOne({ id: a.assessmentId })
        const { _id, ...ca } = a
        return handleCORS(NextResponse.json({ ...ca, assessment: assessment ? (({ _id, ...r }) => r)(assessment) : null }))
      }

      if (route === '/admin/instruments' && method === 'GET') {
        const list = await db.collection('instruments').find({}).toArray()
        return handleCORS(NextResponse.json(list.map(({ _id, ...i }) => i)))
      }
      if (route.startsWith('/admin/instruments/') && method === 'GET') {
        const inst = await getInstrument(db, path[2])
        if (!inst) return handleCORS(NextResponse.json({ error: 'Tidak ditemukan' }, { status: 404 }))
        return handleCORS(NextResponse.json(inst))
      }
      if (route.startsWith('/admin/instruments/') && method === 'PUT') {
        const code = path[2]; const body = await request.json()
        const allowed = {}
        for (const k of ['name', 'instruction', 'items', 'options', 'cutoffs', 'recommendations', 'severityBands', 'redFlagSeverities', 'threshold', 'suicideItem']) if (body[k] !== undefined) allowed[k] = body[k]
        await db.collection('instruments').updateOne({ code }, { $set: allowed })
        await audit(db, user, 'Ubah Master Kuesioner', `Instrumen ${code} diperbarui`)
        const inst = await getInstrument(db, code)
        return handleCORS(NextResponse.json(inst))
      }

      if (route === '/admin/age-rules' && method === 'GET') {
        const ar = await db.collection('age_rules').findOne({ id: 'default' })
        const { _id, ...clean } = ar
        return handleCORS(NextResponse.json(clean))
      }
      if (route === '/admin/age-rules' && method === 'PUT') {
        const { rules } = await request.json()
        await db.collection('age_rules').updateOne({ id: 'default' }, { $set: { rules } })
        await audit(db, user, 'Ubah Aturan Usia', `${rules?.length || 0} aturan`)
        const ar = await db.collection('age_rules').findOne({ id: 'default' })
        const { _id, ...clean } = ar
        return handleCORS(NextResponse.json(clean))
      }

      if (route === '/admin/audit-logs' && method === 'GET') {
        const list = await db.collection('audit_logs').find({}).sort({ createdAt: -1 }).limit(50).toArray()
        return handleCORS(NextResponse.json(list.map(({ _id, ...l }) => l)))
      }

      if (route === '/admin/referrals' && method === 'GET') {
        const list = await db.collection('referrals').find({}).toArray()
        return handleCORS(NextResponse.json(list.map(({ _id, ...r }) => r)))
      }
      if (route === '/admin/referrals' && method === 'POST') {
        const { name, type, contact, note } = await request.json()
        const doc = { id: uuidv4(), name, type, contact, note }
        await db.collection('referrals').insertOne(doc)
        await audit(db, user, 'Tambah Rujukan', name)
        return handleCORS(NextResponse.json(doc))
      }
      if (route.startsWith('/admin/referrals/') && method === 'DELETE') {
        await db.collection('referrals').deleteOne({ id: path[2] })
        await audit(db, user, 'Hapus Rujukan', path[2])
        return handleCORS(NextResponse.json({ ok: true }))
      }

      // ---- User Management ----
      if (route === '/admin/users' && method === 'GET') {
        const users = await db.collection('users').find({ role: 'user' }).sort({ createdAt: -1 }).toArray()
        const out = []
        for (const u of users) {
          const { _id, passwordHash, ...safe } = u
          const memberCount = await db.collection('members').countDocuments({ userId: u.id })
          const assessmentCount = await db.collection('assessments').countDocuments({ userId: u.id })
          out.push({ ...safe, status: safe.status || 'active', memberCount, assessmentCount })
        }
        return handleCORS(NextResponse.json(out))
      }
      if (route.startsWith('/admin/users/') && path[3] === 'reset-password' && method === 'POST') {
        const id = path[2]; const { newPassword } = await request.json()
        if (!newPassword || newPassword.length < 4) return handleCORS(NextResponse.json({ error: 'Password minimal 4 karakter' }, { status: 400 }))
        const target = await db.collection('users').findOne({ id })
        if (!target) return handleCORS(NextResponse.json({ error: 'User tidak ditemukan' }, { status: 404 }))
        await db.collection('users').updateOne({ id }, { $set: { passwordHash: hashPassword(newPassword) } })
        await audit(db, user, 'Reset Password User', `${target.email}`)
        return handleCORS(NextResponse.json({ ok: true }))
      }
      if (route.startsWith('/admin/users/') && method === 'PATCH') {
        const id = path[2]; const { status } = await request.json()
        if (!['active', 'suspended'].includes(status)) return handleCORS(NextResponse.json({ error: 'Status tidak valid' }, { status: 400 }))
        const target = await db.collection('users').findOne({ id })
        if (!target) return handleCORS(NextResponse.json({ error: 'User tidak ditemukan' }, { status: 404 }))
        await db.collection('users').updateOne({ id }, { $set: { status } })
        await audit(db, user, status === 'suspended' ? 'Suspend Akun User' : 'Aktifkan Akun User', `${target.email}`)
        const u = await db.collection('users').findOne({ id })
        const { _id, passwordHash, ...safe } = u
        return handleCORS(NextResponse.json(safe))
      }
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
