import api from './client'

export const authAPI = {
  login: (email, password) =>
    api.post('/auth/login', new URLSearchParams({ username: email, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  me: () => api.get('/auth/me'),
}

export const crmAPI = {
  listOrganizations: (params) => api.get('/crm/organizations', { params }),
  getOrganization: (id) => api.get(`/crm/organizations/${id}`),
  listOpportunities: (params) => api.get('/crm/opportunities', { params }),
  getOpportunity: (id) => api.get(`/crm/opportunities/${id}`),
  updateOpportunity: (id, data) => api.patch(`/crm/opportunities/${id}`, data),
  listContacts: (params) => api.get('/crm/contacts', { params }),
  getContact: (id) => api.get(`/crm/contacts/${id}`),
  getPipeline: (params) => api.get('/crm/pipeline', { params }),
}

export const discoveryAPI = {
  triggerDiscovery: (params) => api.post('/discovery/trigger', params),
  getSources: () => api.get('/discovery/sources'),
}

export const enrichmentAPI = {
  getQueue: () => api.get('/enrichment/queue'),
  triggerEnrichment: (contactId, provider) =>
    api.post(`/enrichment/contacts/${contactId}/enrich`, { provider }),
  getHistory: (contactId) => api.get(`/enrichment/contacts/${contactId}/history`),
  confirmEnrichment: (contactId, provider) =>
    api.post(`/enrichment/contacts/${contactId}/confirm`, { provider }),
}

export const verificationAPI = {
  verify: (contactMethodId) => api.post(`/verification/verify/${contactMethodId}`),
  getStatus: (contactMethodId) => api.get(`/verification/status/${contactMethodId}`),
}

export const scoringAPI = {
  score: (opportunityId) => api.post(`/scoring/score/${opportunityId}`),
  getScore: (opportunityId) => api.get(`/scoring/score/${opportunityId}`),
}

export const campaignAPI = {
  listCampaigns: () => api.get('/campaigns'),
  createCampaign: (data) => api.post('/campaigns', data),
  getCampaign: (id) => api.get(`/campaigns/${id}`),
  updateStatus: (id, status) => api.patch(`/campaigns/${id}/status`, { status }),
  listDrafts: (campaignId) => api.get(`/campaigns/${campaignId}/drafts`),
  getDraft: (id) => api.get(`/campaigns/drafts/${id}`),
  generateDraft: (data) => api.post('/campaigns/drafts/generate', data),
  editDraft: (id, data) => api.patch(`/campaigns/drafts/${id}`, data),
  approveDraft: (id, data) => api.post(`/campaigns/drafts/${id}/approve`, data),
  rejectDraft: (id, data) => api.post(`/campaigns/drafts/${id}/reject`, data),
  dispatch: (id) => api.post(`/campaigns/drafts/${id}/dispatch`),
}

export const suppressionAPI = {
  list: (params) => api.get('/suppression', { params }),
  add: (data) => api.post('/suppression', data),
  check: (email) => api.get(`/suppression/check/${email}`),
}

export const errorAPI = {
  listErrors: (params) => api.get('/errors', { params }),
  retryJob: (jobId) => api.post(`/errors/${jobId}/retry`),
}

export const healthAPI = {
  getDashboard: () => api.get('/health/dashboard'),
  getStatus: () => api.get('/health/status'),
}
