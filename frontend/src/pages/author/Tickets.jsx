import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/Layout";
import { fetchTickets } from "../../api/client";

const authorLinks = [
  { to: "/author/books", label: "My Books" },
  { to: "/author/tickets", label: "My Tickets" },
  { to: "/author/tickets/new", label: "New Ticket" },
];

const POLL_MS = 5000;

export default function Tickets() {
  const [tickets, setTickets] = useState([]);
  const [error, setError] = useState("");

  function load() {
    fetchTickets()
      .then(setTickets)
      .catch((e) => setError(e.message));
  }

  useEffect(() => {
    load();
    const timer = setInterval(load, POLL_MS);
    return () => clearInterval(timer);
  }, []);

  return (
    <Layout links={authorLinks}>
      <h2>My Tickets</h2>
      <p className="muted">Auto-refreshes every 5 seconds when admin replies.</p>
      {error && <p className="error">{error}</p>}

      {tickets.length === 0 ? (
        <p className="muted">No tickets yet. <Link to="/author/tickets/new">Create one</Link></p>
      ) : (
        <ul className="ticket-list">
          {tickets.map((t) => (
            <li key={t.id} className="card ticket-card">
              <div className="ticket-head">
                <Link to={`/author/tickets/${t.id}`}>
                  <strong>{t.subject}</strong>
                </Link>
                <span className={`badge status-${t.status.replace(/\s/g, "")}`}>{t.status}</span>
              </div>
              <p className="muted">
                {t.category} · {t.priority}
                {t.book_title ? ` · ${t.book_title}` : " · General"}
              </p>
              <p>
                <strong>Your query:</strong> {t.description.slice(0, 120)}
                {t.description.length > 120 ? "…" : ""}
              </p>
              {t.latest_reply ? (
                <p className="reply-preview">
                  <strong>Latest reply:</strong> {t.latest_reply.body.slice(0, 120)}
                  {t.latest_reply.body.length > 120 ? "…" : ""}
                  <span className="muted"> — {t.latest_reply.sender_email}</span>
                </p>
              ) : (
                <p className="muted">No reply yet.</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </Layout>
  );
}
