/**
 * MythosEngine API Client
 * Talks to the FastAPI backend on localhost:8741.
 */

const BASE =
  typeof window !== "undefined" && window.electronAPI
    ? "http://127.0.0.1:8741"
    : "/api";

let _token = localStorage.getItem("me_token") || null;

export function setToken(t) {
  _token = t;
  if (t) localStorage.setItem("me_token", t);
  else localStorage.removeItem("me_token");
}

export function getToken() {
  return _token;
}

async function request(method, path, body = null) {
  const headers = { "Content-Type": "application/json" };
  if (_token) headers["Authorization"] = `Bearer ${_token}`;

  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(`${BASE}${path}`, opts);
  if (res.status === 401) {
    setToken(null);
    window.dispatchEvent(new CustomEvent('auth:logout'));
    throw new Error("Session expired");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  if (res.status === 204) return null;
  return res.json();
}

async function requestText(method, path) {
  const headers = { "Content-Type": "application/json" };
  if (_token) headers["Authorization"] = `Bearer ${_token}`;
  const res = await fetch(`${BASE}${path}`, { method, headers });
  if (res.status === 401) {
    setToken(null);
    window.location.hash = "#/login";
    throw new Error("Session expired");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.text();
}

// ── Auth ─────────────────────────────────────────────────────────────────────
export const auth = {
  status: async () => {
    // Raw fetch — no auth token, no 401 redirect
    const res = await fetch(`${BASE}/auth/status`);
    return res.json();
  },
  setup: (email, username, password) =>
    request("POST", "/auth/setup", { email, username, password }),
  login: (email, password) => request("POST", "/auth/login", { email, password }),
  logout: () => request("POST", "/auth/logout"),
  me: () => request("GET", "/auth/me"),
  changePassword: (current, newPw) =>
    request("POST", "/auth/change-password", {
      current_password: current,
      new_password: newPw,
    }),
  register: (email, username, password, invite_code) =>
    request("POST", "/auth/register", { email, username, password, invite_code }),
};

// ── Notes ────────────────────────────────────────────────────────────────────
export const notes = {
  // List & search
  list: (folder = "", tag = "") => {
    const params = new URLSearchParams();
    if (folder) params.set("folder", folder);
    if (tag) params.set("tag", tag);
    const qs = params.toString();
    return request("GET", `/notes${qs ? `?${qs}` : ""}`);
  },
  get: (id) => request("GET", `/notes/${encodeURIComponent(id)}`),
  search: (query) =>
    request("GET", `/notes/search?q=${encodeURIComponent(query)}`),

  // CRUD
  create: (title, content = "", folder_id = null, tags = [], meta = {}) =>
    request("POST", "/notes", { title, content, folder_id, tags, meta }),
  update: (id, data) =>
    request("PUT", `/notes/${encodeURIComponent(id)}`, data),
  delete: (id) => request("DELETE", `/notes/${encodeURIComponent(id)}`),

  // Move
  move: (note_id, dest_folder_id) =>
    request("POST", "/notes/move", { note_id, dest_folder_id }),

  // Tags
  addTag: (id, tag) =>
    request("POST", `/notes/${encodeURIComponent(id)}/tags`, { tag }),
  removeTag: (id, tag) =>
    request("DELETE", `/notes/${encodeURIComponent(id)}/tags/${encodeURIComponent(tag)}`),

  // Metadata
  updateMeta: (id, meta) =>
    request("PUT", `/notes/${encodeURIComponent(id)}/meta`, { meta }),
};

// ── Folders ──────────────────────────────────────────────────────────────────
export const folders = {
  list: () => request("GET", "/notes/folders"),
  create: (name, parent_id = null) =>
    request("POST", "/notes/folders", { name, parent_id }),
  update: (id, data) =>
    request("PUT", `/notes/folders/${encodeURIComponent(id)}`, data),
  delete: (id) =>
    request("DELETE", `/notes/folders/${encodeURIComponent(id)}`),
};

// ── AI ───────────────────────────────────────────────────────────────────────
export const ai = {
  ask: (prompt, history = []) => request("POST", "/ai/ask", { prompt, history }),
  summarize: (text) => request("POST", "/ai/summarize", { text }),
  suggestTags: (text) => request("POST", "/ai/suggest-tags", { text }),
};

// ── Dashboard ────────────────────────────────────────────────────────────────
export const dashboard = {
  stats: () => request("GET", "/dashboard/stats"),
  recent: () => request("GET", "/dashboard/recent"),
};

// ── Settings ─────────────────────────────────────────────────────────────────
export const settings = {
  get: () => request("GET", "/settings"),
  update: (data) => request("PUT", "/settings", data),
};

// ── Users (admin) ────────────────────────────────────────────────────────────
export const users = {
  list: () => request("GET", "/users"),
  get: (id) => request("GET", `/users/${id}`),
  updateRole: (id, roles) => request("PUT", `/users/${id}/roles`, { roles }),
  disable: (id) => request("POST", `/users/${id}/disable`),
  enable: (id) => request("POST", `/users/${id}/enable`),
  resetPassword: (id, newPw) =>
    request("POST", `/users/${id}/reset-password`, { new_password: newPw }),
};

// ── Invites (admin) ──────────────────────────────────────────────────────────
export const invites = {
  list: () => request("GET", "/invites"),
  generate: () => request("POST", "/invites"),
  revoke: (id) => request("DELETE", `/invites/${id}`),
};

// ── Sessions ─────────────────────────────────────────────────────────────────
export const sessions = {
  list: (vaultId, skip = 0, limit = 50) => {
    const params = new URLSearchParams({ vault_id: vaultId, skip, limit });
    return request("GET", `/sessions?${params.toString()}`);
  },
  get: (id) => request("GET", `/sessions/${encodeURIComponent(id)}`),
  create: (data) => request("POST", "/sessions", data),
  update: (id, data) => request("PUT", `/sessions/${encodeURIComponent(id)}`, data),
  delete: (id) => request("DELETE", `/sessions/${encodeURIComponent(id)}`),
  generateRecap: (id) => request("POST", `/sessions/${encodeURIComponent(id)}/recap`),
};

// ── Characters ────────────────────────────────────────────────────────────────
export const characters = {
  list: (vaultId = "default", type = null) => {
    const params = new URLSearchParams({ vault_id: vaultId });
    if (type) params.set("type", type);
    return request("GET", `/characters?${params}`);
  },
  get: (id) => request("GET", `/characters/${id}`),
  create: (data) => request("POST", "/characters", data),
  update: (id, data) => request("PUT", `/characters/${id}`, data),
  delete: (id) => request("DELETE", `/characters/${id}`),
};

// ── Debug (admin) ─────────────────────────────────────────────────────────────
export const debug = {
  listCrashLogs: () => request("GET", "/debug/crash-logs"),
  getCrashLog: (filename) => request("GET", `/debug/crash-logs/${encodeURIComponent(filename)}`),
  deleteCrashLog: (filename) => request("DELETE", `/debug/crash-logs/${encodeURIComponent(filename)}`),
  getRuntimeLog: () => request("GET", "/debug/runtime-log"),
};
