import { useState, useEffect } from 'react'
import { crmAPI, scoringAPI } from '../api'
import { LoadingSpinner, EmptyState, PageHeader, StatusBadge, ConfidenceBadge } from '../components/ui'
import { Briefcase, Search, RefreshCw, ChevronDown, ChevronRight } from 'lucide-react'

export default function Opportunities() {
  const [opps, setOpps] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState(null)
  const [scoring, setScoring] = useState(null)

  const load = async (q) => {
    setLoading(true)
    try {
      const res = await crmAPI.listOpportunities(q ? { search: q } : {})
      setOpps(Array.isArray(res.data) ? res.data : (res.data?.items || []))
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleScore = async (id, e) => {
    e.stopPropagation()
    try {
      setScoring(id)
      await scoringAPI.score(id)
      await load(search)
    } catch (err) {
      console.error(err)
    } finally {
      setScoring(null)
    }
  }

  return (
    <div>
      <PageHeader title="Opportunities" subtitle="Job postings and opportunities being tracked" />

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-5">
        <form onSubmit={(e) => { e.preventDefault(); load(search) }} className="flex gap-2">
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm pl-9" placeholder="Search opportunities..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <button className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-sm">Search</button>
        </form>
      </div>

      {loading ? <LoadingSpinner /> : opps.length === 0 ? (
        <EmptyState icon={Briefcase} title="No opportunities" description="Opportunities are discovered via daily automated lead discovery." />
      ) : (
        <div className="space-y-2">
          {opps.map(o => (
            <div key={o.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 p-0 overflow-hidden">
              <div
                className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
                onClick={() => setExpanded(expanded === o.id ? null : o.id)}
              >
                <div className="flex items-center gap-3 min-w-0">
                  {expanded === o.id ? <ChevronDown size={16} className="text-gray-400 flex-shrink-0" /> : <ChevronRight size={16} className="text-gray-400 flex-shrink-0" />}
                  <div className="min-w-0">
                    <p className="font-medium text-gray-900 truncate">{o.title}</p>
                    <p className="text-xs text-gray-500">{o.organization_name || '—'} · {o.opportunity_type} · {o.experience_level}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <ConfidenceBadge score={o.confidence_score} />
                  <StatusBadge status={o.status} />
                  <button
                    onClick={(e) => handleScore(o.id, e)}
                    disabled={scoring === o.id}
                    className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1 disabled:opacity-50"
                  >
                    {scoring === o.id ? <><RefreshCw size={12} className="animate-spin" /> Scoring...</> : 'Re-score'}
                  </button>
                </div>
              </div>

              {expanded === o.id && (
                <div className="border-t border-gray-100 p-4 bg-gray-50 grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-xs text-gray-500 font-medium mb-1">Description</p>
                    <p className="text-gray-700 text-xs line-clamp-4">{o.description || 'No description available.'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 font-medium mb-1">Details</p>
                    <div className="space-y-1 text-xs text-gray-600">
                      <p><span className="font-medium">Type:</span> {o.opportunity_type}</p>
                      <p><span className="font-medium">Exp Level:</span> {o.experience_level}</p>
                      <p><span className="font-medium">Source:</span> {o.source_name || '—'}</p>
                      <p><span className="font-medium">Discovered:</span> {o.discovered_at ? new Date(o.discovered_at).toLocaleDateString() : '—'}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 font-medium mb-1">Scoring Breakdown</p>
                    <div className="space-y-1 text-xs text-gray-600">
                      {o.score_breakdown ? Object.entries(o.score_breakdown).map(([k, v]) => (
                        <p key={k}><span className="font-medium capitalize">{k.replace(/_/g, ' ')}:</span> {v}</p>
                      )) : <p className="text-gray-400">Not scored yet</p>}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
