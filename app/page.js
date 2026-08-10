'use client'

import { useState, useEffect, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogAction } from '@/components/ui/alert-dialog'
import { Toaster } from '@/components/ui/sonner'
import { toast } from 'sonner'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts'
import { Textarea } from '@/components/ui/textarea'
import { Brain, Users, Plus, LogOut, Heart, Activity, FileText, ClipboardList, AlertTriangle, Trash2, Pencil, ArrowLeft, Phone, TrendingUp, ShieldAlert, HeartPulse, Baby, User, LayoutDashboard, Bell, Settings, ListChecks, ScrollText, Save, ShieldCheck, RefreshCw, UserCog, KeyRound, Ban, CheckCircle2, BookUser } from 'lucide-react'

const REL_OPTS = ['Diri Sendiri', 'Anak', 'Pasangan', 'Orang Tua', 'Saudara Kandung', 'Lainnya']
const ADMIN_ROLES = ['super_admin', 'admin_medis', 'admin_teknis']
function isAdminRole(role) { return ADMIN_ROLES.includes(role) }

function api(path, { method = 'GET', body, token } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  return fetch(`/api${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined }).then(async r => {
    const data = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(data.error || 'Terjadi kesalahan')
    return data
  })
}

function catLevel(cat) {
  if (!cat) return 'ok'
  const c = cat.toLowerCase()
  if (['normal', 'minimal'].some(x => c === x)) return 'ok'
  if (['ambang', 'ringan', 'sedang'].some(x => c === x)) return 'warn'
  return 'danger'
}
function CatBadge({ cat }) {
  const lvl = catLevel(cat)
  const cls = lvl === 'ok' ? 'bg-emerald-100 text-emerald-700 border-emerald-200'
    : lvl === 'warn' ? 'bg-amber-100 text-amber-700 border-amber-200'
    : 'bg-red-100 text-red-700 border-red-200'
  return <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${cls}`}>{cat}</span>
}
function ageIcon(age) {
  if (age <= 10) return <Baby className="h-5 w-5" />
  return <User className="h-5 w-5" />
}

export default function App() {
  const [token, setToken] = useState(null)
  const [user, setUser] = useState(null)
  const [booted, setBooted] = useState(false)
  const [view, setView] = useState('dashboard')

  const [members, setMembers] = useState([])
  const [activeMember, setActiveMember] = useState(null)
  const [questionnaire, setQuestionnaire] = useState(null)
  const [answers, setAnswers] = useState({})
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [referrals, setReferrals] = useState([])
  const [emergencyOpen, setEmergencyOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  const [authMode, setAuthMode] = useState('login')
  const [af, setAf] = useState({ name: '', email: '', password: '' })

  const [memberDialog, setMemberDialog] = useState(false)
  const [editingMember, setEditingMember] = useState(null)
  const [mf, setMf] = useState({ fullName: '', gender: 'Laki-laki', dob: '', relationship: 'Anak' })

  useEffect(() => {
    const t = typeof window !== 'undefined' ? localStorage.getItem('siap_token') : null
    if (t) { setToken(t); api('/auth/me', { token: t }).then(d => { setUser(d.user); setBooted(true) }).catch(() => { localStorage.removeItem('siap_token'); setToken(null); setBooted(true) }) }
    else setBooted(true)
  }, [])

  useEffect(() => { if (token && user && !isAdminRole(user.role)) loadMembers() }, [token, user])

  function loadMembers() { api('/members', { token }).then(setMembers).catch(e => toast.error(e.message)) }

  async function handleAuth(e) {
    e.preventDefault()
    setLoading(true)
    try {
      const path = authMode === 'login' ? '/auth/login' : '/auth/register'
      const body = authMode === 'login' ? { email: af.email, password: af.password } : af
      const d = await api(path, { method: 'POST', body })
      localStorage.setItem('siap_token', d.token)
      setToken(d.token); setUser(d.user)
      toast.success(authMode === 'login' ? 'Berhasil masuk' : 'Akun berhasil dibuat')
    } catch (e) { toast.error(e.message) } finally { setLoading(false) }
  }

  function logout() { localStorage.removeItem('siap_token'); setToken(null); setUser(null); setView('dashboard'); setMembers([]) }

  function openAddMember() { setEditingMember(null); setMf({ fullName: '', gender: 'Laki-laki', dob: '', relationship: 'Anak' }); setMemberDialog(true) }
  function openEditMember(m) { setEditingMember(m); setMf({ fullName: m.fullName, gender: m.gender, dob: m.dob, relationship: m.relationship }); setMemberDialog(true) }

  async function saveMember(e) {
    e.preventDefault()
    try {
      if (editingMember) { await api(`/members/${editingMember.id}`, { method: 'PUT', body: mf, token }); toast.success('Profil diperbarui') }
      else { await api('/members', { method: 'POST', body: mf, token }); toast.success('Anggota keluarga ditambahkan') }
      setMemberDialog(false); loadMembers()
    } catch (e) { toast.error(e.message) }
  }

  async function deleteMember(m) {
    if (!confirm(`Hapus profil ${m.fullName}? Seluruh riwayat asesmennya juga akan dihapus.`)) return
    try { await api(`/members/${m.id}`, { method: 'DELETE', token }); toast.success('Profil dihapus'); loadMembers() } catch (e) { toast.error(e.message) }
  }

  function startAssessment(member) {
    setActiveMember(member)
    if (member.age < 4) { toast.error('Asesmen tersedia untuk usia 4 tahun ke atas.'); return }
    if (member.instruments.length === 1) loadQuestionnaire(member, member.instruments[0].code)
    else setView('select-instrument')
  }

  async function loadQuestionnaire(member, code) {
    try {
      setLoading(true)
      const q = await api(`/questionnaire/${code}`, { token })
      setQuestionnaire(q); setAnswers({}); setActiveMember(member); setView('assessment')
    } catch (e) { toast.error(e.message) } finally { setLoading(false) }
  }

  const answeredCount = questionnaire ? questionnaire.items.filter(i => answers[i.id] !== undefined).length : 0
  const totalItems = questionnaire ? questionnaire.items.length : 0
  const progressPct = totalItems ? Math.round((answeredCount / totalItems) * 100) : 0

  async function submitAssessment() {
    if (answeredCount < totalItems) { toast.error(`Masih ada ${totalItems - answeredCount} pernyataan belum dijawab`); return }
    try {
      setLoading(true)
      const d = await api('/assessments', { method: 'POST', body: { memberId: activeMember.id, instrumentCode: questionnaire.code, answers }, token })
      setResult(d); setView('result')
      if (d.result.suicideRisk) { await loadReferrals(); setEmergencyOpen(true) }
    } catch (e) { toast.error(e.message) } finally { setLoading(false) }
  }

  async function loadReferrals() { try { const r = await api('/referrals', { token }); setReferrals(r) } catch (e) {} }

  async function openHistory(member) {
    setActiveMember(member)
    try { const h = await api(`/assessments?memberId=${member.id}`, { token }); setHistory(h); setView('history') } catch (e) { toast.error(e.message) }
  }

  async function viewResult(assessmentId) {
    try { const d = await api(`/assessments/${assessmentId}`, { token }); setResult(d); setView('result') } catch (e) { toast.error(e.message) }
  }

  function printReport() {
    if (!result) return
    const r = result.result
    const rows = r.family === 'sdq'
      ? r.subDetail.map(s => `<tr><td>${s.name}</td><td style="text-align:center">${s.score}</td><td style="text-align:center">${s.category}</td></tr>`).join('') + `<tr style="font-weight:bold"><td>Total Kesulitan</td><td style="text-align:center">${r.totalDifficulties}</td><td style="text-align:center">${r.totalCategory}</td></tr>`
      : r.family === 'phq9' ? `<tr><td>Total Skor PHQ-9</td><td style="text-align:center">${r.total}/27</td><td style="text-align:center">${r.severity}</td></tr><tr><td>Item 9 (Ide melukai diri)</td><td style="text-align:center">${r.item9}</td><td></td></tr>`
      : `<tr><td>Total Skor GHQ-12</td><td style="text-align:center">${r.total}/36</td><td style="text-align:center">${r.overallCategory}</td></tr><tr><td>Distres Psikologis</td><td style="text-align:center">${r.distress}</td><td></td></tr><tr><td>Disfungsi Sosial</td><td style="text-align:center">${r.dysfunction}</td><td></td></tr>`
    const recs = r.recommendations.map(x => `<li>${x}</li>`).join('')
    const w = window.open('', '_blank')
    w.document.write(`<html><head><title>Laporan Asesmen - ${result.memberName}</title><style>body{font-family:Arial,sans-serif;padding:40px;color:#0f172a}h1{color:#0d9488}table{width:100%;border-collapse:collapse;margin:16px 0}td,th{border:1px solid #cbd5e1;padding:8px}th{background:#f1f5f9;text-align:left}.meta{color:#475569}.box{background:#f8fafc;border:1px solid #e2e8f0;padding:16px;border-radius:8px;margin-top:16px}</style></head><body><h1>Laporan Asesmen Kesehatan Psikologis</h1><p class="meta"><b>Nama:</b> ${result.memberName} &nbsp; | &nbsp; <b>Usia:</b> ${result.memberAge} th &nbsp; | &nbsp; <b>Instrumen:</b> ${result.instrumentName}<br/><b>Tanggal:</b> ${new Date(result.createdAt).toLocaleString('id-ID')}</p><h3>Hasil Skoring</h3><table><thead><tr><th>Aspek</th><th style="text-align:center">Skor</th><th style="text-align:center">Kategori</th></tr></thead><tbody>${rows}</tbody></table><div class="box"><h3>Rekomendasi</h3><ul>${recs}</ul></div><p style="margin-top:24px;font-size:12px;color:#64748b">Catatan: Hasil ini merupakan skrining awal, bukan diagnosis klinis. Untuk kepastian, konsultasikan dengan tenaga profesional.</p><script>window.onload=function(){window.print()}</script></body></html>`)
    w.document.close()
  }

  if (!booted) return <div className="min-h-screen flex items-center justify-center bg-slate-50"><Brain className="h-8 w-8 text-teal-600 animate-pulse" /></div>

  if (!token || !user) return <AuthScreen {...{ authMode, setAuthMode, af, setAf, handleAuth, loading }} />

  if (isAdminRole(user.role)) return <AdminPanel user={user} token={token} logout={logout} />

  return (
    <div className="min-h-screen bg-slate-50">
      <Toaster position="top-center" richColors />
      <header className="bg-gradient-to-r from-teal-600 to-cyan-600 text-white shadow-md">
        <div className="container flex items-center justify-between py-4">
          <button onClick={() => setView('dashboard')} className="flex items-center gap-2">
            <div className="bg-white/20 rounded-lg p-2"><Brain className="h-6 w-6" /></div>
            <div className="text-left">
              <div className="font-bold text-lg leading-none">SIAP</div>
              <div className="text-xs text-teal-50">Asesmen Kesehatan Psikologis</div>
            </div>
          </button>
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block"><div className="text-sm font-medium">{user.name}</div><div className="text-xs text-teal-50">{user.email}</div></div>
            <Button variant="secondary" size="sm" onClick={logout}><LogOut className="h-4 w-4 mr-1" /> Keluar</Button>
          </div>
        </div>
      </header>

      <main className="container py-8">
        {view === 'dashboard' && <Dashboard {...{ user, members, openAddMember, openEditMember, deleteMember, startAssessment, openHistory }} />}
        {view === 'select-instrument' && <SelectInstrument {...{ activeMember, loadQuestionnaire, setView }} />}
        {view === 'assessment' && questionnaire && <Assessment {...{ questionnaire, activeMember, answers, setAnswers, answeredCount, totalItems, progressPct, submitAssessment, setView, loading }} />}
        {view === 'result' && result && <ResultView {...{ result, setView, printReport, openHistory }} />}
        {view === 'history' && <HistoryView {...{ activeMember, history, setView, viewResult, startAssessment }} />}
      </main>

      <MemberDialog {...{ memberDialog, setMemberDialog, mf, setMf, saveMember, editingMember }} />
      <EmergencyDialog {...{ emergencyOpen, setEmergencyOpen, referrals }} />
    </div>
  )
}

function AuthScreen({ authMode, setAuthMode, af, setAf, handleAuth, loading }) {
  const [screen, setScreen] = useState('auth') // auth | forgot | reset
  const [fEmail, setFEmail] = useState('')
  const [demoToken, setDemoToken] = useState('')
  const [rToken, setRToken] = useState('')
  const [rPass, setRPass] = useState('')
  const [busy, setBusy] = useState(false)

  async function sendForgot(e) {
    e.preventDefault(); setBusy(true)
    try { const d = await api('/auth/forgot-password', { method: 'POST', body: { email: fEmail } }); setDemoToken(d.token); setRToken(d.token); toast.success('Tautan reset dibuat') } catch (e) { toast.error(e.message) } finally { setBusy(false) }
  }
  async function doReset(e) {
    e.preventDefault(); setBusy(true)
    try { await api('/auth/reset-password', { method: 'POST', body: { token: rToken, newPassword: rPass } }); toast.success('Password berhasil direset. Silakan masuk.'); setScreen('auth'); setDemoToken(''); setRPass(''); setAuthMode('login') } catch (e) { toast.error(e.message) } finally { setBusy(false) }
  }

  return (
    <div className="min-h-screen flex bg-slate-50">
      <Toaster position="top-center" richColors />
      <div className="hidden lg:flex lg:w-1/2 min-h-screen flex-col justify-center bg-gradient-to-br from-teal-600 to-cyan-700 text-white p-12">
        <div className="bg-white/20 rounded-2xl p-3 w-fit mb-6"><Brain className="h-10 w-10" /></div>
        <h1 className="text-4xl font-bold leading-tight">Asesmen Kesehatan Psikologis Keluarga</h1>
        <p className="mt-4 text-teal-50 text-lg">Skrining kesehatan mental otomatis untuk seluruh anggota keluarga dengan instrumen tervalidasi.</p>
        <div className="mt-8 space-y-3">
          <Feature icon={<Baby className="h-5 w-5" />} title="SDQ" desc="Anak & remaja usia 4-18 tahun" />
          <Feature icon={<HeartPulse className="h-5 w-5" />} title="PHQ-9 & GHQ-12" desc="Skrining depresi & kesehatan mental dewasa" />
          <Feature icon={<ShieldAlert className="h-5 w-5" />} title="Deteksi Risiko" desc="Peringatan dini untuk kondisi berisiko tinggi" />
        </div>
      </div>
      <div className="flex-1 flex items-center justify-center p-6">
        <Card className="w-full max-w-md">
          {screen === 'auth' && (<>
            <CardHeader><CardTitle className="text-2xl">{authMode === 'login' ? 'Masuk' : 'Buat Akun'}</CardTitle><CardDescription>Kelola asesmen kesehatan mental keluarga Anda</CardDescription></CardHeader>
            <CardContent>
              <Tabs value={authMode} onValueChange={setAuthMode} className="mb-4">
                <TabsList className="grid grid-cols-2 w-full"><TabsTrigger value="login">Masuk</TabsTrigger><TabsTrigger value="register">Daftar</TabsTrigger></TabsList>
              </Tabs>
              <form onSubmit={handleAuth} className="space-y-4">
                {authMode === 'register' && (<div><Label>Nama Lengkap</Label><Input value={af.name} onChange={e => setAf({ ...af, name: e.target.value })} placeholder="Nama Anda" required /></div>)}
                <div><Label>Email</Label><Input type="email" value={af.email} onChange={e => setAf({ ...af, email: e.target.value })} placeholder="email@contoh.com" required /></div>
                <div><Label>Password</Label><Input type="password" value={af.password} onChange={e => setAf({ ...af, password: e.target.value })} placeholder="********" required /></div>
                <Button type="submit" className="w-full bg-teal-600 hover:bg-teal-700" disabled={loading}>{loading ? 'Memproses...' : (authMode === 'login' ? 'Masuk' : 'Daftar')}</Button>
                {loading && <p className="text-xs text-slate-500 text-center">Mohon tunggu, permintaan pertama bisa memerlukan 10-15 detik...</p>}
              </form>
              {authMode === 'login' && <button onClick={() => { setScreen('forgot'); setFEmail(af.email) }} className="mt-3 text-sm text-teal-600 hover:underline w-full text-center">Lupa password?</button>}
            </CardContent>
          </>)}

          {screen === 'forgot' && (<>
            <CardHeader><CardTitle className="text-2xl flex items-center gap-2"><KeyRound className="h-6 w-6 text-teal-600" /> Lupa Password</CardTitle><CardDescription>Masukkan email akun Anda untuk mendapatkan tautan reset.</CardDescription></CardHeader>
            <CardContent>
              <form onSubmit={sendForgot} className="space-y-4">
                <div><Label>Email</Label><Input type="email" value={fEmail} onChange={e => setFEmail(e.target.value)} placeholder="email@contoh.com" required /></div>
                <Button type="submit" className="w-full bg-teal-600 hover:bg-teal-700" disabled={busy}>{busy ? 'Memproses...' : 'Kirim Tautan Reset'}</Button>
              </form>
              {demoToken && (
                <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm">
                  <div className="font-semibold text-amber-800 flex items-center gap-1"><AlertTriangle className="h-4 w-4" /> Mode Demo (email disimulasikan)</div>
                  <p className="text-amber-700 mt-1">Pada sistem nyata, tautan ini dikirim ke email. Untuk demo, gunakan kode berikut:</p>
                  <code className="block mt-2 break-all bg-white border rounded px-2 py-1 text-xs">{demoToken}</code>
                  <Button className="w-full mt-3 bg-amber-600 hover:bg-amber-700" onClick={() => setScreen('reset')}>Lanjut Reset Password</Button>
                </div>
              )}
              <button onClick={() => setScreen('auth')} className="mt-3 text-sm text-slate-500 hover:underline w-full text-center">Kembali ke Masuk</button>
            </CardContent>
          </>)}

          {screen === 'reset' && (<>
            <CardHeader><CardTitle className="text-2xl flex items-center gap-2"><KeyRound className="h-6 w-6 text-teal-600" /> Reset Password</CardTitle><CardDescription>Masukkan kode token dan password baru Anda.</CardDescription></CardHeader>
            <CardContent>
              <form onSubmit={doReset} className="space-y-4">
                <div><Label>Kode Token</Label><Input value={rToken} onChange={e => setRToken(e.target.value)} required /></div>
                <div><Label>Password Baru</Label><Input type="password" value={rPass} onChange={e => setRPass(e.target.value)} placeholder="Min. 4 karakter" required /></div>
                <Button type="submit" className="w-full bg-teal-600 hover:bg-teal-700" disabled={busy}>{busy ? 'Memproses...' : 'Simpan Password Baru'}</Button>
              </form>
              <button onClick={() => setScreen('auth')} className="mt-3 text-sm text-slate-500 hover:underline w-full text-center">Kembali ke Masuk</button>
            </CardContent>
          </>)}
        </Card>
      </div>
    </div>
  )
}
function Feature({ icon, title, desc }) {
  return <div className="flex items-center gap-3"><div className="bg-white/20 rounded-lg p-2">{icon}</div><div><div className="font-semibold">{title}</div><div className="text-sm text-teal-50">{desc}</div></div></div>
}

function Dashboard({ user, members, openAddMember, openEditMember, deleteMember, startAssessment, openHistory }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div><h2 className="text-2xl font-bold text-slate-800">Selamat datang, {user.name}</h2><p className="text-slate-500">Kelola profil keluarga dan lakukan asesmen kesehatan mental.</p></div>
        <Button onClick={openAddMember} className="bg-teal-600 hover:bg-teal-700"><Plus className="h-4 w-4 mr-1" /> Tambah Anggota</Button>
      </div>
      {members.length === 0 ? (
        <Card className="border-dashed"><CardContent className="flex flex-col items-center justify-center py-16 text-center"><Users className="h-12 w-12 text-slate-300 mb-3" /><h3 className="font-semibold text-slate-700">Belum ada anggota keluarga</h3><p className="text-slate-500 text-sm mb-4">Tambahkan anggota keluarga untuk memulai asesmen.</p><Button onClick={openAddMember} className="bg-teal-600 hover:bg-teal-700"><Plus className="h-4 w-4 mr-1" /> Tambah Anggota</Button></CardContent></Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {members.map(m => (
            <Card key={m.id} className="overflow-hidden hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-11 w-11 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center font-bold">{m.fullName.charAt(0).toUpperCase()}</div>
                    <div><CardTitle className="text-base">{m.fullName}</CardTitle><CardDescription>{m.relationship} • {m.gender}</CardDescription></div>
                  </div>
                  <div className="flex gap-1"><button onClick={() => openEditMember(m)} className="text-slate-400 hover:text-teal-600 p-1"><Pencil className="h-4 w-4" /></button><button onClick={() => deleteMember(m)} className="text-slate-400 hover:text-red-600 p-1"><Trash2 className="h-4 w-4" /></button></div>
                </div>
              </CardHeader>
              <CardContent className="pb-3">
                <div className="flex items-center gap-2 text-sm text-slate-600 mb-2">{ageIcon(m.age)}<span className="font-medium">{m.age} tahun</span></div>
                {m.age < 4 ? (<Badge variant="outline" className="text-slate-500">Asesmen tersedia usia 4+ tahun</Badge>) : (
                  <div className="flex flex-wrap gap-1">{m.instruments.map(i => <Badge key={i.code} variant="outline" className="bg-cyan-50 text-cyan-700 border-cyan-200">{i.name.split(' ')[0].replace('-', '')}</Badge>)}</div>
                )}
              </CardContent>
              <CardFooter className="gap-2">
                <Button size="sm" className="flex-1 bg-teal-600 hover:bg-teal-700" disabled={m.age < 4} onClick={() => startAssessment(m)}><ClipboardList className="h-4 w-4 mr-1" /> Asesmen</Button>
                <Button size="sm" variant="outline" onClick={() => openHistory(m)}><TrendingUp className="h-4 w-4 mr-1" /> Riwayat</Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

function SelectInstrument({ activeMember, loadQuestionnaire, setView }) {
  return (
    <div className="max-w-2xl mx-auto">
      <Button variant="ghost" size="sm" onClick={() => setView('dashboard')} className="mb-4"><ArrowLeft className="h-4 w-4 mr-1" /> Kembali</Button>
      <h2 className="text-xl font-bold text-slate-800">Pilih Instrumen Asesmen</h2>
      <p className="text-slate-500 mb-6">Untuk {activeMember.fullName} ({activeMember.age} tahun). Silakan pilih kuesioner.</p>
      <div className="grid gap-4">
        {activeMember.instruments.map(i => (
          <Card key={i.code} className="cursor-pointer hover:shadow-md hover:border-teal-400 transition-all" onClick={() => loadQuestionnaire(activeMember, i.code)}>
            <CardContent className="flex items-center gap-4 py-5">
              <div className="bg-teal-100 text-teal-700 rounded-lg p-3">{i.code === 'phq9' ? <HeartPulse className="h-6 w-6" /> : <Activity className="h-6 w-6" />}</div>
              <div className="flex-1"><div className="font-semibold text-slate-800">{i.name}</div><div className="text-sm text-slate-500">{i.code === 'phq9' ? '9 pernyataan • Skrining tingkat keparahan depresi' : '12 pernyataan • Kesehatan mental umum & distres psikologis'}</div></div>
              <ArrowLeft className="h-5 w-5 text-slate-300 rotate-180" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

function Assessment({ questionnaire, activeMember, answers, setAnswers, answeredCount, totalItems, progressPct, submitAssessment, setView, loading }) {
  return (
    <div className="max-w-3xl mx-auto">
      <Button variant="ghost" size="sm" onClick={() => setView('dashboard')} className="mb-4"><ArrowLeft className="h-4 w-4 mr-1" /> Batal</Button>
      <Card className="mb-4 sticky top-2 z-10">
        <CardContent className="py-4">
          <div className="flex items-center justify-between mb-2"><div><div className="font-bold text-slate-800">{questionnaire.name}</div><div className="text-sm text-slate-500">{activeMember.fullName} • {activeMember.age} tahun</div></div><div className="text-sm font-semibold text-teal-600">{answeredCount}/{totalItems}</div></div>
          <Progress value={progressPct} className="h-2" />
          <p className="text-xs text-slate-500 mt-2">{questionnaire.instruction}</p>
        </CardContent>
      </Card>
      <div className="space-y-3">
        {questionnaire.items.map((item, idx) => (
          <Card key={item.id} className={answers[item.id] !== undefined ? 'border-teal-200 bg-teal-50/30' : ''}>
            <CardContent className="py-4">
              <div className="flex gap-3 mb-3"><span className="flex-shrink-0 h-6 w-6 rounded-full bg-slate-200 text-slate-600 text-xs font-bold flex items-center justify-center">{idx + 1}</span><p className="text-slate-800 font-medium">{item.text}</p></div>
              <RadioGroup value={answers[item.id]?.toString()} onValueChange={v => setAnswers({ ...answers, [item.id]: Number(v) })} className="grid gap-2 sm:grid-cols-2 pl-9">
                {questionnaire.options.map(opt => (
                  <label key={opt.value} htmlFor={`q${item.id}-${opt.value}`} className={`flex items-center gap-2 rounded-md border px-3 py-2 cursor-pointer text-sm transition-colors ${answers[item.id] === opt.value ? 'border-teal-500 bg-teal-100/50 text-teal-800' : 'border-slate-200 hover:bg-slate-50'}`}>
                    <RadioGroupItem value={opt.value.toString()} id={`q${item.id}-${opt.value}`} />
                    <span>{opt.label}</span>
                  </label>
                ))}
              </RadioGroup>
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="sticky bottom-4 mt-6">
        <Button onClick={submitAssessment} disabled={loading} className="w-full h-12 text-base bg-teal-600 hover:bg-teal-700 shadow-lg">{loading ? 'Menghitung...' : `Lihat Hasil (${answeredCount}/${totalItems})`}</Button>
      </div>
    </div>
  )
}

function ResultView({ result, setView, printReport, openHistory }) {
  const r = result.result
  const lvl = catLevel(r.overallCategory)
  const banner = lvl === 'ok' ? 'from-emerald-500 to-teal-600' : lvl === 'warn' ? 'from-amber-500 to-orange-500' : 'from-red-500 to-rose-600'
  return (
    <div className="max-w-3xl mx-auto">
      <Button variant="ghost" size="sm" onClick={() => setView('dashboard')} className="mb-4"><ArrowLeft className="h-4 w-4 mr-1" /> Dashboard</Button>
      <div className={`rounded-xl bg-gradient-to-r ${banner} text-white p-6 mb-5 shadow`}>
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div><div className="text-sm opacity-90">{result.instrumentName}</div><h2 className="text-2xl font-bold">{result.memberName} • {result.memberAge} th</h2><div className="text-sm opacity-90 mt-1">{new Date(result.createdAt).toLocaleString('id-ID')}</div></div>
          <div className="text-right"><div className="text-sm opacity-90">Kategori Hasil</div><div className="text-2xl font-bold">{r.overallCategory}</div></div>
        </div>
      </div>

      {r.suicideRisk && (<Card className="mb-5 border-red-300 bg-red-50"><CardContent className="py-4 flex gap-3"><ShieldAlert className="h-6 w-6 text-red-600 flex-shrink-0" /><div><div className="font-bold text-red-700">Peringatan Risiko Tinggi</div><p className="text-sm text-red-600">Terdeteksi indikasi pikiran menyakiti diri (PHQ-9 item 9). Mohon segera hubungi kontak darurat. Hotline SEJIWA/Kemenkes: <b>119 ext 8</b>.</p></div></CardContent></Card>)}

      <Card className="mb-5">
        <CardHeader><CardTitle className="text-lg flex items-center gap-2"><FileText className="h-5 w-5 text-teal-600" /> Rincian Skor</CardTitle></CardHeader>
        <CardContent>
          {r.family === 'sdq' && (
            <Table>
              <TableHeader><TableRow><TableHead>Aspek</TableHead><TableHead className="text-center">Skor</TableHead><TableHead className="text-center">Kategori</TableHead></TableRow></TableHeader>
              <TableBody>
                {r.subDetail.map(s => (<TableRow key={s.key}><TableCell>{s.name}</TableCell><TableCell className="text-center font-medium">{s.score}</TableCell><TableCell className="text-center"><CatBadge cat={s.category} /></TableCell></TableRow>))}
                <TableRow className="bg-slate-50 font-semibold"><TableCell>Total Kesulitan (E+C+H+P)</TableCell><TableCell className="text-center">{r.totalDifficulties} / 40</TableCell><TableCell className="text-center"><CatBadge cat={r.totalCategory} /></TableCell></TableRow>
              </TableBody>
            </Table>
          )}
          {r.family === 'phq9' && (
            <div className="space-y-3">
              <ScoreRow label="Total Skor PHQ-9" value={`${r.total} / 27`} badge={r.severity} />
              <ScoreRow label="Item 9 (Pikiran melukai diri)" value={r.item9} badge={r.item9 > 0 ? 'Perlu Perhatian' : 'Aman'} />
            </div>
          )}
          {r.family === 'ghq12' && (
            <div className="space-y-3">
              <ScoreRow label="Total Skor GHQ-12" value={`${r.total} / 36`} badge={r.overallCategory} />
              <ScoreRow label="Distres Psikologis" value={`${r.distress} / 18`} />
              <ScoreRow label="Disfungsi Sosial" value={`${r.dysfunction} / 18`} />
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="mb-5">
        <CardHeader><CardTitle className="text-lg flex items-center gap-2"><Heart className="h-5 w-5 text-teal-600" /> Rekomendasi</CardTitle></CardHeader>
        <CardContent><ul className="space-y-2">{r.recommendations.map((rec, i) => (<li key={i} className="flex gap-2 text-slate-700"><span className="text-teal-500 mt-1">•</span><span className="text-sm">{rec}</span></li>))}</ul>
          <p className="text-xs text-slate-400 mt-4">Hasil ini adalah skrining awal, bukan diagnosis klinis. Konsultasikan dengan tenaga profesional untuk kepastian.</p>
        </CardContent>
      </Card>

      <div className="flex gap-2 flex-wrap">
        <Button onClick={printReport} className="bg-teal-600 hover:bg-teal-700"><FileText className="h-4 w-4 mr-1" /> Unduh PDF</Button>
        <Button variant="outline" onClick={() => openHistory({ id: result.memberId, fullName: result.memberName, age: result.memberAge })}><TrendingUp className="h-4 w-4 mr-1" /> Lihat Riwayat</Button>
        <Button variant="outline" onClick={() => setView('dashboard')}>Selesai</Button>
      </div>
    </div>
  )
}
function ScoreRow({ label, value, badge }) {
  return <div className="flex items-center justify-between border-b pb-2"><span className="text-slate-600">{label}</span><div className="flex items-center gap-3"><span className="font-semibold text-slate-800">{value}</span>{badge && <CatBadge cat={badge} />}</div></div>
}

function HistoryView({ activeMember, history, setView, viewResult, startAssessment }) {
  const chartData = useMemo(() => [...history].reverse().map(h => ({ date: new Date(h.createdAt).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' }), skor: h.result.trendScore })), [history])
  return (
    <div className="max-w-4xl mx-auto">
      <Button variant="ghost" size="sm" onClick={() => setView('dashboard')} className="mb-4"><ArrowLeft className="h-4 w-4 mr-1" /> Dashboard</Button>
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div><h2 className="text-2xl font-bold text-slate-800">Riwayat Asesmen</h2><p className="text-slate-500">{activeMember.fullName} • {activeMember.age} tahun</p></div>
        {activeMember.instruments && <Button className="bg-teal-600 hover:bg-teal-700" onClick={() => startAssessment(activeMember)}><Plus className="h-4 w-4 mr-1" /> Asesmen Baru</Button>}
      </div>
      {history.length === 0 ? (
        <Card className="border-dashed"><CardContent className="py-16 text-center text-slate-500"><ClipboardList className="h-10 w-10 mx-auto mb-2 text-slate-300" />Belum ada riwayat asesmen.</CardContent></Card>
      ) : (
        <>
          {chartData.length >= 2 && (
            <Card className="mb-5"><CardHeader><CardTitle className="text-lg flex items-center gap-2"><TrendingUp className="h-5 w-5 text-teal-600" /> Grafik Tren Skor</CardTitle></CardHeader>
              <CardContent><div style={{ width: '100%', height: 260 }}><ResponsiveContainer><LineChart data={chartData}><CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" /><XAxis dataKey="date" fontSize={12} /><YAxis fontSize={12} /><Tooltip /><Line type="monotone" dataKey="skor" stroke="#0d9488" strokeWidth={2} dot={{ r: 4 }} /></LineChart></ResponsiveContainer></div></CardContent>
            </Card>
          )}
          <Card>
            <CardHeader><CardTitle className="text-lg">Daftar Asesmen</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader><TableRow><TableHead>Tanggal</TableHead><TableHead>Instrumen</TableHead><TableHead className="text-center">Skor</TableHead><TableHead className="text-center">Kategori</TableHead><TableHead></TableHead></TableRow></TableHeader>
                <TableBody>
                  {history.map(h => (
                    <TableRow key={h.id}>
                      <TableCell className="text-sm">{new Date(h.createdAt).toLocaleDateString('id-ID')}</TableCell>
                      <TableCell className="text-sm">{h.instrumentName}{h.result.redFlag && <AlertTriangle className="inline h-4 w-4 text-red-500 ml-1" />}</TableCell>
                      <TableCell className="text-center font-medium">{h.result.trendScore}</TableCell>
                      <TableCell className="text-center"><CatBadge cat={h.result.overallCategory} /></TableCell>
                      <TableCell className="text-right"><Button size="sm" variant="outline" onClick={() => viewResult(h.id)}>Lihat</Button></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}

function MemberDialog({ memberDialog, setMemberDialog, mf, setMf, saveMember, editingMember }) {
  return (
    <Dialog open={memberDialog} onOpenChange={setMemberDialog}>
      <DialogContent>
        <DialogHeader><DialogTitle>{editingMember ? 'Ubah Profil' : 'Tambah Anggota Keluarga'}</DialogTitle><DialogDescription>Usia akan dihitung otomatis dari tanggal lahir untuk menentukan kuesioner.</DialogDescription></DialogHeader>
        <form onSubmit={saveMember} className="space-y-4">
          <div><Label>Nama Lengkap</Label><Input value={mf.fullName} onChange={e => setMf({ ...mf, fullName: e.target.value })} required /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><Label>Jenis Kelamin</Label>
              <Select value={mf.gender} onValueChange={v => setMf({ ...mf, gender: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="Laki-laki">Laki-laki</SelectItem><SelectItem value="Perempuan">Perempuan</SelectItem></SelectContent></Select>
            </div>
            <div><Label>Tanggal Lahir</Label><Input type="date" value={mf.dob} onChange={e => setMf({ ...mf, dob: e.target.value })} required /></div>
          </div>
          <div><Label>Hubungan Keluarga</Label>
            <Select value={mf.relationship} onValueChange={v => setMf({ ...mf, relationship: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{REL_OPTS.map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}</SelectContent></Select>
          </div>
          <DialogFooter><Button type="submit" className="bg-teal-600 hover:bg-teal-700">{editingMember ? 'Simpan Perubahan' : 'Tambah'}</Button></DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function EmergencyDialog({ emergencyOpen, setEmergencyOpen, referrals }) {
  return (
    <AlertDialog open={emergencyOpen} onOpenChange={setEmergencyOpen}>
      <AlertDialogContent className="border-red-300">
        <AlertDialogHeader>
          <div className="mx-auto bg-red-100 rounded-full p-3 mb-2"><ShieldAlert className="h-8 w-8 text-red-600" /></div>
          <AlertDialogTitle className="text-center text-red-700">Anda Tidak Sendirian</AlertDialogTitle>
          <AlertDialogDescription className="text-center">Jawaban Anda menunjukkan Anda mungkin sedang mengalami masa yang sangat berat. Mohon segera hubungi salah satu kontak berikut. Bantuan tersedia.</AlertDialogDescription>
        </AlertDialogHeader>
        <div className="space-y-2">
          {referrals.map(r => (
            <div key={r.id} className="flex items-center gap-3 rounded-lg border border-red-100 bg-red-50 p-3">
              <Phone className="h-5 w-5 text-red-600 flex-shrink-0" />
              <div className="flex-1"><div className="font-semibold text-slate-800">{r.name}</div><div className="text-xs text-slate-500">{r.note}</div></div>
              <div className="font-bold text-red-700">{r.contact}</div>
            </div>
          ))}
        </div>
        <AlertDialogFooter><AlertDialogAction className="w-full bg-red-600 hover:bg-red-700">Saya Mengerti</AlertDialogAction></AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

// ==================== ADMIN PANEL ====================
const ROLE_LABEL = { super_admin: 'Super Admin', admin_medis: 'Admin Medis / Psikolog', admin_teknis: 'Admin Teknis' }
const SEV_CLS = { Kritis: 'bg-red-600 text-white', Tinggi: 'bg-red-100 text-red-700 border-red-200', Sedang: 'bg-amber-100 text-amber-700 border-amber-200' }
const STATUS_CLS = { New: 'bg-red-100 text-red-700', 'Under Review': 'bg-amber-100 text-amber-700', Referred: 'bg-blue-100 text-blue-700', Resolved: 'bg-emerald-100 text-emerald-700' }
const SUB_NAMES_CLIENT = { E: 'Emosional (E)', C: 'Perilaku (C)', H: 'Hiperaktivitas (H)', P: 'Teman Sebaya (P)' }

function AdminPanel({ user, token, logout }) {
  const [tab, setTab] = useState('dashboard')
  const aapi = (path, opts = {}) => api(path, { ...opts, token })
  return (
    <div className="min-h-screen bg-slate-50">
      <Toaster position="top-center" richColors />
      <header className="bg-slate-900 text-white shadow-md">
        <div className="container flex items-center justify-between py-4">
          <div className="flex items-center gap-2">
            <div className="bg-teal-500/20 rounded-lg p-2"><ShieldCheck className="h-6 w-6 text-teal-400" /></div>
            <div><div className="font-bold text-lg leading-none">SIAP Admin</div><div className="text-xs text-slate-300">Panel Administrasi Sistem</div></div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block"><div className="text-sm font-medium">{user.name}</div><Badge className="bg-teal-500/20 text-teal-300 border-0 text-[10px]">{ROLE_LABEL[user.role] || user.role}</Badge></div>
            <Button variant="secondary" size="sm" onClick={logout}><LogOut className="h-4 w-4 mr-1" /> Keluar</Button>
          </div>
        </div>
      </header>
      <div className="container py-6">
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="mb-6 flex-wrap h-auto">
            <TabsTrigger value="dashboard"><LayoutDashboard className="h-4 w-4 mr-1" /> Dashboard</TabsTrigger>
            <TabsTrigger value="alerts"><Bell className="h-4 w-4 mr-1" /> Red Flag Alerts</TabsTrigger>
            <TabsTrigger value="kuesioner"><ListChecks className="h-4 w-4 mr-1" /> Master Kuesioner</TabsTrigger>
            <TabsTrigger value="usia"><Settings className="h-4 w-4 mr-1" /> Aturan Usia</TabsTrigger>
            <TabsTrigger value="users"><UserCog className="h-4 w-4 mr-1" /> Manajemen User</TabsTrigger>
            <TabsTrigger value="rujukan"><BookUser className="h-4 w-4 mr-1" /> Rujukan</TabsTrigger>
            <TabsTrigger value="log"><ScrollText className="h-4 w-4 mr-1" /> Audit Log</TabsTrigger>
          </TabsList>
          <TabsContent value="dashboard"><AdminDashboard aapi={aapi} /></TabsContent>
          <TabsContent value="alerts"><AdminAlerts aapi={aapi} /></TabsContent>
          <TabsContent value="kuesioner"><AdminInstruments aapi={aapi} /></TabsContent>
          <TabsContent value="usia"><AdminAgeRules aapi={aapi} /></TabsContent>
          <TabsContent value="users"><AdminUsers aapi={aapi} /></TabsContent>
          <TabsContent value="rujukan"><AdminReferrals aapi={aapi} /></TabsContent>
          <TabsContent value="log"><AdminLogs aapi={aapi} /></TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, cls }) {
  return <Card><CardContent className="py-5 flex items-center gap-4"><div className={`rounded-lg p-3 ${cls}`}>{icon}</div><div><div className="text-2xl font-bold text-slate-800">{value}</div><div className="text-sm text-slate-500">{label}</div></div></CardContent></Card>
}

function AdminDashboard({ aapi }) {
  const [stats, setStats] = useState(null)
  const [range, setRange] = useState('daily')
  useEffect(() => {
    let active = true
    const load = () => aapi(`/admin/stats?range=${range}`).then(d => { if (active) setStats(d) }).catch(() => {})
    load(); const t = setInterval(load, 15000)
    return () => { active = false; clearInterval(t) }
  }, [range])
  if (!stats) return <div className="text-slate-500">Memuat statistik...</div>
  const distData = [
    { name: 'Normal', value: stats.distribution.Normal, fill: '#10b981' },
    { name: 'Ambang', value: stats.distribution.Ambang, fill: '#f59e0b' },
    { name: 'Abnormal', value: stats.distribution.Abnormal, fill: '#ef4444' },
  ]
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={<ClipboardList className="h-6 w-6 text-teal-600" />} label="Total Asesmen" value={stats.total} cls="bg-teal-100" />
        <StatCard icon={<ShieldAlert className="h-6 w-6 text-red-600" />} label="Alert Baru (belum ditangani)" value={stats.newAlerts} cls="bg-red-100" />
        <StatCard icon={<Users className="h-6 w-6 text-blue-600" />} label="User Terdaftar" value={stats.totalUsers} cls="bg-blue-100" />
        <StatCard icon={<Heart className="h-6 w-6 text-cyan-600" />} label="Anggota Keluarga" value={stats.totalMembers} cls="bg-cyan-100" />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card><CardHeader><div className="flex items-center justify-between gap-2"><CardTitle className="text-base flex items-center gap-2"><TrendingUp className="h-5 w-5 text-teal-600" /> Tren Asesmen</CardTitle><Select value={range} onValueChange={setRange}><SelectTrigger className="w-32 h-8 text-xs"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="daily">Harian (14 hari)</SelectItem><SelectItem value="weekly">Mingguan (8 mgg)</SelectItem><SelectItem value="monthly">Bulanan (6 bln)</SelectItem></SelectContent></Select></div></CardHeader>
          <CardContent><div style={{ width: '100%', height: 240 }}><ResponsiveContainer><LineChart data={stats.trend}><CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" /><XAxis dataKey="date" fontSize={11} /><YAxis fontSize={11} allowDecimals={false} /><Tooltip /><Line type="monotone" dataKey="count" stroke="#0d9488" strokeWidth={2} dot={{ r: 3 }} /></LineChart></ResponsiveContainer></div></CardContent>
        </Card>
        <Card><CardHeader><CardTitle className="text-base flex items-center gap-2"><Activity className="h-5 w-5 text-teal-600" /> Distribusi Kategori Hasil</CardTitle></CardHeader>
          <CardContent><div style={{ width: '100%', height: 240 }}><ResponsiveContainer><BarChart data={distData}><CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" /><XAxis dataKey="name" fontSize={11} /><YAxis fontSize={11} allowDecimals={false} /><Tooltip /><Bar dataKey="value" radius={[6, 6, 0, 0]}>{distData.map((e, i) => <Cell key={i} fill={e.fill} />)}</Bar></BarChart></ResponsiveContainer></div></CardContent>
        </Card>
      </div>
      <Card><CardHeader><CardTitle className="text-base">Status Penanganan Alert</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {Object.entries(stats.alertStatus).map(([k, v]) => (<div key={k} className={`rounded-lg p-3 text-center ${STATUS_CLS[k]}`}><div className="text-2xl font-bold">{v}</div><div className="text-xs">{k}</div></div>))}
        </CardContent>
      </Card>
    </div>
  )
}

function AdminAlerts({ aapi }) {
  const [alerts, setAlerts] = useState([])
  const [filter, setFilter] = useState('all')
  const [detail, setDetail] = useState(null)
  const load = () => aapi(`/admin/alerts?status=${filter}`).then(setAlerts).catch(e => toast.error(e.message))
  useEffect(() => { load(); const t = setInterval(load, 15000); return () => clearInterval(t) }, [filter])
  async function changeStatus(id, status) {
    try { await aapi(`/admin/alerts/${id}`, { method: 'PATCH', body: { status } }); toast.success('Status diperbarui'); load() } catch (e) { toast.error(e.message) }
  }
  async function openDetail(id) { try { const d = await aapi(`/admin/alerts/${id}`); setDetail(d) } catch (e) { toast.error(e.message) } }
  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div><h3 className="text-lg font-bold text-slate-800 flex items-center gap-2"><ShieldAlert className="h-5 w-5 text-red-600" /> Red Flag Alert System</h3><p className="text-sm text-slate-500">Diperbarui otomatis tiap 15 detik.</p></div>
        <div className="flex items-center gap-2">
          <Select value={filter} onValueChange={setFilter}><SelectTrigger className="w-44"><SelectValue /></SelectTrigger><SelectContent>{['all', 'New', 'Under Review', 'Referred', 'Resolved'].map(s => <SelectItem key={s} value={s}>{s === 'all' ? 'Semua Status' : s}</SelectItem>)}</SelectContent></Select>
          <Button variant="outline" size="sm" onClick={load}><RefreshCw className="h-4 w-4" /></Button>
        </div>
      </div>
      <Card><CardContent className="p-0">
        <Table>
          <TableHeader><TableRow><TableHead>Waktu</TableHead><TableHead>Pasien</TableHead><TableHead>Instrumen</TableHead><TableHead>Tipe Risiko</TableHead><TableHead className="text-center">Severity</TableHead><TableHead>Status</TableHead><TableHead></TableHead></TableRow></TableHeader>
          <TableBody>
            {alerts.length === 0 ? (<TableRow><TableCell colSpan={7} className="text-center text-slate-400 py-8">Tidak ada alert.</TableCell></TableRow>) : alerts.map(a => (
              <TableRow key={a.id} className={a.status === 'New' ? 'bg-red-50/40' : ''}>
                <TableCell className="text-xs whitespace-nowrap">{new Date(a.createdAt).toLocaleString('id-ID')}</TableCell>
                <TableCell className="text-sm font-medium">{a.memberName}<div className="text-xs text-slate-400">{a.memberAge} th • {a.userEmail}</div></TableCell>
                <TableCell className="text-sm">{a.instrumentName}</TableCell>
                <TableCell className="text-sm">{a.type}</TableCell>
                <TableCell className="text-center"><span className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-semibold ${SEV_CLS[a.severity] || 'bg-slate-100'}`}>{a.severity}</span></TableCell>
                <TableCell><Select value={a.status} onValueChange={v => changeStatus(a.id, v)}><SelectTrigger className={`w-36 h-8 text-xs ${STATUS_CLS[a.status]}`}><SelectValue /></SelectTrigger><SelectContent>{['New', 'Under Review', 'Referred', 'Resolved'].map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select></TableCell>
                <TableCell><Button size="sm" variant="outline" onClick={() => openDetail(a.id)}>Detail</Button></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent></Card>
      <Dialog open={!!detail} onOpenChange={o => !o && setDetail(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Detail Alert</DialogTitle></DialogHeader>
          {detail && (<div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-slate-500">Pasien</span><span className="font-medium">{detail.memberName} ({detail.memberAge} th)</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Kontak User</span><span>{detail.userEmail}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Instrumen</span><span>{detail.instrumentName}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Tipe</span><span className="font-medium text-red-600">{detail.type}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Kategori Hasil</span><CatBadge cat={detail.category} /></div>
            {detail.assessment && (<div className="mt-3 rounded-lg bg-slate-50 p-3"><div className="font-semibold mb-1">Rekomendasi Otomatis</div><ul className="list-disc pl-4 space-y-1 text-slate-600">{detail.assessment.result.recommendations.map((r, i) => <li key={i}>{r}</li>)}</ul></div>)}
          </div>)}
        </DialogContent>
      </Dialog>
    </div>
  )
}

function NumPair({ label, arr, onChange }) {
  return <div className="flex items-center gap-2"><span className="text-sm text-slate-600 w-40">{label}</span><Input type="number" className="w-20 h-8" value={arr[0]} onChange={e => onChange([Number(e.target.value), arr[1]])} /><span className="text-slate-400">/</span><Input type="number" className="w-20 h-8" value={arr[1]} onChange={e => onChange([arr[0], Number(e.target.value)])} /></div>
}

function AdminInstruments({ aapi }) {
  const [list, setList] = useState([])
  const [code, setCode] = useState(null)
  const [inst, setInst] = useState(null)
  const [saving, setSaving] = useState(false)
  useEffect(() => { aapi('/admin/instruments').then(l => { setList(l); if (l[0]) selectInst(l[0].code) }).catch(e => toast.error(e.message)) }, [])
  function selectInst(c) { setCode(c); aapi(`/admin/instruments/${c}`).then(setInst).catch(e => toast.error(e.message)) }
  function upd(patch) { setInst(prev => ({ ...prev, ...patch })) }
  function updItem(idx, patch) { setInst(prev => ({ ...prev, items: prev.items.map((it, i) => i === idx ? { ...it, ...patch } : it) })) }
  async function save() {
    try { setSaving(true); await aapi(`/admin/instruments/${code}`, { method: 'PUT', body: inst }); toast.success('Kuesioner disimpan') } catch (e) { toast.error(e.message) } finally { setSaving(false) }
  }
  return (
    <div>
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <h3 className="text-lg font-bold text-slate-800">Master Kuesioner &amp; Skoring</h3>
        <Select value={code || ''} onValueChange={selectInst}><SelectTrigger className="w-72"><SelectValue placeholder="Pilih instrumen" /></SelectTrigger><SelectContent>{list.map(i => <SelectItem key={i.code} value={i.code}>{i.name}</SelectItem>)}</SelectContent></Select>
        {inst && <Button onClick={save} disabled={saving} className="bg-teal-600 hover:bg-teal-700 ml-auto"><Save className="h-4 w-4 mr-1" /> {saving ? 'Menyimpan...' : 'Simpan Perubahan'}</Button>}
      </div>
      {!inst ? <div className="text-slate-500">Memuat...</div> : (
        <div className="space-y-5">
          <Card><CardContent className="py-4 space-y-3">
            <div><Label>Nama Instrumen</Label><Input value={inst.name} onChange={e => upd({ name: e.target.value })} /></div>
            <div><Label>Instruksi</Label><Textarea value={inst.instruction} onChange={e => upd({ instruction: e.target.value })} /></div>
          </CardContent></Card>

          <Card><CardHeader><CardTitle className="text-base">Daftar Soal ({inst.items.length})</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {inst.items.map((it, idx) => (
                <div key={it.id} className="flex items-start gap-2 border-b pb-2">
                  <span className="text-xs font-bold text-slate-400 w-6 pt-2">{it.id}</span>
                  <Textarea value={it.text} onChange={e => updItem(idx, { text: e.target.value })} className="flex-1 min-h-[38px]" rows={1} />
                  {inst.family === 'sdq' && (<><Select value={it.sub} onValueChange={v => updItem(idx, { sub: v })}><SelectTrigger className="w-20 h-9"><SelectValue /></SelectTrigger><SelectContent>{['E', 'C', 'H', 'P', 'Pr'].map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select><label className="flex items-center gap-1 text-xs text-slate-500 pt-2 whitespace-nowrap"><input type="checkbox" checked={!!it.reversed} onChange={e => updItem(idx, { reversed: e.target.checked })} /> reversed</label></>)}
                  {inst.family === 'ghq12' && (<Select value={it.sub} onValueChange={v => updItem(idx, { sub: v })}><SelectTrigger className="w-24 h-9"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="D">Distres</SelectItem><SelectItem value="S">Sosial</SelectItem></SelectContent></Select>)}
                </div>
              ))}
            </CardContent>
          </Card>

          {inst.family === 'sdq' && (
            <Card><CardHeader><CardTitle className="text-base">Batas Skor (Cutoff) — [Normal maks / Ambang maks]</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {['E', 'C', 'H', 'P', 'total'].map(k => <NumPair key={k} label={k === 'total' ? 'Total Kesulitan' : SUB_NAMES_CLIENT[k]} arr={inst.cutoffs[k]} onChange={v => upd({ cutoffs: { ...inst.cutoffs, [k]: v } })} />)}
                <NumPair label="Prososial [Normal min / Ambang nilai]" arr={inst.cutoffs.prosocial} onChange={v => upd({ cutoffs: { ...inst.cutoffs, prosocial: v } })} />
              </CardContent>
            </Card>
          )}
          {inst.family === 'sdq' && (
            <Card><CardHeader><CardTitle className="text-base">Teks Rekomendasi</CardTitle></CardHeader>
              <CardContent className="space-y-3">{['Normal', 'Ambang', 'Abnormal'].map(k => <div key={k}><Label>{k}</Label><Textarea value={inst.recommendations[k]} onChange={e => upd({ recommendations: { ...inst.recommendations, [k]: e.target.value } })} /></div>)}</CardContent>
            </Card>
          )}
          {inst.family === 'phq9' && (
            <Card><CardHeader><CardTitle className="text-base">Batas Keparahan (Cutoff) &amp; Rekomendasi</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                <div className="text-xs text-slate-500 mb-1 flex items-center gap-2">Item Red Flag (bunuh diri): No. <Input type="number" value={inst.suicideItem} onChange={e => upd({ suicideItem: Number(e.target.value) })} className="w-16 h-7" /></div>
                {inst.severityBands.map((b, i) => (
                  <div key={i} className="flex items-center gap-2 border-b pb-2">
                    <span className="text-xs text-slate-500 w-14">≤ skor</span>
                    <Input type="number" className="w-20 h-8" value={b.max} onChange={e => { const sb = [...inst.severityBands]; sb[i] = { ...b, max: Number(e.target.value) }; upd({ severityBands: sb }) }} />
                    <Input className="w-32 h-8" value={b.label} onChange={e => { const sb = [...inst.severityBands]; sb[i] = { ...b, label: e.target.value }; upd({ severityBands: sb }) }} />
                    <Textarea className="flex-1 min-h-[36px]" rows={1} value={b.rec} onChange={e => { const sb = [...inst.severityBands]; sb[i] = { ...b, rec: e.target.value }; upd({ severityBands: sb }) }} />
                  </div>
                ))}
                <div><Label>Kategori yang memicu Red Flag (pisahkan koma)</Label><Input value={(inst.redFlagSeverities || []).join(', ')} onChange={e => upd({ redFlagSeverities: e.target.value.split(',').map(s => s.trim()).filter(Boolean) })} /></div>
              </CardContent>
            </Card>
          )}
          {inst.family === 'ghq12' && (
            <Card><CardHeader><CardTitle className="text-base">Ambang &amp; Rekomendasi</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-2"><Label className="w-40">Ambang Skor Total</Label><Input type="number" className="w-24 h-8" value={inst.threshold} onChange={e => upd({ threshold: Number(e.target.value) })} /></div>
                <div><Label>Rekomendasi (Ada Masalah)</Label><Textarea value={inst.recommendations.problem} onChange={e => upd({ recommendations: { ...inst.recommendations, problem: e.target.value } })} /></div>
                <div><Label>Rekomendasi (Normal)</Label><Textarea value={inst.recommendations.normal} onChange={e => upd({ recommendations: { ...inst.recommendations, normal: e.target.value } })} /></div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

function AdminAgeRules({ aapi }) {
  const [rules, setRules] = useState(null)
  useEffect(() => { aapi('/admin/age-rules').then(d => setRules(d.rules)).catch(e => toast.error(e.message)) }, [])
  function updRule(i, patch) { setRules(rules.map((r, idx) => idx === i ? { ...r, ...patch } : r)) }
  function addRule() { setRules([...rules, { minAge: 0, maxAge: 0, codes: [], label: '' }]) }
  function delRule(i) { setRules(rules.filter((_, idx) => idx !== i)) }
  async function save() { try { await aapi('/admin/age-rules', { method: 'PUT', body: { rules } }); toast.success('Aturan usia disimpan') } catch (e) { toast.error(e.message) } }
  if (!rules) return <div className="text-slate-500">Memuat...</div>
  return (
    <div>
      <div className="flex items-center justify-between mb-4"><h3 className="text-lg font-bold text-slate-800">Aturan Routing Berdasarkan Usia</h3><div className="flex gap-2"><Button variant="outline" size="sm" onClick={addRule}><Plus className="h-4 w-4 mr-1" /> Aturan</Button><Button className="bg-teal-600 hover:bg-teal-700" size="sm" onClick={save}><Save className="h-4 w-4 mr-1" /> Simpan</Button></div></div>
      <Card><CardContent className="p-0"><Table>
        <TableHeader><TableRow><TableHead>Label</TableHead><TableHead>Usia Min</TableHead><TableHead>Usia Maks</TableHead><TableHead>Kode Instrumen (pisah koma)</TableHead><TableHead></TableHead></TableRow></TableHeader>
        <TableBody>{rules.map((r, i) => (
          <TableRow key={i}>
            <TableCell><Input className="h-8" value={r.label || ''} onChange={e => updRule(i, { label: e.target.value })} /></TableCell>
            <TableCell><Input type="number" className="h-8 w-20" value={r.minAge} onChange={e => updRule(i, { minAge: Number(e.target.value) })} /></TableCell>
            <TableCell><Input type="number" className="h-8 w-20" value={r.maxAge} onChange={e => updRule(i, { maxAge: Number(e.target.value) })} /></TableCell>
            <TableCell><Input className="h-8" value={(r.codes || []).join(', ')} onChange={e => updRule(i, { codes: e.target.value.split(',').map(s => s.trim()).filter(Boolean) })} /></TableCell>
            <TableCell><button onClick={() => delRule(i)} className="text-red-500"><Trash2 className="h-4 w-4" /></button></TableCell>
          </TableRow>))}</TableBody>
      </Table></CardContent></Card>
      <p className="text-xs text-slate-400 mt-2">Kode tersedia: sdq_parent, sdq_self, phq9, ghq12</p>
    </div>
  )
}

function AdminUsers({ aapi }) {
  const [users, setUsers] = useState([])
  const [resetTarget, setResetTarget] = useState(null)
  const [newPass, setNewPass] = useState('')
  const load = () => aapi('/admin/users').then(setUsers).catch(e => toast.error(e.message))
  useEffect(() => { load() }, [])
  async function toggleStatus(u) {
    const status = u.status === 'suspended' ? 'active' : 'suspended'
    try { await aapi(`/admin/users/${u.id}`, { method: 'PATCH', body: { status } }); toast.success(status === 'suspended' ? 'Akun ditangguhkan' : 'Akun diaktifkan'); load() } catch (e) { toast.error(e.message) }
  }
  async function doReset(e) {
    e.preventDefault()
    try { await aapi(`/admin/users/${resetTarget.id}/reset-password`, { method: 'POST', body: { newPassword: newPass } }); toast.success('Password direset'); setResetTarget(null); setNewPass('') } catch (e) { toast.error(e.message) }
  }
  return (
    <div>
      <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2"><UserCog className="h-5 w-5 text-teal-600" /> Manajemen User</h3>
      <Card><CardContent className="p-0"><Table>
        <TableHeader><TableRow><TableHead>Nama</TableHead><TableHead>Email</TableHead><TableHead className="text-center">Anggota</TableHead><TableHead className="text-center">Asesmen</TableHead><TableHead className="text-center">Status</TableHead><TableHead className="text-right">Aksi</TableHead></TableRow></TableHeader>
        <TableBody>{users.length === 0 ? (<TableRow><TableCell colSpan={6} className="text-center text-slate-400 py-8">Belum ada user terdaftar.</TableCell></TableRow>) : users.map(u => (
          <TableRow key={u.id} className={u.status === 'suspended' ? 'bg-red-50/40' : ''}>
            <TableCell className="font-medium">{u.name}</TableCell>
            <TableCell className="text-sm text-slate-500">{u.email}</TableCell>
            <TableCell className="text-center">{u.memberCount}</TableCell>
            <TableCell className="text-center">{u.assessmentCount}</TableCell>
            <TableCell className="text-center"><span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${u.status === 'suspended' ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'}`}>{u.status === 'suspended' ? 'Ditangguhkan' : 'Aktif'}</span></TableCell>
            <TableCell className="text-right space-x-1">
              <Button size="sm" variant="outline" onClick={() => setResetTarget(u)}><KeyRound className="h-3.5 w-3.5 mr-1" /> Reset</Button>
              {u.status === 'suspended'
                ? <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" onClick={() => toggleStatus(u)}><CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Aktifkan</Button>
                : <Button size="sm" variant="destructive" onClick={() => toggleStatus(u)}><Ban className="h-3.5 w-3.5 mr-1" /> Suspend</Button>}
            </TableCell>
          </TableRow>))}</TableBody>
      </Table></CardContent></Card>
      <Dialog open={!!resetTarget} onOpenChange={o => { if (!o) { setResetTarget(null); setNewPass('') } }}>
        <DialogContent className="max-w-sm">
          <DialogHeader><DialogTitle>Reset Password</DialogTitle><DialogDescription>{resetTarget?.email}</DialogDescription></DialogHeader>
          <form onSubmit={doReset} className="space-y-4">
            <div><Label>Password Baru</Label><Input type="text" value={newPass} onChange={e => setNewPass(e.target.value)} placeholder="Min. 4 karakter" required /></div>
            <DialogFooter><Button type="submit" className="bg-teal-600 hover:bg-teal-700">Simpan Password</Button></DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function AdminReferrals({ aapi }) {
  const [refs, setRefs] = useState([])
  const [form, setForm] = useState({ name: '', type: 'Hotline', contact: '', note: '' })
  const load = () => aapi('/admin/referrals').then(setRefs).catch(e => toast.error(e.message))
  useEffect(() => { load() }, [])
  async function add(e) {
    e.preventDefault()
    if (!form.name || !form.contact) { toast.error('Nama dan kontak wajib diisi'); return }
    try { await aapi('/admin/referrals', { method: 'POST', body: form }); toast.success('Rujukan ditambahkan'); setForm({ name: '', type: 'Hotline', contact: '', note: '' }); load() } catch (e) { toast.error(e.message) }
  }
  async function del(id) { try { await aapi(`/admin/referrals/${id}`, { method: 'DELETE' }); toast.success('Rujukan dihapus'); load() } catch (e) { toast.error(e.message) } }
  return (
    <div>
      <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2"><BookUser className="h-5 w-5 text-teal-600" /> Direktori Rujukan &amp; Kontak Darurat</h3>
      <p className="text-sm text-slate-500 mb-4">Kontak berikut otomatis ditampilkan pada layar hasil pasien berisiko tinggi (mis. terdeteksi ide bunuh diri).</p>
      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-1"><CardHeader><CardTitle className="text-base">Tambah Rujukan</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={add} className="space-y-3">
              <div><Label>Nama</Label><Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="mis. RSJ / Psikolog" /></div>
              <div><Label>Jenis</Label>
                <Select value={form.type} onValueChange={v => setForm({ ...form, type: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{['Hotline Darurat', 'Hotline', 'Klinik', 'Psikolog', 'Psikiater', 'Rumah Sakit Jiwa (RSJ)', 'Lainnya'].map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}</SelectContent></Select>
              </div>
              <div><Label>Kontak</Label><Input value={form.contact} onChange={e => setForm({ ...form, contact: e.target.value })} placeholder="Telepon / alamat" /></div>
              <div><Label>Catatan</Label><Textarea value={form.note} onChange={e => setForm({ ...form, note: e.target.value })} rows={2} /></div>
              <Button type="submit" className="w-full bg-teal-600 hover:bg-teal-700"><Plus className="h-4 w-4 mr-1" /> Tambah</Button>
            </form>
          </CardContent>
        </Card>
        <div className="lg:col-span-2 space-y-2">
          {refs.length === 0 ? <Card><CardContent className="py-10 text-center text-slate-400">Belum ada rujukan.</CardContent></Card> : refs.map(r => (
            <Card key={r.id}><CardContent className="py-3 flex items-center gap-3">
              <div className="bg-red-100 text-red-600 rounded-lg p-2"><Phone className="h-5 w-5" /></div>
              <div className="flex-1"><div className="font-semibold text-slate-800">{r.name} <Badge variant="outline" className="ml-1 text-[10px]">{r.type}</Badge></div><div className="text-xs text-slate-500">{r.note}</div></div>
              <div className="font-bold text-slate-700">{r.contact}</div>
              <button onClick={() => del(r.id)} className="text-slate-400 hover:text-red-600 ml-2"><Trash2 className="h-4 w-4" /></button>
            </CardContent></Card>
          ))}
        </div>
      </div>
    </div>
  )
}

function AdminLogs({ aapi }) {
  const [logs, setLogs] = useState([])
  useEffect(() => { aapi('/admin/audit-logs').then(setLogs).catch(e => toast.error(e.message)) }, [])
  return (
    <div>
      <h3 className="text-lg font-bold text-slate-800 mb-4">Audit Trail / Log Aktivitas</h3>
      <Card><CardContent className="p-0"><Table>
        <TableHeader><TableRow><TableHead>Waktu</TableHead><TableHead>Aktor</TableHead><TableHead>Aksi</TableHead><TableHead>Detail</TableHead></TableRow></TableHeader>
        <TableBody>{logs.length === 0 ? (<TableRow><TableCell colSpan={4} className="text-center text-slate-400 py-8">Belum ada aktivitas.</TableCell></TableRow>) : logs.map(l => (
          <TableRow key={l.id}><TableCell className="text-xs whitespace-nowrap">{new Date(l.createdAt).toLocaleString('id-ID')}</TableCell><TableCell className="text-sm">{l.actorName} <span className="text-xs text-slate-400">({l.actorRole})</span></TableCell><TableCell className="text-sm font-medium">{l.action}</TableCell><TableCell className="text-sm text-slate-500">{l.detail}</TableCell></TableRow>))}</TableBody>
      </Table></CardContent></Card>
    </div>
  )
}
