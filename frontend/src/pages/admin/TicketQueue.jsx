import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/Layout";
import { fetchAdminTickets } from "../../api/client";

const adminLinks = [{ to: "/admin/tickets", label: "Ticket Queue" }];

const POLL_MS = 5000;

export default function TicketQueue() {
  const [tickets, setTickets] = useState([]);
  const [filters, setFilters] = useState({
    status: "",
    category: "",
    priority: "",
    date_from: "",
    date_to: "",
  });
  const [error, setError] = useState("");

  function load() {
    const params = {};
    if (filters.status) params.status = filters.status;
    if (filters.category) params.category = filters.category;
    if (filters.priority) params.priority = filters.priority;
    if (filters.date_from) params.date_from = filters.date_from;
    if (filters.date_to) params.date_to = filters.date_to;

    fetchAdminTickets(params)
      .then(setTickets)
      .catch((e) => setError(e.message));
  }

  useEffect(() => {
    load();
    const timer = setInterval(load, POLL_MS);
    return () => clearInterval(timer);
  }, [filters]);

  return (
    <Layout links={adminLinks}>
      <h2>Ticket Queue</h2>
      <p className="muted">Sorted by priority (Critical first), then oldest first.</p>

      <div className="filters card">
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
        >
          <option value="">All statuses</option>
          <option>Open</option>
          <option>In Progress</option>
          <option>Resolved</option>
          <option>Closed</option>
        </select>
        <select
          value={filters.category}
          onChange={(e) => setFilters({ ...filters, category: e.target.value })}
        >
          <option value="">All categories</option>
          <option>Royalty & Payments</option>
          <option>ISBN & Metadata Issues</option>
          <option>Printing & Quality</option>
          <option>Distribution & Availability</option>
          <option>Book Status & Production Updates</option>
          <option>General Inquiry</option>
        </select>
        <select
          value={filters.priority}
          onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
        >
          <option value="">All priorities</option>
          <option>Critical</option>
          <option>High</option>
          <option>Medium</option>
          <option>Low</option>
        </select>
        <label className="filter-date">
          From
          <input
            type="date"
            value={filters.date_from}
            onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
          />
        </label>
        <label className="filter-date">
          To
          <input
            type="date"
            value={filters.date_to}
            onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
          />
        </label>
      </div>

      {error && <p className="error">{error}</p>}

      {tickets.length === 0 ? (
        <p className="muted">No tickets match your filters.</p>
      ) : (
        <ul className="ticket-list">
          {tickets.map((t) => (
            <li key={t.id} className={`card ticket-card priority-${t.priority}`}>
              <div className="ticket-head">
                <Link to={`/admin/tickets/${t.id}`}>
                  <strong>{t.subject}</strong>
                </Link>
                <span className={`badge priority-${t.priority}`}>{t.priority}</span>
              </div>
              <p className="muted">
                {t.author_name} · {t.category} · <span className="badge">{t.status}</span>
                {t.created_at ? ` · ${new Date(t.created_at).toLocaleDateString()}` : ""}
              </p>
              <p>
                {t.description.length > 100 ? `${t.description.slice(0, 100)}…` : t.description}
              </p>
            </li>
          ))}
        </ul>
      )}
    </Layout>
  );
}
