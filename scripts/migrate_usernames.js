// One-time migration: assign a username to old accounts that only had email.
const fs = require('fs')
const path = require('path')
const { MongoClient } = require('mongodb')

function loadEnv() {
  const envPath = path.join(__dirname, '..', '.env')
  const txt = fs.readFileSync(envPath, 'utf8')
  const out = {}
  for (const line of txt.split('\n')) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/i)
    if (m) out[m[1]] = m[2].replace(/^"|"$/g, '')
  }
  return out
}

function sanitize(base) {
  let u = (base || 'user').toLowerCase().replace(/[^a-z0-9_]/g, '')
  if (!u) u = 'user'
  return u
}

async function main() {
  const env = loadEnv()
  const client = new MongoClient(env.MONGO_URL)
  await client.connect()
  const db = client.db(env.DB_NAME)
  const users = db.collection('users')

  // existing usernames to guarantee uniqueness
  const existing = new Set()
  for (const u of await users.find({ username: { $exists: true, $ne: null } }).toArray()) {
    if (u.username) existing.add(u.username.toLowerCase())
  }

  const toMigrate = await users.find({ $or: [{ username: { $exists: false } }, { username: null }, { username: '' }] }).toArray()
  console.log(`Users needing username: ${toMigrate.length}`)

  const mapping = []
  for (const u of toMigrate) {
    let base = sanitize((u.email || '').split('@')[0] || u.name || 'user')
    let candidate = base
    let i = 1
    while (existing.has(candidate)) { candidate = `${base}${i}`; i++ }
    existing.add(candidate)
    await users.updateOne({ id: u.id || u._id }, { $set: { username: candidate } })
    mapping.push({ email: u.email || '(none)', name: u.name, username: candidate })
  }

  console.log('Migration mapping:')
  mapping.forEach(m => console.log(`  ${m.email}  ->  @${m.username}   (${m.name})`))
  console.log(`Done. Migrated ${mapping.length} account(s).`)

  const total = await users.countDocuments()
  const withUsername = await users.countDocuments({ username: { $exists: true, $ne: null } })
  console.log(`Total users: ${total}, with username: ${withUsername}`)

  await client.close()
}

main().catch(e => { console.error(e); process.exit(1) })
