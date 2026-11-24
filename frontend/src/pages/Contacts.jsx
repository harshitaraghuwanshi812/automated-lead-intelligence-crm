import { useState, useEffect } from 'react'
import { crmAPI } from '../api'
import { LoadingSpinner, EmptyState, PageHeader, StatusBadge } from '../components/ui'
import { Users, Search, Mail, Phone, Building2 } from 'lucide-react'

export default function Contacts() {
  const [contacts, setContacts] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  const load = async (q) => {
    setLoading(true)
    try {
      const res = await crmAPI.listContacts(q ? { search: q } : {})
      setContacts(Array.isArray(res.data) ? res.data : (res.data?.items || []))
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const verificationColor = (status) => {
    if (status === 'deliverable') return 'text-green-600'
    if (status === 'undeliverable') return 'text-red-500'
    if (status === 'risky' || status === 'catch-all') return 'text-yellow-600'
    return 'text-gray-400'
  }

  return (
    <div>
      <PageHeader title="Contacts" subtitle="Enriched contact records with verification status" />

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-5">
        <form onSubmit={(e) => { e.preventDefault(); load(search) }} className="flex gap-2">
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm pl-9" placeholder="Search contacts..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <button className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-sm">Search</button>
        </form>
      </div>

      {loading ? <LoadingSpinner /> : contacts.length === 0 ? (
        <EmptyState icon={Users} title="No contacts found" description="Contacts are enriched from discovered opportunities." />
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {['Name', 'Title', 'Organization', 'Email', 'Verification', 'Source'].map(h => (
                  <th key={h} className="text-left text-xs font-semibold text-gray-500 px-4 py-3 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {contacts.map(c => (
                <tr key={c.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 bg-indigo-100 rounded-full flex items-center justify-center text-xs font-bold text-indigo-600">
                        {c.full_name?.[0]?.toUpperCase() || 'C'}
                      </div>
                      <span className="font-medium text-gray-900">{c.full_name || '—'}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-600 text-xs">{c.title || '—'}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1 text-gray-600 text-xs">
                      <Building2 size={12} className="text-gray-400" />
                      {c.organization_name || '—'}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {c.email ? (
                      <div className="flex items-center gap-1">
                        <Mail size={12} className={verificationColor(c.email_status)} />
                        <span className="text-xs text-gray-700">{c.email}</span>
                      </div>
                    ) : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={c.email_status || 'unknown'} />
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">{c.source || 'manual'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
