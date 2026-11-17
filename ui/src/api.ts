const BASE = import.meta.env.VITE_API_BASE || "";

function getSessionId(): string {
  let sid = localStorage.getItem("genai_session_id");
  if (!sid) {
    sid = "sess_" + Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
    localStorage.setItem("genai_session_id", sid);
  }
  return sid;
}

async function request(path: string, opts?: RequestInit) {
  const token = localStorage.getItem("token");
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    "X-Session-ID": getSessionId(),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  const res = await fetch(`${BASE}${path}`, { ...opts, headers });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  login: (username: string, password: string) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  updateCredentials: (body: {
    x_bearer_token?: string;
    x_user_access_token?: string;
    anthropic_api_key?: string;
  }) =>
    request("/config/credentials", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getCredentialsStatus: () => request("/config/credentials/status"),
  createCampaign: (body: any) =>
    request("/campaigns", { method: "POST", body: JSON.stringify(body) }),
  listCampaigns: () => request("/campaigns"),
  addSeed: (campaignId: number, username: string) =>
    request(`/campaigns/${campaignId}/seeds`, {
      method: "POST",
      body: JSON.stringify({ username }),
    }),
  findProspects: (campaignId: number) =>
    request(`/campaigns/${campaignId}/find`, { method: "POST" }),
  loadDemoData: (campaignId: number) =>
    request(`/campaigns/${campaignId}/load-demo-data`, { method: "POST" }),
  listProspects: (campaignId: number) =>
    request(`/campaigns/${campaignId}/prospects`),
  createDraft: (prospectId: number) =>
    request(`/prospects/${prospectId}/draft`, { method: "POST" }),
  batchDraftAll: (campaignId: number) =>
    request(`/campaigns/${campaignId}/draft-all`, { method: "POST" }),
  generateDraft: (draftId: number) =>
    request(`/drafts/${draftId}/generate`, { method: "POST" }),
  updateDraft: (draftId: number, body: { dm_text?: string; status?: string; approved_by?: string }) =>
    request(`/drafts/${draftId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  approveDraft: (draftId: number, approvedBy: string = "admin") =>
    request(`/drafts/${draftId}/approve?approved_by=${encodeURIComponent(approvedBy)}`, {
      method: "PATCH",
    }),
  rejectDraft: (draftId: number) =>
    request(`/drafts/${draftId}/reject`, { method: "PATCH" }),
  sendCampaign: (campaignId: number) =>
    request(`/campaigns/${campaignId}/send`, { method: "POST" }),
  simulateSend: (campaignId: number) =>
    request(`/campaigns/${campaignId}/simulate-send`, { method: "POST" }),
  syncReplies: (campaignId: number) =>
    request(`/campaigns/${campaignId}/sync-replies`, { method: "POST" }),
  simulateReplies: (campaignId: number) =>
    request(`/campaigns/${campaignId}/simulate-replies`, { method: "POST" }),
  stats: (campaignId: number) => request(`/campaigns/${campaignId}/stats`),
  replies: (campaignId: number) => request(`/campaigns/${campaignId}/replies`),
};
