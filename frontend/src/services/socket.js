import { io } from "socket.io-client";

const SOCKET_URL = "http://localhost:5001";

class SocketService {
  constructor() {
    this.socket = null;
    this.connected = false;
  }

  connect() {
    if (!this.socket) {
      this.socket = io(SOCKET_URL, {
        transports: ["websocket", "polling"],
      });

      this.socket.on("connect", () => {
        this.connected = true;
        console.log("Connected to server");
      });

      this.socket.on("disconnect", () => {
        this.connected = false;
        console.log("Disconnected from server");
      });

      this.socket.on("error", (error) => {
        console.error("Socket error:", error);
      });
    }

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
    }
  }

  isConnected() {
    return this.connected && this.socket?.connected;
  }

  // Session events
  joinSession(sessionId, isMaster = false, displayName = null) {
    if (this.socket) {
      this.socket.emit("join_session", {
        session_id: sessionId,
        is_master: isMaster,
        display_name: displayName,
      });
    }
  }

  sendMessage(message, videoTimestamp = 0, queryMode = 'omniscient', startTime = null, endTime = null) {
    if (this.socket) {
      this.socket.emit("send_message", { 
        message, 
        video_timestamp: videoTimestamp,
        query_mode: queryMode,
        start_time: startTime,
        end_time: endTime
      });
    }
  }

  askQuestion(question, videoTimestamp = 0) {
    if (this.socket) {
      this.socket.emit("ask_question", {
        question,
        video_timestamp: videoTimestamp,
      });
    }
  }

  // Master session events
  sendVideoTimeUpdate(sessionId, videoTime) {
    if (this.socket) {
      this.socket.emit("video_time_update", {
        session_id: sessionId,
        video_time: videoTime,
      });
    }
  }

  requestCurrentTime(sessionId) {
    if (this.socket) {
      this.socket.emit("request_current_time", {
        session_id: sessionId,
      });
    }
  }

  sendCurrentTime(requesterId, videoTime) {
    if (this.socket) {
      this.socket.emit("send_current_time", {
        requester_id: requesterId,
        video_time: videoTime,
      });
    }
  }

  // Event listeners
  onUserJoined(callback) {
    if (this.socket) {
      this.socket.on("user_joined", callback);
    }
  }

  onUserLeft(callback) {
    if (this.socket) {
      this.socket.on("user_left", callback);
    }
  }

  onNewMessage(callback) {
    if (this.socket) {
      this.socket.on("new_message", callback);
    }
  }

  onAiResponse(callback) {
    if (this.socket) {
      this.socket.on("ai_response", callback);
    }
  }

  onSessionUsers(callback) {
    if (this.socket) {
      this.socket.on("session_users", callback);
    }
  }

  onChatHistory(callback) {
    if (this.socket) {
      this.socket.on("chat_history", callback);
    }
  }

  onJoinConfirmed(callback) {
    if (this.socket) {
      this.socket.on("join_confirmed", callback);
    }
  }

  onError(callback) {
    if (this.socket) {
      this.socket.on("error", callback);
    }
  }

  // Master session event listeners
  onSyncVideoTime(callback) {
    if (this.socket) {
      this.socket.on("sync_video_time", callback);
    }
  }

  onTimeRequested(callback) {
    if (this.socket) {
      this.socket.on("time_requested", callback);
    }
  }

  onMasterDisconnected(callback) {
    if (this.socket) {
      this.socket.on("master_disconnected", callback);
    }
  }

  // Remove event listeners
  off(event, callback) {
    if (this.socket) {
      this.socket.off(event, callback);
    }
  }
}

export default new SocketService();
