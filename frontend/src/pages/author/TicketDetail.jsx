import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Layout from "../../components/Layout";
import { fetchTicket } from "../../api/client";

const authorLinks = [
  { to: "/author/books", label: "My Books" },
  { to: "/author/tickets", label: "My Tickets" },
  { to: "/author/tickets/new", label: "New Ticket" },
];

const POLL_MS = 5000;

export default function TicketDetail() {
  const { id } = useParams();
  const [ticket, setTicket] = useState(null);
  const [error, setError] = useState("");

  function load() {
    fetchTicket(id)
      .then(setTicket)
      .catch((e) => setError(e.message));
  }

  useEffect(() => {
    load();
    const timer = setInterval(load, POLL_MS);
    return () => clearInterval(timer);
  }, [id]);

  if (!ticket && !error) return <Layout links={authorLinks}><p>Loading...</p></Layout>;

  return (
    <Layout links={authorLinks}>
      <h2>{ticket?.subject}</h2>
      {error && <p className="error">{error}</p>}
      {ticket && (
        <>
          <p>
            <span className={`badge status-${ticket.status.replace(/\s/g, "")}`}>{ticket.status}</span>{" "}
            {ticket.category} · {ticket.priority}
          </p>
          <p className="card">{ticket.description}</p>

          <h3>Conversation</h3>
          {ticket.messages?.length === 0 ? (
            <p className="muted">No replies yet. Our team will respond soon.</p>
          ) : (
            <ul className="messages">
              {ticket.messages.map((m) => (
                <li key={m.id} className="card">
                  <p className="muted">{m.sender_email} · {new Date(m.created_at).toLocaleString()}</p>
                  <p style={{ whiteSpace: "pre-wrap" }}>{m.body}</p>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </Layout>
  );
}
