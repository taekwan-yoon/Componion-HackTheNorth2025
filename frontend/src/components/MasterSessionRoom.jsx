import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import VideoPlayer from "./VideoPlayer";
import ChatBox from "./ChatBox";
import UserList from "./UserList";
import VideoProcessingStatus from "./VideoProcessingStatus";
import socketService from "../services/socket";
import { sessionAPI } from "../services/api";
import "./SessionRoom.css";

const MasterSessionRoom = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [users, setUsers] = useState([]);
  const [messages, setMessages] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentVideoTime, setCurrentVideoTime] = useState(0);
  const [videoProcessed, setVideoProcessed] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isChatCollapsed, setIsChatCollapsed] = useState(false);

  useEffect(() => {
    const initializeSession = async () => {
      try {
        // Connect to socket
        socketService.connect();

        // Set up socket event listeners
        setupSocketListeners();

        // Join the session as master
        socketService.joinSession(sessionId, true, "Session Master");
      } catch (err) {
        setError("Failed to connect to session");
        console.error("Session initialization error:", err);
      }
    };

    initializeSession();
    return () => {
      // Cleanup socket listeners and disconnect
      socketService.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const setupSocketListeners = () => {
    socketService.onJoinConfirmed((data) => {
      console.log("Master join confirmed:", data);
      setSession(data.session);
      setCurrentUser({
        user_id: data.user_id,
        display_name: data.display_name,
      });
      setIsConnected(true);
      setVideoProcessed(data.session?.video_processed || false);
      setLoading(false);
    });

    socketService.onSessionUsers((users) => {
      setUsers(users);
    });

    socketService.onChatHistory((messages) => {
      setMessages(messages);
    });

    socketService.onNewMessage((message) => {
      setMessages((prev) => [...prev, message]);
    });

    socketService.onUserJoined((data) => {
      console.log("User joined:", data.display_name);
    });

    socketService.onUserLeft((data) => {
      console.log("User left:", data.display_name);
    });

    socketService.onTimeRequested((data) => {
      // Send current video time to requesting user
      socketService.sendCurrentTime(data.requester_id, currentVideoTime);
    });

    socketService.onError((error) => {
      console.error("Socket error:", error);
      setError(error.message || "Connection error");
      if (error.message === "Session not found") {
        navigate("/");
      }
    });

    // Handle socket connection status
    const socket = socketService.connect();
    socket.on("connect", () => {
      setIsConnected(true);
    });

    socket.on("disconnect", () => {
      setIsConnected(false);
    });
  };

  const handleLeaveSession = () => {
    socketService.disconnect();
    navigate("/");
  };

  const handleSendMessage = (message, videoTimestamp, queryMode, startTime, endTime) => {
    socketService.sendMessage(message, videoTimestamp, queryMode, startTime, endTime);
  };

  const handleAskQuestion = async (question) => {
    try {
      // Add user's question to chat first
      const userQuestion = {
        id: Date.now() + Math.random(),
        message: question,
        message_type: "user",
        user_id: currentUser?.user_id || "user",
        display_name: currentUser?.display_name || "You",
        created_at: new Date().toISOString(),
        is_ai_directed: true, // Mark as AI-directed
      };

      setMessages((prev) => [...prev, userQuestion]);

      // Call the REST API endpoint with video timestamp context
      const response = await sessionAPI.askAI(
        question,
        sessionId,
        currentUser?.user_id || "user",
        currentVideoTime
      );

      // Create AI response message
      const aiMessage = {
        id: Date.now() + Math.random() + 1,
        message: response.answer,
        message_type: "ai",
        user_id: "ai_assistant",
        display_name: "AI Assistant",
        created_at: response.timestamp || new Date().toISOString(),
        reply_to_message_id: userQuestion.id,
        reply_to_message: question, // Include the original question text for preview
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Error asking AI question:", error);

      // Show error message in chat
      const errorMessage = {
        id: Date.now() + Math.random(),
        message:
          "Sorry, I couldn't process your question right now. Please try again.",
        message_type: "ai",
        user_id: "ai_assistant",
        display_name: "AI Assistant",
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const toggleChat = () => {
    setIsChatCollapsed(!isChatCollapsed);
  };

  const handleProcessingComplete = () => {
    console.log("Video processing completed - updating state");
    setVideoProcessed(true);
    // Optionally refresh session data to get updated video_processed status
    if (session) {
      setSession((prev) => ({ ...prev, video_processed: true }));
    }
  };

  if (loading) {
    return (
      <div className="session-room-loading">
        <div className="loading-content">
          <div className="loading-spinner"></div>
          <h2>Loading Video Player Demo...</h2>
          <p>Preparing integration preview</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="session-room-error">
        <div className="error-content">
          <h2>Connection Error</h2>
          <p>{error}</p>
          <button onClick={() => navigate("/")} className="back-button">
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="session-room master-session">
      <div className="session-header demo-header">
        <div className="session-title">
          <h1>Componion</h1>
        </div>
        <div className="session-actions">
          <button onClick={handleLeaveSession} className="leave-button">
            ×
          </button>
        </div>
      </div>

      <div
        className={`session-content master-content ${
          isChatCollapsed ? "chat-collapsed" : ""
        }`}
      >
        <div className="video-main-area">
          {/* Show video processing status if video URL exists but not processed */}
          {session?.video_url && !videoProcessed && (
            <VideoProcessingStatus
              videoUrl={session.video_url}
              sessionId={sessionId}
              onProcessingComplete={handleProcessingComplete}
            />
          )}

          <VideoPlayer
            videoFile={session?.video_file}
            videoUrl={session?.video_url}
            sessionName={session?.name}
            isMaster={true}
            onTimeUpdate={(time) => {
              setCurrentVideoTime(time);
              // Broadcast time updates to all participants
              socketService.sendVideoTimeUpdate(sessionId, time);
            }}
          />
        </div>

        {/* Collapsible Chat Sidebar - only show when expanded */}
        {!isChatCollapsed && (
          <div className="master-sidebar">
            <div className="chat-panel">
              <div className="chat-header">
                <button className="chat-toggle" onClick={toggleChat}>
                  −
                </button>
              </div>

              <div className="chat-content">
                <ChatBox
                  messages={messages}
                  onSendMessage={handleSendMessage}
                  onAskQuestion={handleAskQuestion}
                  currentUser={currentUser}
                  isConnected={isConnected}
                  isMaster={true}
                  currentVideoTime={currentVideoTime}
                />
                <div className="chat-sidebar">
                  <UserList users={users} currentUser={currentUser} />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Floating Chat Button - only show when collapsed */}
        {isChatCollapsed && (
          <div className="chat-panel collapsed">
            <button className="chat-toggle" onClick={toggleChat}>
              +
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MasterSessionRoom;
