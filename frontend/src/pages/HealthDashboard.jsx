import { useState, useEffect } from 'react'
import { healthAPI } from '../api'
import { LoadingSpinner, PageHeader, StatCard } from '../components/ui'
import {
  Activity, CheckCircle, XCircle, AlertCircle, Clock, RefreshCw,
  Database, Cpu, Mail, Zap, Server, CreditCard
} from 'lucide-react'

function ServiceChip({ name, status }) {
  const isHealthy = status === 'healthy' || status === 'connected' || status === true || status === 'running'
  const isDegraded = status === 'degraded' || status === 'slow'
  return (
    <div className={`flex items-center justify-between px-4 py-3 rounded-xl border ${
      isHealthy ? 'border-green-200 bg-green-50' :
      isDegraded ? 'border-yellow-200 bg-yellow-50' :
      'border-red-200 bg-red-50'
    }`}>
      <span className={`text-sm font-medium capitalize ${
        isHealthy ? 'text-green-800' : isDegraded ? 'text-yellow-800' : 'text-red-800'
      }`}>
        {name.replace(/_/g, ' ')}
      </span>
      <div className="flex items-center gap-1.5">
        {isHealthy ? (
          <><CheckCircle size={15} className="text-green-500" /><span className="text-xs text-green-600 font-medium">Healthy</span></>
        ) : isDegraded ? (
          <><AlertCircle size={15} className="text-yellow-500" /><span className="text-xs text-yellow-600 font-medium">Degraded</span></>
        ) : (
          <><XCircle size={15} className="text-red-400" /><span className="text-xs text-red-600 font-medium capitalize">{String(status)}</span></>
        )}
      </div>
    </div>
  )
}

function MetricRow({ label, value, unit }) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-gray-50 last:border-0">
      <span className="text-sm text-gray-600">{label}</span>
      <span className="text-sm font-semibold text-gray-900">{value ?? '—'}{unit ? ` ${unit}` : ''}</span>
    </div>
  )
}

export default function HealthDashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const res = await healthAPI.getDashboard()
      setData(res.data)
      setLastRefresh(new Date())
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  // Auto-refresh every 30s
  useEffect(() => {
    const timer = setInterval(load, 30000)
    return () => clearInterval(timer)
  }, [])

  const services = data?.services || {}
  const metrics = data?.metrics || {}
  const api_usage = data?.api_usage || {}
  const credit_usage = data?.credit_usage || {}
  const queue = data?.queue || {}

  const overallHealthy = Object.values(services).every(
    v => v === 'healthy' || v === 'connected' || v === true || v === 'running'
  )

  return (
    <div>
      <PageHeader
        title="System Health"
        subtitle={lastRefresh ? `Last updated: ${lastRefresh.toLocaleTimeString()}` : 'Loading health data...'}
        actions={
          <button onClick={load} disabled={loading} className="bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg border border-gray-300 transition-colors cursor-pointer text-sm flex items-center gap-2 disabled:opacity-50">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        }
      />

      {loading && !data ? <LoadingSpinner size="lg" /> : (
        <div className="space-y-6">
          {/* Overall Status Banner */}
          <div className={`flex items-center gap-3 p-4 rounded-xl border-2 ${
            overallHealthy ? 'border-green-300 bg-green-50' : 'border-yellow-300 bg-yellow-50'
          }`}>
            {overallHealthy
              ? <CheckCircle size={22} className="text-green-500" />
              : <AlertCircle size={22} className="text-yellow-500" />}
            <div>
              <p className={`font-semibold ${overallHealthy ? 'text-green-800' : 'text-yellow-800'}`}>
                {overallHealthy ? 'All Systems Operational' : 'Some Services Degraded'}
              </p>
              <p className="text-xs text-gray-500">
                {Object.keys(services).length} services monitored · Auto-refreshes every 30s
              </p>
            </div>
          </div>

          {/* Top Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Emails Sent Today" value={metrics.emails_sent_today} icon={Mail} color="blue" />
            <StatCard label="Pending Approval" value={metrics.pending_approval} icon={Clock} color="yellow" />
            <StatCard label="Queue Depth" value={queue.pending_jobs} icon={Zap} color="purple" />
            <StatCard label="Errors (Unresolved)" value={metrics.unresolved_errors} icon={AlertCircle} color="red" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Service Health */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Server size={18} className="text-blue-600" />
                Service Status
              </h2>
              <div className="space-y-2">
                {Object.entries(services).map(([k, v]) => (
                  <ServiceChip key={k} name={k} status={v} />
                ))}
                {Object.keys(services).length === 0 && (
                  <p className="text-sm text-gray-400 text-center py-6">No services reporting</p>
                )}
              </div>
            </div>

            {/* Campaign & Email Metrics */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Activity size={18} className="text-blue-600" />
                Campaign Metrics
              </h2>
              <MetricRow label="Total Sent" value={metrics.total_sent} />
              <MetricRow label="Delivered" value={metrics.delivered} />
              <MetricRow label="Opened" value={metrics.opened} />
              <MetricRow label="Clicked" value={metrics.clicked} />
              <MetricRow label="Bounced" value={metrics.bounced} />
              <MetricRow label="Unsubscribed" value={metrics.unsubscribed} />
              <MetricRow label="Spam Complaints" value={metrics.spam_complaints} />
            </div>

            {/* API Usage */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Cpu size={18} className="text-blue-600" />
                API Usage
              </h2>
              {Object.keys(api_usage).length > 0 ? (
                Object.entries(api_usage).map(([k, v]) => (
                  <MetricRow key={k} label={k.replace(/_/g, ' ')} value={v} />
                ))
              ) : (
                <>
                  <MetricRow label="Gemini API Calls" value={metrics.gemini_calls} />
                  <MetricRow label="Gemini Tokens Used" value={metrics.gemini_tokens} />
                  <MetricRow label="Email Provider Calls" value={metrics.email_provider_calls} />
                </>
              )}
            </div>

            {/* Credit Usage */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <CreditCard size={18} className="text-blue-600" />
                Credit Usage
              </h2>
              {Object.keys(credit_usage).length > 0 ? (
                Object.entries(credit_usage).map(([k, v]) => (
                  <MetricRow key={k} label={k.replace(/_/g, ' ')} value={v} />
                ))
              ) : (
                <>
                  <MetricRow label="ContactOut Credits Used" value={metrics.contactout_credits} />
                  <MetricRow label="Snov.io Credits Used" value={metrics.snovio_credits} />
                  <MetricRow label="Verification Credits" value={metrics.verification_credits} />
                </>
              )}
            </div>
          </div>

          {/* n8n Workflow Status */}
          {data?.workflows && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Zap size={18} className="text-blue-600" />
                n8n Workflow Health
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {data.workflows.map((wf, i) => (
                  <div key={i} className={`flex items-center gap-2 p-3 rounded-lg border ${
                    wf.active ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'
                  }`}>
                    {wf.active ? <CheckCircle size={14} className="text-green-500" /> : <Clock size={14} className="text-gray-400" />}
                    <span className="text-xs font-medium text-gray-700">{wf.name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
