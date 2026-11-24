// Shared class strings for reuse
export const cls = {
  btnPrimary: "inline-flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-150 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-sm",
  btnSecondary: "inline-flex items-center justify-center bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg border border-gray-300 transition-colors duration-150 cursor-pointer text-sm",
  btnDanger: "inline-flex items-center justify-center bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-150 cursor-pointer text-sm",
  btnSuccess: "inline-flex items-center justify-center bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-150 cursor-pointer text-sm",
  card: "bg-white rounded-xl shadow-sm border border-gray-100 p-6",
  input: "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm",
}

export function ConfidenceBadge({ score }) {
  if (score === null || score === undefined) return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">No Score</span>
  if (score === 'suppressed') return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">Suppressed</span>
  const num = Number(score)
  if (num >= 80) return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">{num} · High</span>
  if (num >= 60) return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">{num} · Medium</span>
  return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">{num} · Low</span>
}

export function StatusBadge({ status, label }) {
  const text = label || status
  const colorMap = {
    active: 'bg-green-100 text-green-800',
    draft: 'bg-yellow-100 text-yellow-800',
    paused: 'bg-orange-100 text-orange-800',
    completed: 'bg-blue-100 text-blue-800',
    cancelled: 'bg-red-100 text-red-800',
    generated: 'bg-purple-100 text-purple-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    edited: 'bg-indigo-100 text-indigo-800',
    sent: 'bg-green-100 text-green-800',
    pending: 'bg-yellow-100 text-yellow-800',
    failed: 'bg-red-100 text-red-800',
    delivered: 'bg-green-100 text-green-800',
    bounced: 'bg-red-100 text-red-800',
    unresolved: 'bg-red-100 text-red-800',
    resolved: 'bg-green-100 text-green-800',
    suppressed: 'bg-gray-100 text-gray-700',
    deliverable: 'bg-green-100 text-green-800',
    undeliverable: 'bg-red-100 text-red-800',
    risky: 'bg-orange-100 text-orange-800',
    unknown: 'bg-gray-100 text-gray-700',
    inactive: 'bg-gray-100 text-gray-700',
    email: 'bg-blue-100 text-blue-800',
    manual_block: 'bg-red-100 text-red-800',
    unsubscribed: 'bg-orange-100 text-orange-800',
    hard_bounce: 'bg-red-100 text-red-800',
    spam_complaint: 'bg-pink-100 text-pink-800',
    invalid_email: 'bg-gray-100 text-gray-700',
  }
  const cls = colorMap[status?.toLowerCase()] || 'bg-gray-100 text-gray-700'
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {text}
    </span>
  )
}

export function LoadingSpinner({ size = 'md' }) {
  const sizes = { sm: 'h-4 w-4', md: 'h-8 w-8', lg: 'h-12 w-12' }
  return (
    <div className="flex justify-center items-center p-8">
      <div className={`animate-spin rounded-full border-2 border-blue-600 border-t-transparent ${sizes[size]}`}></div>
    </div>
  )
}

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="text-center py-12">
      {Icon && <Icon className="mx-auto h-12 w-12 text-gray-300 mb-4" />}
      <h3 className="text-sm font-medium text-gray-900">{title}</h3>
      {description && <p className="mt-1 text-sm text-gray-500">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="flex items-center justify-between mb-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
      </div>
      {actions && <div className="flex gap-3">{actions}</div>}
    </div>
  )
}

export function StatCard({ label, value, icon: Icon, color = 'blue', trend }) {
  const colorMap = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    red: 'bg-red-50 text-red-600',
    purple: 'bg-purple-50 text-purple-600',
  }
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value ?? '—'}</p>
          {trend && <p className="text-xs text-gray-400 mt-1">{trend}</p>}
        </div>
        {Icon && (
          <div className={`p-3 rounded-xl ${colorMap[color]}`}>
            <Icon size={22} />
          </div>
        )}
      </div>
    </div>
  )
}

export function Modal({ open, onClose, title, children, footer }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black bg-opacity-40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
        </div>
        <div className="p-6">{children}</div>
        {footer && <div className="p-6 border-t border-gray-100 bg-gray-50 rounded-b-xl flex justify-end gap-3">{footer}</div>}
      </div>
    </div>
  )
}
