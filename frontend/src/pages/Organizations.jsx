import { useState, useEffect } from 'react'
import { crmAPI } from '../api'
import { LoadingSpinner, EmptyState, PageHeader, StatusBadge } from '../components/ui'
import { Building2, Search, Globe, MapPin } from 'lucide-react'

export default function Organizations() {
  const [orgs, setOrgs] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  const load = async (q) => {
    setLoading(true)
    try {
      const res = await crmAPI.listOrganizations(q ? { search: q } : {})
      setOrgs(Array.isArray(res.data) ? res.data : (res.data?.items || []))
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleSearch = (e) => { e.preventDefault(); load(search) }

  return (
    <div>
      <PageHeader title="Organizations" subtitle="All tracked companies and recruiting orgs" />

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-5">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm pl-9" placeholder="Search organizations..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <button className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-sm">Search</button>
        </form>
      </div>

      {loading ? <LoadingSpinner /> : orgs.length === 0 ? (
        <EmptyState icon={Building2} title="No organizations found" description="Organizations appear here as leads are discovered." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {orgs.map(org => (
            <div key={org.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start gap-3 mb-3">
                <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center text-blue-600 font-bold text-sm flex-shrink-0">
                  {org.name?.[0]?.toUpperCase() || 'O'}
                </div>
                <div className="min-w-0">
                  <h3 className="font-semibold text-gray-900 truncate">{org.name}</h3>
                  <p className="text-xs text-gray-500">{org.industry || 'Unknown industry'}</p>
                </div>
              </div>
              {org.website && (
                <a href={org.website} target="_blank" rel="noopener noreferrer"
                  className="flex items-center gap-1 text-xs text-blue-600 hover:underline mb-2">
                  <Globe size={12} />{org.website}
                </a>
              )}
              {org.location && (
                <p className="flex items-center gap-1 text-xs text-gray-500">
                  <MapPin size={12} />{org.location}
                </p>
              )}
              {org.description && (
                <p className="text-xs text-gray-500 mt-2 line-clamp-2">{org.description}</p>
              )}
              <div className="mt-3 pt-3 border-t border-gray-50">
                <StatusBadge status={org.is_active ? 'active' : 'inactive'} label={org.is_active ? 'Active' : 'Inactive'} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
