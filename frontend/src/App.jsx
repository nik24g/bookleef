import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Login from "./pages/Login";
import Books from "./pages/author/Books";
import NewTicket from "./pages/author/NewTicket";
import TicketDetail from "./pages/author/TicketDetail";
import Tickets from "./pages/author/Tickets";
import AdminTicketDetail from "./pages/admin/TicketDetail";
import TicketQueue from "./pages/admin/TicketQueue";

function PrivateRoute({ children, role }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="center">Loading...</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (role && user.role !== role) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/author/books"
        element={
          <PrivateRoute role="author">
            <Books />
          </PrivateRoute>
        }
      />
      <Route
        path="/author/tickets"
        element={
          <PrivateRoute role="author">
            <Tickets />
          </PrivateRoute>
        }
      />
      <Route
        path="/author/tickets/new"
        element={
          <PrivateRoute role="author">
            <NewTicket />
          </PrivateRoute>
        }
      />
      <Route
        path="/author/tickets/:id"
        element={
          <PrivateRoute role="author">
            <TicketDetail />
          </PrivateRoute>
        }
      />
      <Route
        path="/admin/tickets"
        element={
          <PrivateRoute role="admin">
            <TicketQueue />
          </PrivateRoute>
        }
      />
      <Route
        path="/admin/tickets/:id"
        element={
          <PrivateRoute role="admin">
            <AdminTicketDetail />
          </PrivateRoute>
        }
      />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
