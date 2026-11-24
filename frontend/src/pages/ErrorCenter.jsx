import { useState, useEffect } from 'react'
import { errorAPI } from '../api'
import { LoadingSpinner, EmptyState, PageHeader, StatusBadge } from '../components/ui'
import { AlertTriangle, RefreshCw, ChevronDown, ChevronRight, Hash } from 'lucide-react'

const CATEGORIES = ['', 'network', 'auth', 'rate_limit', 'parse', 'validation', 'timeout', 'unknown']

export default function ErrorCenter() {
  const [errors, setErrors] = useState([])
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState('')
  const [status, setStatus] = useState('')
  const [expanded, setExpanded] = useState(null)
  const [retrying, setRetrying] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const params = {}
      if (category) params.category = category
      if (status) params.recovery_status = status
      const res = await errorAPI.listErrors(params)
      setErrors(Array.isArray(res.data) ? res.data : (res.data?.items || []))
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [category, status])

  const handleRetry = async (jobId, e) => {
    e.stopPropagation()
    setRetrying(jobId)
    try {
      await errorAPI.retryJob(jobId)
      await load()
    } catch (err) {
      console.error(err)
    } finally {
      setRetrying(null)
    }
  }

  const categoryColor = {
    network: 'bg-orange-100 text-orange-700',
    auth: 'bg-red-100 text-red-700',
    rate_limit: 'bg-yellow-100 text-yellow-700',
    parse: 'bg-purple-100 text-purple-700',
    validation: 'bg-pink-100 text-pink-700',
    timeout: 'bg-orange-100 text-orange-700',
    unknown: 'bg-gray-100 text-gray-700',
  }

  const unresolved = errors.filter(e => e.recovery_status === 'unresolved').length
  const resolved = errors.filter(e => e.recovery_status === 'resolved').length

  return (
    <div>
      <PageHeader
        title="Error Center"
        subtitle="Workflow failures, job errors and recovery status"
        actions={
          <button onClick={load} className="bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg border border-gray-300 transition-colors cursor-pointer text-sm flex items-center gap-2">
            <RefreshCw size={14} /> Refresh
          </button>
        }
      />

      {/* Stats strip */}
      <div className="grid grid-cols-3 gap-4 mb-5">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center py-4">
          <p className="text-2xl font-bold text-gray-900">{errors.length}</p>
          <p className="text-xs text-gray-500 mt-1">Total Errors</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center py-4">
          <p className="text-2xl font-bold text-red-600">{unresolved}</p>
          <p className="text-xs text-gray-500 mt-1">Unresolved</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center py-4">
          <p className="text-2xl font-bold text-green-600">{resolved}</p>
          <p className="text-xs text-gray-500 mt-1">Resolved</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-5 flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-gray-600">Category:</label>
          <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm w-auto text-xs" value={category} onChange={e => setCategory(e.target.value)}>
            {CATEGORIES.map(c => (
              <option key={c} value={c}>{c || 'All Categories'}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-gray-600">Status:</label>
          <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm w-auto text-xs" value={status} onChange={e => setStatus(e.target.value)}>
            <option value="">All Statuses</option>
            <option value="unresolved">Unresolved</option>
            <option value="resolved">Resolved</option>
            <option value="retrying">Retrying</option>
          </select>
        </div>
      </div>

      {loading ? <LoadingSpinner /> : errors.length === 0 ? (
        <EmptyState icon={AlertTriangle} title="No errors found" description="All workflows are running clean." />
      ) : (
        <div className="space-y-2">
          {errors.map(err => (
            <div key={err.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 p-0 overflow-hidden">
              <div
                className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
                onClick={() => setExpanded(expanded === err.id ? null : err.id)}
              >
                <div className="flex items-center gap-3 min-w-0">
                  {expanded === err.id
                    ? <ChevronDown size={16} className="text-gray-400 flex-shrink-0" />
                    : <ChevronRight size={16} className="text-gray-400 flex-shrink-0" />}
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm text-gray-900 truncate">{err.workflow_name || err.job_name || 'Unknown Job'}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${categoryColor[err.failure_category] || 'bg-gray-100 text-gray-700'}`}>
                        {err.failure_category || 'unknown'}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-400 mt-0.5">
                      <span className="flex items-center gap-1"><Hash size={10} />{err.correlation_id?.slice(0, 16) || '—'}</span>
                      <span>Retries: {err.retry_count || 0}</span>
                      <span>{err.created_at ? new Date(err.created_at).toLocaleString() : '—'}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <StatusBadge status={err.recovery_status || 'unresolved'} />
                  {err.recovery_status === 'unresolved' && (
                    <button
                      onClick={(e) => handleRetry(err.id, e)}
                      disabled={retrying === err.id}
                      className="bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg border border-gray-300 transition-colors cursor-pointer text-xs py-1 px-2 flex items-center gap-1 disabled:opacity-50"
                    >
                      <RefreshCw size={12} className={retrying === err.id ? 'animate-spin' : ''} />
                      {retrying === err.id ? 'Retrying...' : 'Retry'}
                    </button>
                  )}
                </div>
              </div>

              {expanded === err.id && (
                <div className="border-t border-gray-100 p-4 bg-gray-50 space-y-3">
                  <div>
                    <p className="text-xs font-semibold text-gray-500 mb-1">Error Message</p>
                    <p className="text-xs text-red-700 bg-red-50 border border-red-100 rounded-lg p-3 font-mono">
                      {err.error_message || 'No error message recorded'}
                    </p>
                  </div>
                  {err.stack_trace && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 mb-1">Stack Trace</p>
                      <pre className="text-xs text-gray-600 bg-gray-100 rounded-lg p-3 overflow-x-auto max-h-32 font-mono">
                        {err.stack_trace}
                      </pre>
                    </div>
                  )}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    <div>
                      <p className="text-gray-400 font-medium">Correlation ID</p>
                      <p className="font-mono text-gray-700 truncate">{err.correlation_id || '—'}</p>
                    </div>
                    <div>
                      <p className="text-gray-400 font-medium">Job Type</p>
                      <p className="text-gray-700">{err.job_type || err.workflow_name || '—'}</p>
                    </div>
                    <div>
                      <p className="text-gray-400 font-medium">Max Retries</p>
                      <p className="text-gray-700">{err.max_retries || 3}</p>
                    </div>
                    <div>
                      <p className="text-gray-400 font-medium">Next Retry</p>
                      <p className="text-gray-700">{err.next_retry_at ? new Date(err.next_retry_at).toLocaleString() : '—'}</p>
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
