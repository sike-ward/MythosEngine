import { useState, useEffect } from "react";
import { Routes, Route, useNavigate, useLocation } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import ErrorBoundary from "./components/ErrorBoundary";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Browse from "./pages/Browse";
import Create from "./pages/Create";
import Universe from "./pages/Universe";
import Settings from "./pages/Settings";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import { auth, setToken, getToken } from "./api";
import { useSessionExpiry } from "./hooks/useSessionExpiry";

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [needsSetup, setNeedsSetup] = useState(false);
  // exp stored in memory only — not persisted to localStorage
  const [sessionExp, setSessionExp] = useState(null);
  const [expiryWarning, setExpiryWarning] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  // Try to restore session on mount, and check if first-run setup is needed
  useEffect(() => {
    const init = async () => {
      try {
        // Check if the database needs first-time setup
        const statusData = await auth.status();
        if (statusData.needs_setup) {
          setNeedsSetup(true);
          setLoading(false);
          return;
        }

        // Try to restore existing session
        const token = getToken();
        if (token) {
          try {
            const data = await auth.me();
            setUser(data.user);
            // No exp for restored sessions — token expiry handled by server 401
          } catch {
            setToken(null);
          }
        }
      } catch (err) {
        console.error("Init failed:", err);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  // Session expiry countdown (Item 56)
  useSessionExpiry(
    sessionExp,
    (mins) =>
      setExpiryWarning(
        `Your session expires in ${mins} minute${mins !== 1 ? "s" : ""}. Please save your work.`
      ),
    () => {
      setExpiryWarning(null);
      handleLogout();
    }
  );

  // exp comes from the login/setup/register response (Item 55)
  const handleLogin = (token, userData, exp = null) => {
    setToken(token);
    setUser(userData);
    setSessionExp(exp);
    setExpiryWarning(null);
    setNeedsSetup(false);
    navigate("/");
  };

  const handleLogout = () => {
    auth.logout().catch((err) => console.error('Logout failed:', err));
    setToken(null);
    setUser(null);
    setSessionExp(null);
    setExpiryWarning(null);
    navigate("/login");
  };

  if (loading) {
    return (
      <div className="h-screen bg-base flex items-center justify-center">
        <div className="text-center">
          <div className="text-3xl mb-3">⚡</div>
          <div className="text-txt-muted text-sm">Loading MythosEngine...</div>
        </div>
      </div>
    );
  }

  // Not logged in → show login (or setup if first run)
  if (!user) {
    return <Login onLogin={handleLogin} needsSetup={needsSetup} />;
  }

  return (
    <div className="h-screen flex bg-base overflow-hidden">
      {/* Session expiry warning banner */}
      {expiryWarning && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-warning/90 text-txt text-center py-2 px-4 text-sm font-medium">
          {expiryWarning}
        </div>
      )}

      {/* Sidebar */}
      <Sidebar
        currentPath={location.pathname}
        onNavigate={(path) => navigate(path)}
        onLogout={handleLogout}
        user={user}
      />

      {/* Main content area */}
      <main className="flex-1 overflow-y-auto">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<Dashboard user={user} />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/browse" element={<Browse />} />
            <Route path="/create" element={<Create />} />
            <Route path="/universe" element={<Universe />} />
            <Route path="/settings" element={<Settings user={user} />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  );
}
