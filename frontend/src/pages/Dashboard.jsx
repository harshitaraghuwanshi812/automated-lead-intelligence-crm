import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { healthAPI, crmAPI, errorAPI } from '../api'
import { StatCard, LoadingSpinner, StatusBadge } from '../components/ui'
import {
  Zap, Users, Building2, Briefcase, Mail, AlertTriangle,
  Activity, CheckCircle, XCircle, Clock, TrendingUp
} from 'lucide-react'

export default function Dashboard() {
  const [health, setHealth] = useState(null)
  const [stats, setStats] = useState(null)
  const [recentErrors, setRecentErrors] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [h, orgs, opps, contacts] = await Promise.allSettled([
          healthAPI.getDashboard(),
          crmAPI.listOrganizations({ limit: 1 }),
          crmAPI.listOpportunities({ limit: 1 }),
          crmAPI.listContacts({ limit: 1 }),
        ])
        if (h.status === 'fulfilled') setHealth(h.value.data)
        setStats({
          orgs: orgs.status === 'fulfilled' ? (orgs.value.data?.total || orgs.value.data?.length || '—') : '—',
          opps: opps.status === 'fulfilled' ? (opps.value.data?.total || opps.value.data?.length || '—') : '—',
          contacts: contacts.status === 'fulfilled' ? (contacts.value.data?.total || contacts.value.data?.length || '—') : '—',
        })
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <LoadingSpinner size="lg" />

  const metrics = health?.metrics || {}
  const services = health?.services || {}

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">System Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">
          Overview of lead generation, campaigns and system health
        </p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard
          label="Organizations"
          value={stats?.orgs}
          icon={Building2}
          color="blue"
        />
        <StatCard
          label="Opportunities"
          value={stats?.opps}
          icon={Briefcase}
          color="purple"
        />
        <StatCard
          label="Contacts"
          value={stats?.contacts}
          icon={Users}
          color="green"
        />
        <StatCard
          label="Emails Sent Today"
          value={metrics?.emails_sent_today ?? '—'}
          icon={Mail}
          color="yellow"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* System Services */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Activity size={18} className="text-blue-600" />
            Service Health
          </h2>
          <div className="space-y-3">
            {Object.entries(services).map(([key, val]) => (
              <div key={key} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                <span className="text-sm text-gray-700 capitalize">{key.replace(/_/g, ' ')}</span>
                <div className="flex items-center gap-2">
                  {val === 'healthy' || val === 'connected' || val === true ? (
                    <><CheckCircle size={14} className="text-green-500" /><span className="text-xs text-green-600 font-medium">Healthy</span></>
                  ) : val === 'degraded' ? (
                    <><Clock size={14} className="text-yellow-500" /><span className="text-xs text-yellow-600 font-medium">Degraded</span></>
                  ) : (
                    <><XCircle size={14} className="text-red-400" /><span className="text-xs text-gray-500 font-medium capitalize">{String(val)}</span></>
                  )}
                </div>
              </div>
            ))}
            {Object.keys(services).length === 0 && (
              <p className="text-sm text-gray-400 text-center py-4">No service data available</p>
            )}
          </div>
        </div>

        {/* Campaign Metrics */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp size={18} className="text-blue-600" />
            Campaign Metrics
          </h2>
          <div className="space-y-3">
            {[
              { label: 'Total Sent', value: metrics?.total_sent },
              { label: 'Delivered', value: metrics?.delivered },
              { label: 'Opened', value: metrics?.opened },
              { label: 'Bounced', value: metrics?.bounced },
              { label: 'Unsubscribed', value: metrics?.unsubscribed },
              { label: 'Pending Approval', value: metrics?.pending_approval },
            ].map(({ label, value }) => (
              <div key={label} className="flex justify-between py-2 border-b border-gray-50 last:border-0">
                <span className="text-sm text-gray-600">{label}</span>
                <span className="text-sm font-semibold text-gray-900">{value ?? '—'}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Links */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'View Pipeline', path: '/pipeline', icon: Zap, color: 'text-blue-600' },
            { label: 'Enrich Contacts', path: '/enrichment', icon: Users, color: 'text-green-600' },
            { label: 'Create Campaign', path: '/campaigns', icon: Mail, color: 'text-purple-600' },
            { label: 'Error Center', path: '/errors', icon: AlertTriangle, color: 'text-red-600' },
          ].map(({ label, path, icon: Icon, color }) => (
            <Link
              key={path}
              to={path}
              className="flex flex-col items-center gap-2 p-4 rounded-xl border border-gray-100 hover:border-blue-200 hover:bg-blue-50 transition-colors"
            >
              <Icon size={22} className={color} />
              <span className="text-xs font-medium text-gray-700">{label}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
