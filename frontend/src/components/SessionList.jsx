import React, { useState, useEffect, useRef } from "react";
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
  const [mode, setMode] = useState(""); // "create" or "join"
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [reloading, setReloading] = useState(false);
  const sessionsRef = useRef(null);

  useEffect(() => {
    fetchSessions();
    // Refresh sessions every 5 seconds
    const interval = setInterval(fetchSessions, 5001);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (showCreateModal) {
      document.body.classList.add('modal-open');
    } else {
      document.body.classList.remove('modal-open');
    }
    return () => {
      document.body.classList.remove('modal-open');
    };
  }, [showCreateModal]);

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
      setShowCreateModal(false); // Close modal on success
      await fetchSessions();
      onCreateSession?.(newSession);
    } catch (err) {
      setError("Failed to create session");
      console.error("Error creating session:", err);
    } finally {
      setCreating(false);
    }
  };

  const handleCloseModal = () => {
    setShowCreateModal(false);
    setNewSessionName("");
    setVideoUrl("");
    setError(null);
  };

  const smoothScrollTo = (element, duration = 1000) => {
    const targetPosition = element.offsetTop;
    const startPosition = window.pageYOffset;
    const distance = targetPosition - startPosition;
    let startTime = null;

    const easeInOutCubic = (t) => {
      return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
    };

    const animation = (currentTime) => {
      if (startTime === null) startTime = currentTime;
      const timeElapsed = currentTime - startTime;
      const progress = Math.min(timeElapsed / duration, 1);
      const ease = easeInOutCubic(progress);

      window.scrollTo(0, startPosition + distance * ease);

      if (progress < 1) {
        requestAnimationFrame(animation);
      }
    };

    requestAnimationFrame(animation);
  };

  const handleJoinModeClick = () => {
    setMode("join");
    // Add smooth transition class and scroll to sessions section
    const sessionsSection = sessionsRef.current;
    if (sessionsSection) {
      sessionsSection.classList.add("sessions-transitioning");

      // Use custom smooth scroll with longer duration
      setTimeout(() => {
        smoothScrollTo(sessionsSection, 1200);
        // Remove transition class after animation
        setTimeout(() => {
          sessionsSection.classList.remove("sessions-transitioning");
        }, 1200);
      }, 100);
    }
  };

  const handleReloadSessions = async () => {
    setReloading(true);
    try {
      const data = await sessionAPI.getAllSessions();
      setSessions(data);
      setError(null);
    } catch (err) {
      setError("Failed to load sessions");
      console.error("Error fetching sessions:", err);
    } finally {
      setReloading(false);
    }
  };

  const handleBackToTop = () => {
    const startPosition = window.pageYOffset;
    const duration = 1000;
    let startTime = null;

    const easeInOutCubic = (t) => {
      return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
    };

    const animation = (currentTime) => {
      if (startTime === null) startTime = currentTime;
      const timeElapsed = currentTime - startTime;
      const progress = Math.min(timeElapsed / duration, 1);
      const ease = easeInOutCubic(progress);

      window.scrollTo(0, startPosition * (1 - ease));

      if (progress < 1) {
        requestAnimationFrame(animation);
      }
    };

    requestAnimationFrame(animation);
  };

  const getVideoThumbnail = (url) => {
    if (!url) return null;

    // Extract YouTube video ID
    const youtubeMatch = url.match(
      /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/
    );
    if (youtubeMatch) {
      return `https://img.youtube.com/vi/${youtubeMatch[1]}/mqdefault.jpg`;
    }
    return null;
  };

  const getTimeAgo = (dateString) => {
    const now = new Date();
    const sessionDate = new Date(dateString);
    const diffInMinutes = Math.floor((now - sessionDate) / (1000 * 60));

    if (diffInMinutes < 1) return "Just now";
    if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`;

    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours} hours ago`;

    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays} days ago`;
  };

  if (loading) {
    return <div className="session-list-loading">Loading sessions...</div>;
  }

  return (
    <div className="session-list">
      {/* Main Landing Section */}
      <div className="landing-section">
        <div className="landing-content">
          {/* Welcome text */}
          <div className="welcome-text">
            <h1>Welcome to Componion</h1>
            <p>Ask while watching videos</p>
          </div>

          {/* Right side - Action buttons */}
          <div className="landing-actions">
            <div className="action-buttons">
              <button
                className="action-button create-button"
                onClick={() => setShowCreateModal(true)}
              >
                <div className="button-content">
                  <h3>Create New Session</h3>
                  <p>Start a new video chat room</p>
                </div>
              </button>

              <button
                className="action-button join-button"
                onClick={handleJoinModeClick}
              >
                <div className="button-content">
                  <h3>Join Existing Session</h3>
                  <p>Browse and join active rooms</p>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Create Session Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create New Session</h2>
              <button className="modal-close" onClick={handleCloseModal}>
                ×
              </button>
            </div>

            <form
              onSubmit={handleCreateSession}
              className="create-session-form"
            >
              <div className="form-row">
                <div className="form-group">
                  <label>Room Name</label>
                  <input
                    type="text"
                    placeholder="Enter a fun room name..."
                    value={newSessionName}
                    onChange={(e) => setNewSessionName(e.target.value)}
                    maxLength={100}
                    required
                    autoFocus
                  />
                </div>

                <div className="form-group">
                  <label>Video URL</label>
                  <input
                    type="url"
                    placeholder="YouTube video URL"
                    value={videoUrl}
                    onChange={(e) => setVideoUrl(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={isMasterSession}
                    onChange={(e) => setIsMasterSession(e.target.checked)}
                  />
                  <span>
                    Create demo video player (shows future integration)
                  </span>
                </label>
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="cancel-button"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !newSessionName.trim()}
                  className="submit-button"
                >
                  {creating ? "Creating..." : "Create Session"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Sessions List */}
      <div className="sessions-section" ref={sessionsRef}>
        <div className="sessions-header-container">
          <div className="sessions-header">
            <div className="header-left">
              <h2>Active Sessions ({sessions.length})</h2>
              <p className="header-subtitle">
                Join a session to watch videos together
              </p>
            </div>
            <div className="header-buttons">
              <button
                onClick={handleReloadSessions}
                className="reload-button"
                disabled={reloading}
                title="Refresh session list"
              >
                ↻
              </button>
            </div>
          </div>
        </div>

        {sessions.length === 0 ? (
          <div className="no-sessions">
            <div className="no-sessions-icon">🎭</div>
            <h3>No active sessions yet</h3>
            <p>Be the first to create a session and start watching together!</p>
            <button
              className="create-first-button"
              onClick={() => setMode("create")}
            >
              Create First Session
            </button>
          </div>
        ) : (
          <div className="sessions-grid">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`session-card ${reloading ? "loading" : ""}`}
              >
                {reloading && (
                  <div className="card-loading-overlay">
                    <div className="card-spinner">🔄</div>
                  </div>
                )}

                {session.video_url && (
                  <div className="session-thumbnail">
                    <img
                      src={
                        getVideoThumbnail(session.video_url) ||
                        "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDMwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjZTllY2VmIi8+Cjx0ZXh0IHg9IjE1MCIgeT0iMTAwIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiM2NjYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiPvCfk7ogVmlkZW88L3RleHQ+Cjwvc3ZnPg=="
                      }
                      alt="Video thumbnail"
                      onError={(e) => {
                        e.target.src =
                          "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDMwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbGzPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjZTllY2VmIi8+Cjx0ZXh0IHg9IjE1MCIgeT0iMTAwIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiM2NjYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiPvCfk7ogVmlkZW88L3RleHQ+Cjwvc3ZnPg==";
                      }}
                    />
                  </div>
                )}

                <div className="session-info">
                  <h3 className="session-name">{session.name}</h3>

                  {session.video_url && (
                    <div className="session-video-url">
                      <span className="video-text">
                        {session.video_url.length > 40
                          ? session.video_url.substring(0, 40) + "..."
                          : session.video_url}
                      </span>
                    </div>
                  )}

                  <div className="session-meta">
                    <div className="meta-item">
                      <span>
                        {session.user_count} participant
                        {session.user_count !== 1 ? "s" : ""}
                      </span>
                    </div>

                    <div className="meta-item">
                      <span>{getTimeAgo(session.created_at)}</span>
                    </div>

                    {/* {session.is_master && (
                      <div className="meta-item demo-badge">
                        <span className="meta-icon">🎬</span>
                        <span>Demo Session</span>
                      </div>
                    )} */}
                  </div>
                  <button
                    className="join-session-button"
                    onClick={() => onJoinSession(session)}
                  >
                    {session.is_master ? "Join Watch Session" : "Join Session"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SessionList;