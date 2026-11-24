import { useState, useEffect } from 'react'
import { suppressionAPI } from '../api'
import { LoadingSpinner, EmptyState, PageHeader, StatusBadge, Modal } from '../components/ui'
import { Shield, Plus, Search, AlertCircle, Check } from 'lucide-react'

const SUPPRESSION_REASONS = [
  { value: 'manual_block', label: 'Manual Block' },
  { value: 'unsubscribed', label: 'Unsubscribed' },
  { value: 'hard_bounce', label: 'Hard Bounce' },
  { value: 'spam_complaint', label: 'Spam Complaint' },
  { value: 'invalid_email', label: 'Invalid Email' },
]

export default function SuppressionManager() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [addModal, setAddModal] = useState(false)
  const [checkModal, setCheckModal] = useState(false)
  const [form, setForm] = useState({ value: '', suppression_type: 'email', reason: 'manual_block', notes: '' })
  const [checkEmail, setCheckEmail] = useState('')
  const [checkResult, setCheckResult] = useState(null)
  const [saving, setSaving] = useState(false)
  const [checking, setChecking] = useState(false)
  const [error, setError] = useState(null)

  const load = async (q) => {
    setLoading(true)
    try {
      const res = await suppressionAPI.list(q ? { search: q } : {})
      setEntries(Array.isArray(res.data) ? res.data : (res.data?.items || []))
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleAdd = async () => {
    setSaving(true)
    setError(null)
    try {
      await suppressionAPI.add(form)
      setAddModal(false)
      setForm({ value: '', suppression_type: 'email', reason: 'manual_block', notes: '' })
      await load(search)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to add suppression entry')
    } finally {
      setSaving(false)
    }
  }

  const handleCheck = async () => {
    if (!checkEmail) return
    setChecking(true)
    setCheckResult(null)
    try {
      const res = await suppressionAPI.check(encodeURIComponent(checkEmail))
      setCheckResult(res.data)
    } catch (e) {
      setCheckResult({ suppressed: false, error: e.response?.data?.detail })
    } finally {
      setChecking(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Suppression Management"
        subtitle="Manage unsubscribes, bounces and blocked recipients"
        actions={
          <div className="flex gap-2">
            <button onClick={() => setCheckModal(true)} className="bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg border border-gray-300 transition-colors cursor-pointer text-sm flex items-center gap-2">
              <Search size={14} /> Check Email
            </button>
            <button onClick={() => setAddModal(true)} className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center gap-2">
              <Plus size={14} /> Add Entry
            </button>
          </div>
        }
      />

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-5">
        <form onSubmit={(e) => { e.preventDefault(); load(search) }} className="flex gap-2">
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm pl-9" placeholder="Search suppression list..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <button className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-sm">Search</button>
        </form>
      </div>

      {/* Stats strip */}
      <div className="grid grid-cols-3 gap-4 mb-5">
        {[
          { label: 'Total Suppressed', value: entries.length, color: 'text-gray-900' },
          { label: 'Manual Blocks', value: entries.filter(e => e.reason === 'manual_block').length, color: 'text-red-600' },
          { label: 'Unsubscribed', value: entries.filter(e => e.reason === 'unsubscribed').length, color: 'text-orange-600' },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center py-4">
            <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-gray-500 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {loading ? <LoadingSpinner /> : entries.length === 0 ? (
        <EmptyState icon={Shield} title="Suppression list is clean" description="No suppressed addresses found." />
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {['Email / Value', 'Type', 'Reason', 'Added At', 'Notes'].map(h => (
                  <th key={h} className="text-left text-xs font-semibold text-gray-500 px-4 py-3 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {entries.map((e, i) => (
                <tr key={e.id || i} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs text-gray-800">{e.value}</td>
                  <td className="px-4 py-3"><StatusBadge status={e.suppression_type || 'email'} /></td>
                  <td className="px-4 py-3"><StatusBadge status={e.reason} label={SUPPRESSION_REASONS.find(r => r.value === e.reason)?.label || e.reason} /></td>
                  <td className="px-4 py-3 text-xs text-gray-400">
                    {e.created_at ? new Date(e.created_at).toLocaleString() : '—'}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 max-w-xs truncate">{e.notes || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Suppression Modal */}
      <Modal
        open={addModal}
        onClose={() => { setAddModal(false); setError(null) }}
        title="Add Suppression Entry"
        footer={<>
          <button onClick={() => { setAddModal(false); setError(null) }} className="bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg border border-gray-300 transition-colors cursor-pointer">Cancel</button>
          <button onClick={handleAdd} disabled={saving || !form.value} className="bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer">
            {saving ? 'Adding...' : 'Add to Suppression List'}
          </button>
        </>}
      >
        <div className="space-y-4">
          {error && <div className="text-xs text-red-600 bg-red-50 border border-red-200 p-3 rounded-lg flex gap-2"><AlertCircle size={14} />{error}</div>}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email Address *</label>
            <input className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm" value={form.value} onChange={e => setForm(f => ({ ...f, value: e.target.value }))} placeholder="user@example.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Reason</label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm" value={form.reason} onChange={e => setForm(f => ({ ...f, reason: e.target.value }))}>
              {SUPPRESSION_REASONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <input className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm" value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} placeholder="Optional reason or reference..." />
          </div>
        </div>
      </Modal>

      {/* Check Email Modal */}
      <Modal
        open={checkModal}
        onClose={() => { setCheckModal(false); setCheckResult(null); setCheckEmail('') }}
        title="Check Suppression Status"
        footer={<button onClick={() => { setCheckModal(false); setCheckResult(null); setCheckEmail('') }} className="bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg border border-gray-300 transition-colors cursor-pointer">Close</button>}
      >
        <div className="space-y-4">
          <div className="flex gap-2">
            <input
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm flex-1"
              value={checkEmail}
              onChange={e => setCheckEmail(e.target.value)}
              placeholder="user@example.com"
              onKeyDown={e => e.key === 'Enter' && handleCheck()}
            />
            <button onClick={handleCheck} disabled={checking || !checkEmail} className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
              {checking ? 'Checking...' : 'Check'}
            </button>
          </div>
          {checkResult && (
            <div className={`p-4 rounded-lg border flex items-start gap-3 ${checkResult.suppressed ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
              {checkResult.suppressed
                ? <AlertCircle size={18} className="text-red-500 flex-shrink-0 mt-0.5" />
                : <Check size={18} className="text-green-500 flex-shrink-0 mt-0.5" />}
              <div>
                <p className={`text-sm font-medium ${checkResult.suppressed ? 'text-red-800' : 'text-green-800'}`}>
                  {checkResult.suppressed ? 'SUPPRESSED — Email blocked' : 'CLEAR — Email is sendable'}
                </p>
                {checkResult.reason && <p className="text-xs text-gray-600 mt-1">Reason: {checkResult.reason}</p>}
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}
