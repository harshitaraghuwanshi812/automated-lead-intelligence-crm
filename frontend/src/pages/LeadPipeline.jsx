import { useState, useEffect } from 'react'
import { crmAPI, scoringAPI } from '../api'
import { ConfidenceBadge, StatusBadge, LoadingSpinner, EmptyState, PageHeader } from '../components/ui'
import { Zap, Search, Filter, Building2, Calendar, ExternalLink, RefreshCw } from 'lucide-react'

const EXP_FILTERS = [
  { label: 'All', value: '' },
  { label: 'Fresher / No Exp', value: 'fresher' },
  { label: '0–1 Year', value: '0_1' },
  { label: '0–2 Years', value: '0_2' },
  { label: 'Internship', value: 'internship' },
  { label: 'Hackathon', value: 'hackathon' },
]

const STAGE_COLS = ['discovered', 'enriched', 'verified', 'draft_generated', 'approved', 'sent']

export default function LeadPipeline() {
  const [view, setView] = useState('table')
  const [opps, setOpps] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [expFilter, setExpFilter] = useState('')
  const [scoreFilter, setScoreFilter] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const params = {}
      if (search) params.search = search
      if (expFilter) params.experience_level = expFilter
      const res = await crmAPI.listOpportunities(params)
      setOpps(Array.isArray(res.data) ? res.data : (res.data?.items || []))
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [expFilter])

  const handleSearch = (e) => {
    e.preventDefault()
    load()
  }

  const filtered = opps.filter(o => {
    if (!scoreFilter) return true
    const s = o.confidence_score
    if (scoreFilter === 'high') return s >= 80
    if (scoreFilter === 'medium') return s >= 60 && s < 80
    if (scoreFilter === 'low') return s < 60
    return true
  })

  const byStage = (stage) => filtered.filter(o => o.status === stage)

  return (
    <div>
      <PageHeader
        title="Lead Pipeline"
        subtitle="AI-scored opportunities from approved sources"
        actions={
          <div className="flex gap-2">
            <button
              onClick={() => setView(v => v === 'table' ? 'kanban' : 'table')}
              className="bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg border border-gray-300 transition-colors cursor-pointer text-xs"
            >
              {view === 'table' ? 'Kanban View' : 'Table View'}
            </button>
            <button onClick={load} className="bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg border border-gray-300 transition-colors cursor-pointer text-xs flex items-center gap-1">
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        }
      />

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-5">
        <div className="flex flex-wrap gap-3 items-center">
          <form onSubmit={handleSearch} className="flex gap-2 flex-1 min-w-48">
            <div className="relative flex-1">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm pl-9 text-sm"
                placeholder="Search opportunities..."
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
            <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-xs px-3">Search</button>
          </form>

          <div className="flex gap-2 flex-wrap">
            {EXP_FILTERS.map(f => (
              <button
                key={f.value}
                onClick={() => setExpFilter(f.value)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                  expFilter === f.value
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'border-gray-300 text-gray-600 hover:border-blue-400'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm w-auto text-xs"
            value={scoreFilter}
            onChange={e => setScoreFilter(e.target.value)}
          >
            <option value="">All Scores</option>
            <option value="high">High (80–100)</option>
            <option value="medium">Medium (60–79)</option>
            <option value="low">Low (&lt;60)</option>
          </select>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : view === 'table' ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  {['Title', 'Organization', 'Type', 'Experience', 'Status', 'Confidence', 'Discovered'].map(h => (
                    <th key={h} className="text-left text-xs font-semibold text-gray-500 px-4 py-3 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-12 text-sm text-gray-400">
                      No opportunities found
                    </td>
                  </tr>
                ) : filtered.map(o => (
                  <tr key={o.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-900 max-w-xs truncate">{o.title}</td>
                    <td className="px-4 py-3 text-gray-600">{o.organization_name || '—'}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={o.opportunity_type} />
                    </td>
                    <td className="px-4 py-3 text-gray-600 text-xs">{o.experience_level || '—'}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={o.status} />
                    </td>
                    <td className="px-4 py-3">
                      <ConfidenceBadge score={o.confidence_score} />
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">
                      {o.discovered_at ? new Date(o.discovered_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Kanban View */
        <div className="flex gap-4 overflow-x-auto pb-4">
          {STAGE_COLS.map(stage => (
            <div key={stage} className="flex-shrink-0 w-64">
              <div className="bg-gray-100 rounded-xl p-3">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                    {stage.replace(/_/g, ' ')}
                  </h3>
                  <span className="bg-white text-xs font-bold text-gray-700 px-2 py-0.5 rounded-full">
                    {byStage(stage).length}
                  </span>
                </div>
                <div className="space-y-2">
                  {byStage(stage).map(o => (
                    <div key={o.id} className="bg-white rounded-lg p-3 shadow-sm border border-gray-100">
                      <p className="text-sm font-medium text-gray-900 truncate">{o.title}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{o.organization_name || '—'}</p>
                      <div className="flex items-center justify-between mt-2">
                        <ConfidenceBadge score={o.confidence_score} />
                        <span className="text-xs text-gray-400">{o.opportunity_type}</span>
                      </div>
                    </div>
                  ))}
                  {byStage(stage).length === 0 && (
                    <p className="text-xs text-gray-400 text-center py-4">Empty</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
