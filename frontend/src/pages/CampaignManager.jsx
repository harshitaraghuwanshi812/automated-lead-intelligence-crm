import { useState, useEffect } from 'react'
import { campaignAPI, crmAPI } from '../api'
import { LoadingSpinner, EmptyState, PageHeader, StatusBadge, Modal } from '../components/ui'
import {
  Mail, Plus, ChevronRight, Zap, Edit3, Check, X, Eye,
  AlertCircle, Send, Pause, Play
} from 'lucide-react'

function CreateCampaignModal({ open, onClose, onCreated }) {
  const [form, setForm] = useState({ name: '', description: '', objective: '', daily_limit: 50, monthly_limit: 1000 })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async () => {
    setSaving(true)
    setError(null)
    try {
      const res = await campaignAPI.createCampaign(form)
      onCreated(res.data)
      onClose()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create campaign')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Create New Campaign"
      footer={<>
        <button onClick={onClose} className="bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg border border-gray-300 transition-colors cursor-pointer">Cancel</button>
        <button onClick={handleSubmit} disabled={saving || !form.name} className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
          {saving ? 'Creating...' : 'Create Campaign'}
        </button>
      </>}
    >
      <div className="space-y-4">
        {error && <div className="text-xs text-red-600 bg-red-50 border border-red-200 p-3 rounded-lg">{error}</div>}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Campaign Name *</label>
          <input className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="e.g., SDE Fresher Outreach Q1" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm h-20 resize-none" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="Campaign goal and audience..." />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Daily Limit</label>
            <input type="number" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm" value={form.daily_limit} onChange={e => setForm(f => ({ ...f, daily_limit: parseInt(e.target.value) }))} min="1" max="500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Limit</label>
            <input type="number" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm" value={form.monthly_limit} onChange={e => setForm(f => ({ ...f, monthly_limit: parseInt(e.target.value) }))} min="1" max="10000" />
          </div>
        </div>
      </div>
    </Modal>
  )
}

function GenerateDraftModal({ open, onClose, campaign, contacts, opportunities, onGenerated }) {
  const [form, setForm] = useState({ opportunity_id: '', contact_id: '' })
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState(null)

  const handleGenerate = async () => {
    setGenerating(true)
    setError(null)
    try {
      const res = await campaignAPI.generateDraft({ campaign_id: campaign?.id, ...form })
      onGenerated(res.data)
      onClose()
    } catch (e) {
      setError(e.response?.data?.detail || 'Draft generation failed')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Generate AI Email Draft"
      footer={<>
        <button onClick={onClose} className="bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg border border-gray-300 transition-colors cursor-pointer">Cancel</button>
        <button onClick={handleGenerate} disabled={generating || !form.opportunity_id || !form.contact_id} className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
          <Zap size={14} />
          {generating ? 'Generating...' : 'Generate Draft'}
        </button>
      </>}
    >
      <div className="space-y-4">
        {error && <div className="text-xs text-red-600 bg-red-50 border border-red-200 p-3 rounded-lg">{error}</div>}
        <div className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <Zap size={16} className="text-blue-600 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-blue-700">AI will generate a personalized email using only verified data from the opportunity and contact. No facts will be invented.</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Select Opportunity *</label>
          <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm" value={form.opportunity_id} onChange={e => setForm(f => ({ ...f, opportunity_id: e.target.value }))}>
            <option value="">— Choose opportunity —</option>
            {(opportunities || []).map(o => (
              <option key={o.id} value={o.id}>{o.title} · {o.organization_name}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Select Contact *</label>
          <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm" value={form.contact_id} onChange={e => setForm(f => ({ ...f, contact_id: e.target.value }))}>
            <option value="">— Choose contact —</option>
            {(contacts || []).map(c => (
              <option key={c.id} value={c.id}>{c.full_name} · {c.email || 'no email'}</option>
            ))}
          </select>
        </div>
      </div>
    </Modal>
  )
}

function DraftCard({ draft, onApprove, onReject, onDispatch }) {
  const [editing, setEditing] = useState(false)
  const [subject, setSubject] = useState(draft.subject_line || '')
  const [body, setBody] = useState(draft.email_body || '')
  const [saving, setSaving] = useState(false)
  const [approving, setApproving] = useState(false)
  const [rejecting, setRejecting] = useState(false)
  const [dispatching, setDispatching] = useState(false)
  const [notes, setNotes] = useState('')
  const [approveModal, setApproveModal] = useState(false)

  const saveEdit = async () => {
    setSaving(true)
    try {
      await campaignAPI.editDraft(draft.id, { subject_line: subject, email_body: body })
      setEditing(false)
    } catch (e) { console.error(e) }
    finally { setSaving(false) }
  }

  const handleApprove = async () => {
    setApproving(true)
    try {
      await campaignAPI.approveDraft(draft.id, {
        decision: 'approved',
        review_notes: notes,
        approved_recipient: draft.recipient_email || '',
        approved_subject: subject,
        approved_body: body,
      })
      setApproveModal(false)
      onApprove(draft.id)
    } catch (e) { console.error(e) }
    finally { setApproving(false) }
  }

  const handleReject = async () => {
    setRejecting(true)
    try {
      await campaignAPI.rejectDraft(draft.id, { decision: 'rejected', review_notes: 'Rejected by reviewer' })
      onReject(draft.id)
    } catch (e) { console.error(e) }
    finally { setRejecting(false) }
  }

  const handleDispatch = async () => {
    setDispatching(true)
    try {
      await campaignAPI.dispatch(draft.id)
      onDispatch(draft.id)
    } catch (e) { console.error(e) }
    finally { setDispatching(false) }
  }

  const statusColor = {
    generated: 'border-purple-200 bg-purple-50',
    edited: 'border-indigo-200 bg-indigo-50',
    approved: 'border-green-200 bg-green-50',
    rejected: 'border-red-200 bg-red-50',
    sent: 'border-gray-200 bg-gray-50',
  }

  return (
    <div className={`border rounded-xl p-4 mb-4 ${statusColor[draft.status] || 'border-gray-200'}`}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <StatusBadge status={draft.status} />
            <span className="text-xs text-gray-500">→ {draft.recipient_name || draft.recipient_email || '—'}</span>
          </div>
          <p className="text-xs text-gray-500">{draft.company_name} · {draft.job_title}</p>
        </div>
        <div className="flex gap-2">
          {!editing && draft.status !== 'sent' && draft.status !== 'approved' && (
            <button onClick={() => setEditing(true)} className="bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg border border-gray-300 transition-colors cursor-pointer text-xs py-1 px-2 flex items-center gap-1">
              <Edit3 size={12} /> Edit
            </button>
          )}
          {draft.status === 'generated' || draft.status === 'edited' ? (
            <>
              <button onClick={() => setApproveModal(true)} className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer text-xs py-1 px-2 flex items-center gap-1">
                <Check size={12} /> Approve
              </button>
              <button onClick={handleReject} disabled={rejecting} className="bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer text-xs py-1 px-2 flex items-center gap-1">
                <X size={12} /> Reject
              </button>
            </>
          ) : draft.status === 'approved' ? (
            <button onClick={handleDispatch} disabled={dispatching} className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-xs py-1 px-2 flex items-center gap-1">
              <Send size={12} /> {dispatching ? 'Sending...' : 'Dispatch'}
            </button>
          ) : null}
        </div>
      </div>

      {editing ? (
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Subject Line</label>
            <input className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm text-sm" value={subject} onChange={e => setSubject(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Email Body</label>
            <textarea className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm h-48 resize-none text-xs font-mono" value={body} onChange={e => setBody(e.target.value)} />
          </div>
          <div className="flex gap-2">
            <button onClick={saveEdit} disabled={saving} className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-xs py-1 px-3">{saving ? 'Saving...' : 'Save Changes'}</button>
            <button onClick={() => setEditing(false)} className="bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg border border-gray-300 transition-colors cursor-pointer text-xs py-1 px-3">Cancel</button>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <div>
            <span className="text-xs font-semibold text-gray-500">SUBJECT: </span>
            <span className="text-sm text-gray-800">{draft.subject_line || subject}</span>
          </div>
          <div className="text-xs text-gray-700 bg-white bg-opacity-70 rounded-lg p-3 font-mono whitespace-pre-wrap max-h-48 overflow-y-auto">
            {draft.email_body || body || '(empty)'}
          </div>
          {(draft.missing_info_warnings?.length > 0) && (
            <div className="flex items-start gap-2 text-xs text-amber-700 bg-amber-50 p-2 rounded-lg">
              <AlertCircle size={12} className="mt-0.5 flex-shrink-0" />
              <span>Missing: {draft.missing_info_warnings.join(', ')}</span>
            </div>
          )}
        </div>
      )}

      {/* Approve Modal */}
      <Modal open={approveModal} onClose={() => setApproveModal(false)} title="Approve Email Draft"
        footer={<>
          <button onClick={() => setApproveModal(false)} className="bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg border border-gray-300 transition-colors cursor-pointer">Cancel</button>
          <button onClick={handleApprove} disabled={approving} className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer">
            {approving ? 'Approving...' : 'Approve & Enable Dispatch'}
          </button>
        </>}
      >
        <div className="space-y-4">
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
            Approving this draft enables it for email dispatch. The email will only be sent after you click <strong>Dispatch</strong>.
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Review Notes (optional)</label>
            <textarea className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm h-20 resize-none text-sm" value={notes} onChange={e => setNotes(e.target.value)} placeholder="Any notes about approval..." />
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default function CampaignManager() {
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)
  const [createModal, setCreateModal] = useState(false)
  const [selected, setSelected] = useState(null)
  const [drafts, setDrafts] = useState([])
  const [draftLoading, setDraftLoading] = useState(false)
  const [generateModal, setGenerateModal] = useState(false)
  const [contacts, setContacts] = useState([])
  const [opportunities, setOpportunities] = useState([])

  const load = async () => {
    setLoading(true)
    try {
      const res = await campaignAPI.listCampaigns()
      setCampaigns(Array.isArray(res.data) ? res.data : [])
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const loadDrafts = async (cid) => {
    setDraftLoading(true)
    try {
      const res = await campaignAPI.listDrafts(cid)
      setDrafts(Array.isArray(res.data) ? res.data : [])
    } catch (e) { console.error(e) }
    finally { setDraftLoading(false) }
  }

  const loadAudienceData = async () => {
    try {
      const [c, o] = await Promise.all([crmAPI.listContacts(), crmAPI.listOpportunities()])
      setContacts(Array.isArray(c.data) ? c.data : (c.data?.items || []))
      setOpportunities(Array.isArray(o.data) ? o.data : (o.data?.items || []))
    } catch (e) { console.error(e) }
  }

  useEffect(() => { load() }, [])

  const selectCampaign = (c) => {
    setSelected(c)
    loadDrafts(c.id)
    loadAudienceData()
  }

  const handleDraftApproved = (draftId) => {
    setDrafts(ds => ds.map(d => d.id === draftId ? { ...d, status: 'approved' } : d))
  }
  const handleDraftRejected = (draftId) => {
    setDrafts(ds => ds.map(d => d.id === draftId ? { ...d, status: 'rejected' } : d))
  }
  const handleDraftDispatched = (draftId) => {
    setDrafts(ds => ds.map(d => d.id === draftId ? { ...d, status: 'sent' } : d))
  }

  return (
    <div>
      <PageHeader
        title="Campaign Manager"
        subtitle="Create campaigns, generate AI drafts, review and dispatch emails"
        actions={
          <button onClick={() => setCreateModal(true)} className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center gap-2">
            <Plus size={16} /> New Campaign
          </button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Campaign List */}
        <div className="lg:col-span-1">
          {loading ? <LoadingSpinner /> : campaigns.length === 0 ? (
            <EmptyState icon={Mail} title="No campaigns" description="Create your first campaign to get started." />
          ) : (
            <div className="space-y-2">
              {campaigns.map(c => (
                <div
                  key={c.id}
                  onClick={() => selectCampaign(c)}
                  className={`card cursor-pointer transition-all hover:shadow-md ${selected?.id === c.id ? 'ring-2 ring-blue-500' : ''}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-sm text-gray-900 truncate">{c.name}</h3>
                    <StatusBadge status={c.status} />
                  </div>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>{c.draft_count || 0} drafts</span>
                    <span>{c.approved_count || 0} approved</span>
                    <span>{c.sent_count || 0} sent</span>
                  </div>
                  {c.description && <p className="text-xs text-gray-400 mt-2 truncate">{c.description}</p>}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Draft Area */}
        <div className="lg:col-span-2">
          {!selected ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center py-16">
              <Mail size={40} className="mx-auto text-gray-200 mb-3" />
              <p className="text-gray-400 text-sm">Select a campaign to view drafts</p>
            </div>
          ) : (
            <div>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">{selected.name}</h2>
                  <p className="text-xs text-gray-500">Daily limit: {selected.daily_limit} · Monthly: {selected.monthly_limit}</p>
                </div>
                <button onClick={() => setGenerateModal(true)} className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center gap-2">
                  <Zap size={14} /> Generate Draft
                </button>
              </div>

              {draftLoading ? <LoadingSpinner /> : drafts.length === 0 ? (
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center py-10">
                  <Zap size={32} className="mx-auto text-gray-200 mb-3" />
                  <p className="text-sm text-gray-400">No drafts yet. Click "Generate Draft" to create one with Gemini AI.</p>
                </div>
              ) : (
                drafts.map(d => (
                  <DraftCard
                    key={d.id}
                    draft={d}
                    onApprove={handleDraftApproved}
                    onReject={handleDraftRejected}
                    onDispatch={handleDraftDispatched}
                  />
                ))
              )}
            </div>
          )}
        </div>
      </div>

      <CreateCampaignModal
        open={createModal}
        onClose={() => setCreateModal(false)}
        onCreated={(c) => { setCampaigns(prev => [c, ...prev]); setCreateModal(false) }}
      />

      <GenerateDraftModal
        open={generateModal}
        onClose={() => setGenerateModal(false)}
        campaign={selected}
        contacts={contacts}
        opportunities={opportunities}
        onGenerated={(draft) => { setDrafts(prev => [draft, ...prev]); setGenerateModal(false) }}
      />
    </div>
  )
}
