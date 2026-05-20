import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Layout from "../../components/Layout";
import {
  addInternalNote,
  assignTicketToMe,
  fetchAdminTicket,
  regenerateDraft,
  replyToTicket,
  updateAdminTicket,
} from "../../api/client";

const adminLinks = [{ to: "/admin/tickets", label: "Ticket Queue" }];

export default function AdminTicketDetail() {
  const { id } = useParams();
  const [ticket, setTicket] = useState(null);
  const [reply, setReply] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function load() {
    try {
      const data = await fetchAdminTicket(id);
      setTicket(data);
      if (!reply && data.ai_draft_response) {
        setReply(data.ai_draft_response);
      }
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    load();
  }, [id]);

  async function saveMeta(field, value) {
    try {
      const updated = await updateAdminTicket(id, { [field]: value });
      setTicket(updated);
      setMessage("Updated.");
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleReply(e) {
    e.preventDefault();
    try {
      const updated = await replyToTicket(id, reply);
      setTicket(updated);
      setMessage("Reply sent to author.");
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleNote(e) {
    e.preventDefault();
    try {
      await addInternalNote(id, note);
      setNote("");
      await load();
      setMessage("Internal note saved.");
    } catch (e) {
      setError(e.message);
    }
  }

  if (!ticket) {
    return (
      <Layout links={adminLinks}>
        <p>{error || "Loading..."}</p>
      </Layout>
    );
  }

  return (
    <Layout links={adminLinks}>
      <h2>{ticket.subject}</h2>
      <p className="muted">
        {ticket.author_name} ({ticket.author_email}) · {ticket.book_title || "General"}
      </p>

      {message && <p className="success">{message}</p>}
      {error && <p className="error">{error}</p>}

      <div className="grid-2">
        <section className="card">
          <h3>Ticket controls</h3>
          <label>
            Status
            <select value={ticket.status} onChange={(e) => saveMeta("status", e.target.value)}>
              <option>Open</option>
              <option>In Progress</option>
              <option>Resolved</option>
              <option>Closed</option>
            </select>
          </label>
          <label>
            Category (override AI)
            <select value={ticket.category} onChange={(e) => saveMeta("category", e.target.value)}>
              <option>Royalty & Payments</option>
              <option>ISBN & Metadata Issues</option>
              <option>Printing & Quality</option>
              <option>Distribution & Availability</option>
              <option>Book Status & Production Updates</option>
              <option>General Inquiry</option>
            </select>
          </label>
          <label>
            Priority (override AI)
            <select value={ticket.priority} onChange={(e) => saveMeta("priority", e.target.value)}>
              <option>Critical</option>
              <option>High</option>
              <option>Medium</option>
              <option>Low</option>
            </select>
          </label>
          <button type="button" onClick={() => assignTicketToMe(id).then(load)}>
            Assign to me
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() =>
              regenerateDraft(id).then((r) => {
                setReply(r.ai_draft_response);
                setMessage("Draft regenerated.");
              })
            }
          >
            Regenerate AI draft
          </button>
        </section>

        <section className="card">
          <h3>Author message</h3>
          <p style={{ whiteSpace: "pre-wrap" }}>{ticket.description}</p>
        </section>
      </div>

      <form className="card form-card" onSubmit={handleReply}>
        <h3>Reply to author</h3>
        <textarea rows={8} value={reply} onChange={(e) => setReply(e.target.value)} required />
        <button type="submit">Send reply</button>
      </form>

      <section className="card">
        <h3>Conversation (visible to author)</h3>
        {ticket.messages?.length === 0 ? (
          <p className="muted">No messages yet.</p>
        ) : (
          <ul className="messages">
            {ticket.messages.map((m) => (
              <li key={m.id}>
                <p className="muted">{m.sender_email}</p>
                <p style={{ whiteSpace: "pre-wrap" }}>{m.body}</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <form className="card form-card" onSubmit={handleNote}>
        <h3>Internal note (admin only)</h3>
        <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} />
        <button type="submit" className="btn-secondary">
          Add note
        </button>
        <ul>
          {ticket.internal_notes?.map((n) => (
            <li key={n.id}>
              <p className="muted">{n.author_email}</p>
              <p>{n.note}</p>
            </li>
          ))}
        </ul>
      </form>
    </Layout>
  );
}
