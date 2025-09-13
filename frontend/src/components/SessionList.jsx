import React, { useState, useEffect } from "react";
import { sessionAPI } from "../services/api";
import "./SessionList.css";

const SessionList = ({ onJoinSession, onCreateSession }) => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newSessionName, setNewSessionName] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [isMasterSession, setIsMasterSession] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchSessions();
    // Refresh sessions every 5 seconds
    const interval = setInterval(fetchSessions, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchSessions = async () => {
    try {
      const data = await sessionAPI.getAllSessions();
      setSessions(data);
      setError(null);
    } catch (err) {
      setError("Failed to load sessions");
      console.error("Error fetching sessions:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async (e) => {
    e.preventDefault();
    if (!newSessionName.trim()) return;

    setCreating(true);
    try {
      const newSession = await sessionAPI.createSession({
        name: newSessionName.trim(),
        video_url: videoUrl.trim() || null,
        is_master: isMasterSession,
      });
      setNewSessionName("");
      setVideoUrl("");
      await fetchSessions();
      onCreateSession?.(newSession);
    } catch (err) {
      setError("Failed to create session");
      console.error("Error creating session:", err);
    } finally {
      setCreating(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (loading) {
    return <div className="session-list-loading">Loading sessions...</div>;
  }

  return (
    <div className="session-list">
      <div className="session-list-header">
        <h1>Video Chat Sessions</h1>
        <p>Join an existing session or create a new one to start chatting!</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="create-session">
        <h2>Create New Session</h2>
        <form onSubmit={handleCreateSession} className="create-session-form">
          <div className="form-group">
            <input
              type="text"
              placeholder="Enter session name..."
              value={newSessionName}
              onChange={(e) => setNewSessionName(e.target.value)}
              maxLength={100}
              required
            />
          </div>

          <div className="form-group">
            <input
              type="url"
              placeholder="YouTube video URL (optional)"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
            />
          </div>

          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={isMasterSession}
                onChange={(e) => setIsMasterSession(e.target.checked)}
              />
              <span>Create demo video player (shows future integration)</span>
            </label>
          </div>

          <button type="submit" disabled={creating || !newSessionName.trim()}>
            {creating ? "Creating..." : "Create Session"}
          </button>
        </form>
      </div>

      <div className="sessions-section">
        <h2>Active Sessions ({sessions.length})</h2>
        {sessions.length === 0 ? (
          <div className="no-sessions">
            <p>No active sessions found. Create the first one!</p>
          </div>
        ) : (
          <div className="sessions-grid">
            {sessions.map((session) => (
              <div key={session.id} className="session-card">
                <div className="session-info">
                  <h3 className="session-name">{session.name}</h3>
                  <div className="session-meta">
                    <span className="user-count">
                      👥 {session.user_count} user
                      {session.user_count !== 1 ? "s" : ""}
                    </span>
                    {session.is_master && (
                      <span className="master-badge">🎬 Demo</span>
                    )}
                    {session.video_url && (
                      <span className="video-badge">📺 Video</span>
                    )}
                    <span className="created-date">
                      Created: {formatDate(session.created_at)}
                    </span>
                  </div>
                </div>
                <button
                  className="join-button"
                  onClick={() => onJoinSession(session)}
                >
                  {session.is_master ? "Join Study Session" : "Join Session"}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SessionList;
