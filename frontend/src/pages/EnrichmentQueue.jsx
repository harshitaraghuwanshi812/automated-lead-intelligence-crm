import { useState, useEffect } from 'react'
import { enrichmentAPI } from '../api'
import { LoadingSpinner, EmptyState, PageHeader, StatusBadge, Modal } from '../components/ui'
import { Users, Zap, AlertCircle, CreditCard, ChevronRight, Check } from 'lucide-react'

const PROVIDERS = [
  { id: 'contactout', label: 'ContactOut', credits: 1, description: 'Email & LinkedIn enrichment' },
  { id: 'snov_io', label: 'Snov.io', credits: 1, description: 'Email finder & verifier' },
]

export default function EnrichmentQueue() {
  const [queue, setQueue] = useState([])
  const [loading, setLoading] = useState(true)
  const [confirmModal, setConfirmModal] = useState(null)
  const [enriching, setEnriching] = useState(null)
  const [selectedProvider, setSelectedProvider] = useState('contactout')
  const [result, setResult] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const res = await enrichmentAPI.getQueue()
      setQueue(Array.isArray(res.data) ? res.data : (res.data?.contacts || []))
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleEnrich = async () => {
    if (!confirmModal) return
    setEnriching(confirmModal.id)
    setConfirmModal(null)
    setResult(null)
    try {
      const res = await enrichmentAPI.triggerEnrichment(confirmModal.id, selectedProvider)
      setResult({ success: true, message: res.data?.message || 'Enrichment triggered successfully.' })
      await load()
    } catch (err) {
      setResult({ success: false, message: err.response?.data?.detail || 'Enrichment failed.' })
    } finally {
      setEnriching(null)
    }
  }

  return (
    <div>
      <PageHeader
        title="Enrichment Queue"
        subtitle="Contacts pending email and profile enrichment"
      />

      {result && (
        <div className={`flex items-center gap-2 p-4 rounded-lg mb-5 text-sm ${result.success ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {result.success ? <Check size={16} /> : <AlertCircle size={16} />}
          {result.message}
          <button onClick={() => setResult(null)} className="ml-auto text-xs hover:underline">Dismiss</button>
        </div>
      )}

      {loading ? <LoadingSpinner /> : queue.length === 0 ? (
        <EmptyState
          icon={Users}
          title="Queue is empty"
          description="All contacts have been enriched, or no contacts need enrichment yet."
        />
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {['Contact', 'Organization', 'Enrichment Status', 'Last Enriched', 'Actions'].map(h => (
                  <th key={h} className="text-left text-xs font-semibold text-gray-500 px-4 py-3 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {queue.map(c => (
                <tr key={c.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 bg-blue-100 rounded-full flex items-center justify-center text-xs font-bold text-blue-600">
                        {c.full_name?.[0] || 'C'}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{c.full_name}</p>
                        <p className="text-xs text-gray-400">{c.title}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-600">{c.organization_name || '—'}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={c.enrichment_status || 'pending'} />
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">
                    {c.last_enriched_at ? new Date(c.last_enriched_at).toLocaleDateString() : 'Never'}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => setConfirmModal(c)}
                      disabled={enriching === c.id}
                      className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-xs py-1 px-3 flex items-center gap-1 disabled:opacity-50"
                    >
                      <Zap size={12} />
                      {enriching === c.id ? 'Enriching...' : 'Enrich'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Credit Confirmation Modal */}
      <Modal
        open={!!confirmModal}
        onClose={() => setConfirmModal(null)}
        title="Confirm Credit Usage"
        footer={
          <>
            <button onClick={() => setConfirmModal(null)} className="bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg border border-gray-300 transition-colors cursor-pointer">Cancel</button>
            <button onClick={handleEnrich} className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">Confirm & Enrich</button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <CreditCard size={18} className="text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-amber-800">Credit Usage Notice</p>
              <p className="text-xs text-amber-600 mt-1">
                Enriching <strong>{confirmModal?.full_name}</strong> will consume provider credits.
                This action cannot be undone.
              </p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Select Provider</label>
            <div className="space-y-2">
              {PROVIDERS.map(p => (
                <label key={p.id} className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedProvider === p.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                }`}>
                  <input
                    type="radio"
                    name="provider"
                    value={p.id}
                    checked={selectedProvider === p.id}
                    onChange={() => setSelectedProvider(p.id)}
                    className="text-blue-600"
                  />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{p.label}</p>
                    <p className="text-xs text-gray-500">{p.description}</p>
                  </div>
                  <span className="text-xs text-gray-500">{p.credits} credit/lookup</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      </Modal>
    </div>
  )
}
