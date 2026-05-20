import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../../components/Layout";
import { createTicket, fetchBooks } from "../../api/client";

const authorLinks = [
  { to: "/author/books", label: "My Books" },
  { to: "/author/tickets", label: "My Tickets" },
  { to: "/author/tickets/new", label: "New Ticket" },
];

export default function NewTicket() {
  const navigate = useNavigate();
  const [books, setBooks] = useState([]);
  const [bookId, setBookId] = useState("");
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchBooks().then(setBooks).catch((e) => setError(e.message));
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = {
        subject,
        description,
        book: bookId ? Number(bookId) : null,
      };
      const ticket = await createTicket(payload);
      navigate(`/author/tickets/${ticket.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout links={authorLinks}>
      <h2>Submit a Support Query</h2>
      <form className="card form-card" onSubmit={handleSubmit}>
        <label>
          Related book
          <select value={bookId} onChange={(e) => setBookId(e.target.value)}>
            <option value="">General / Account Level</option>
            {books.map((b) => (
              <option key={b.id} value={b.id}>
                {b.title} ({b.book_id})
              </option>
            ))}
          </select>
        </label>

        <label>
          Subject
          <input value={subject} onChange={(e) => setSubject(e.target.value)} required />
        </label>

        <label>
          Description
          <textarea
            rows={6}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
          />
        </label>

        <label className="muted">
          Attachment (optional)
          <input type="file" disabled title="UI only — not uploaded in this version" />
        </label>

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={loading}>
          {loading ? "Submitting..." : "Submit ticket"}
        </button>
      </form>
    </Layout>
  );
}
