const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

function getToken() {
  return localStorage.getItem("access_token");
}

export async function api(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  let data = null;
  const text = await response.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!response.ok) {
    const message = data?.detail || data?.message || "Request failed";
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  return data;
}

export function login(email, password) {
  return api("/auth/login/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function fetchMe() {
  return api("/auth/me/");
}

export function fetchBooks() {
  return api("/books/");
}

export function fetchTickets() {
  return api("/tickets/");
}

export function fetchTicket(id) {
  return api(`/tickets/${id}/`);
}

export function createTicket(payload) {
  return api("/tickets/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchAdminTickets(params = {}) {
  const query = new URLSearchParams(params).toString();
  const suffix = query ? `?${query}` : "";
  return api(`/admin/tickets/${suffix}`);
}

export function fetchAdminTicket(id) {
  return api(`/admin/tickets/${id}/`);
}

export function updateAdminTicket(id, payload) {
  return api(`/admin/tickets/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function replyToTicket(id, body) {
  return api(`/admin/tickets/${id}/reply/`, {
    method: "POST",
    body: JSON.stringify({ body }),
  });
}

export function addInternalNote(id, note) {
  return api(`/admin/tickets/${id}/notes/`, {
    method: "POST",
    body: JSON.stringify({ note }),
  });
}

export function assignTicketToMe(id) {
  return api(`/admin/tickets/${id}/assign-me/`, { method: "POST" });
}

export function regenerateDraft(id) {
  return api(`/admin/tickets/${id}/regenerate-draft/`, { method: "POST" });
}
