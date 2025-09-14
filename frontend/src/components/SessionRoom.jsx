import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import ChatBox from "./ChatBox";
import UserList from "./UserList";
import VideoProcessingStatus from "./VideoProcessingStatus";
import socketService from "../services/socket";
import { sessionAPI, videoAPI } from "../services/api";
import "./SessionRoom.css";

const SessionRoom = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [users, setUsers] = useState([]);
  const [messages, setMessages] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [currentVideoTime, setCurrentVideoTime] = useState(0);
  const [isMaster, setIsMaster] = useState(false);
  const [videoProcessed, setVideoProcessed] = useState(false);

  useEffect(() => {
    const initializeSession = async () => {
      try {
        // Connect to socket
        socketService.connect();

        // Set up socket event listeners
        setupSocketListeners();

        // Join the session
        socketService.joinSession(sessionId, false); // Join as participant by default
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
      console.log("Join confirmed:", data);
      setSession(data.session);
      setCurrentUser({
        user_id: data.user_id,
        display_name: data.display_name,
      });
      setIsMaster(data.is_master || false);
      setIsConnected(true);
      setVideoProcessed(data.session?.video_processed || false);
      setLoading(false);

      // If not master, request current video time
      if (!data.is_master) {
        socketService.requestCurrentTime(sessionId);
      }
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
      // User list will be updated via onSessionUsers
      console.log("User joined:", data.display_name);
    });

    socketService.onUserLeft((data) => {
      // User list will be updated via onSessionUsers
      console.log("User left:", data.display_name);
    });

    socketService.onError((error) => {
      console.error("Socket error:", error);
      setError(error.message || "Connection error");
      if (error.message === "Session not found") {
        navigate("/");
      }
    });

    // Video synchronization events
    socketService.onSyncVideoTime((data) => {
      setCurrentVideoTime(data.video_time);
      console.log("Video time synced:", data.video_time);
    });

    socketService.onTimeRequested((data) => {
      // If we're the master, send current video time
      if (isMaster) {
        socketService.sendCurrentTime(data.requester_id, currentVideoTime);
      }
    });

    socketService.onMasterDisconnected(() => {
      console.log("Master disconnected");
      // Could show a notification or handle master disconnection
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
      };

      setMessages((prev) => [...prev, userQuestion]);

      // Call the REST API endpoint with video timestamp context
      const response = await sessionAPI.askAI(
        question,
        sessionId,
        currentUser?.user_id || "user",
        currentVideoTime
      );

      // Create a mock AI message to display in chat
      const aiMessage = {
        id: Date.now() + Math.random() + 1, // Ensure different ID
        message: response.answer,
        message_type: "ai",
        user_id: "ai_assistant",
        display_name: "AI Assistant",
        created_at: response.timestamp || new Date().toISOString(),
      };

      // Add the AI response to messages
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

  const handleLeaveSession = () => {
    socketService.disconnect();
    navigate("/");
  };

  // Check processing status periodically for participants
  useEffect(() => {
    if (session?.video_url && !videoProcessed) {
      const checkProcessingStatus = async () => {
        try {
          const statusData = await videoAPI.getProcessingStatus(session.video_url);
          if (statusData.status === 'completed') {
            setVideoProcessed(true);
          }
        } catch (err) {
          console.error("Error checking processing status:", err);
        }
      };

      // Check immediately and then every 3 seconds
      checkProcessingStatus();
      const interval = setInterval(checkProcessingStatus, 3000);
      
      return () => clearInterval(interval);
    }
  }, [session?.video_url, videoProcessed]);

  if (loading) {
    return (
      <div className="session-room-loading">
        <div className="loading-content">
          <div className="loading-spinner"></div>
          <h2>Joining Session...</h2>
          <p>Connecting to the session room</p>
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
    <div className="session-room">
      <div className="session-header">
        <div className="session-title">
          <h1>Componion</h1>
          <span className="session-id">{session?.name || "Session Room"}</span>
        </div>
        <button onClick={handleLeaveSession} className="leave-button">
          ×
        </button>
      </div>

      <div className="session-content participant-content">
        <div className="chat-main-area">
          {/* Show simple processing status for participants */}
          {session?.video_url && !videoProcessed && (
            <div className="video-processing-notice">
              <p>⚠️ Video is being processed. AI analysis will be available once processing is complete.</p>
            </div>
          )}
          
          <ChatBox
            messages={messages}
            onSendMessage={handleSendMessage}
            onAskQuestion={handleAskQuestion}
            currentUser={currentUser}
            isConnected={isConnected}
            videoProcessed={videoProcessed}
            currentVideoTime={currentVideoTime}
          />
        </div>
        <div className="participant-sidebar">
          <UserList users={users} currentUser={currentUser} />
        </div>
      </div>
    </div>
  );
};

export default SessionRoom;
