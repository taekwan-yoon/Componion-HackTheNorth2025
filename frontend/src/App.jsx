import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useNavigate,
} from "react-router-dom";
import SessionList from "./components/SessionList";
import SessionRoom from "./components/SessionRoom";
import MasterSessionRoom from "./components/MasterSessionRoom";
import "./App.css";

function HomePage() {
  const navigate = useNavigate();

  const handleJoinSession = (session) => {
    navigate(`/session/${session.id}`);
  };

  const handleCreateSession = (sessionData) => {
    if (sessionData.session && sessionData.session.is_master) {
      // If it's a master session, navigate to master view
      navigate(`/master/${sessionData.session.id}`);
    } else {
      navigate(`/session/${sessionData.session?.id || sessionData.id}`);
    }
  };

  return (
    <SessionList
      onJoinSession={handleJoinSession}
      onCreateSession={handleCreateSession}
    />
  );
}

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/session/:sessionId" element={<SessionRoom />} />
          <Route path="/master/:sessionId" element={<MasterSessionRoom />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
