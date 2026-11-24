import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import {
  LayoutDashboard, Users, Building2, Briefcase, Mail, Shield,
  AlertTriangle, Activity, LogOut, Menu, X, Zap, ChevronRight
} from 'lucide-react'

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, roles: [] },
  { path: '/pipeline', label: 'Lead Pipeline', icon: Zap, roles: [] },
  { path: '/organizations', label: 'Organizations', icon: Building2, roles: [] },
  { path: '/contacts', label: 'Contacts', icon: Users, roles: [] },
  { path: '/opportunities', label: 'Opportunities', icon: Briefcase, roles: [] },
  { path: '/enrichment', label: 'Enrichment Queue', icon: ChevronRight, roles: ['researcher', 'admin'] },
  { path: '/campaigns', label: 'Campaign Manager', icon: Mail, roles: ['campaign_manager', 'admin'] },
  { path: '/suppression', label: 'Suppression', icon: Shield, roles: ['campaign_manager', 'admin'] },
  { path: '/errors', label: 'Error Center', icon: AlertTriangle, roles: ['admin'] },
  { path: '/health', label: 'System Health', icon: Activity, roles: ['admin'] },
]

export default function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const { user, logout, hasRole } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const visibleNavItems = navItems.filter(item =>
    item.roles.length === 0 || item.roles.some(r => hasRole(r))
  )

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-gray-900 text-white flex flex-col transition-all duration-200 flex-shrink-0`}>
        {/* Logo */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          {sidebarOpen && (
            <div>
              <h1 className="text-sm font-bold text-white">Lead Intelligence</h1>
              <p className="text-xs text-gray-400">CRM & Outreach</p>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-gray-400 hover:text-white p-1 rounded"
          >
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 overflow-y-auto">
          {visibleNavItems.map((item) => {
            const Icon = item.icon
            const active = location.pathname === item.path ||
              (item.path !== '/' && location.pathname.startsWith(item.path))
            return (
              <Link
                key={item.path}
                to={item.path}
                title={item.label}
                className={`flex items-center gap-3 px-4 py-2.5 mx-2 my-0.5 rounded-lg transition-colors ${
                  active
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <Icon size={18} className="flex-shrink-0" />
                {sidebarOpen && <span className="text-sm font-medium">{item.label}</span>}
              </Link>
            )
          })}
        </nav>

        {/* User info */}
        <div className="border-t border-gray-700 p-4">
          {sidebarOpen ? (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-xs font-bold">
                {user?.full_name?.[0] || user?.email?.[0] || 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-white truncate">{user?.full_name || user?.email}</p>
                <p className="text-xs text-gray-400 truncate capitalize">
                  {Array.isArray(user?.roles) ? user.roles.join(', ') : user?.role || 'user'}
                </p>
              </div>
              <button onClick={handleLogout} className="text-gray-400 hover:text-red-400">
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <button onClick={handleLogout} className="text-gray-400 hover:text-red-400 flex justify-center w-full">
              <LogOut size={18} />
            </button>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-6 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}
