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

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [needsSetup, setNeedsSetup] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Listen for 401 auth:logout events dispatched by api.js
  useEffect(() => {
    const handler = () => {
      setUser(null);
      navigate('/login');
    };
    window.addEventListener('auth:logout', handler);
    return () => window.removeEventListener('auth:logout', handler);
  }, [navigate]);

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

  const handleLogin = (token, userData) => {
    setToken(token);
    setUser(userData);
    setNeedsSetup(false);
    navigate("/");
  };

  const handleLogout = () => {
    auth.logout().catch((err) => console.error('Logout failed:', err));
    setToken(null);
    setUser(null);
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
            <Route path="/browse" element={<Browse user={user} />} />
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
