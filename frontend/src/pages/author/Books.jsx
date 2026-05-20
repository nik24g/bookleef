import { useEffect, useState } from "react";
import Layout from "../../components/Layout";
import { fetchBooks } from "../../api/client";

const authorLinks = [
  { to: "/author/books", label: "My Books" },
  { to: "/author/tickets", label: "My Tickets" },
  { to: "/author/tickets/new", label: "New Ticket" },
];

export default function Books() {
  const [books, setBooks] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchBooks()
      .then(setBooks)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <Layout links={authorLinks}>
      <h2>My Books</h2>
      {error && <p className="error">{error}</p>}

      {books.length === 0 ? (
        <p className="muted">No books found.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>ISBN</th>
                <th>Genre</th>
                <th>Published</th>
                <th>Status</th>
                <th>MRP</th>
                <th>Sold</th>
                <th>Earned</th>
                <th>Paid</th>
                <th>Pending</th>
              </tr>
            </thead>
            <tbody>
              {books.map((book) => (
                <tr key={book.id}>
                  <td>{book.title}</td>
                  <td>{book.isbn || "—"}</td>
                  <td>{book.genre}</td>
                  <td>{book.publication_date || "—"}</td>
                  <td>{book.status}</td>
                  <td>{book.mrp != null ? `₹${book.mrp}` : "—"}</td>
                  <td>{book.total_copies_sold}</td>
                  <td>₹{book.total_royalty_earned}</td>
                  <td>₹{book.royalty_paid}</td>
                  <td>₹{book.royalty_pending}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Layout>
  );
}
