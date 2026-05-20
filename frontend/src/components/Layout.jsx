import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Layout({ children, links }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>BookLeaf</h1>
          <p className="muted">{user?.role === "admin" ? "Admin Portal" : "Author Portal"}</p>
        </div>
        <nav className="nav">
          {links.map((link) => (
            <Link key={link.to} to={link.to}>
              {link.label}
            </Link>
          ))}
          <button type="button" className="btn-link" onClick={handleLogout}>
            Logout
          </button>
        </nav>
      </header>
      <main className="main">{children}</main>
    </div>
  );
}
