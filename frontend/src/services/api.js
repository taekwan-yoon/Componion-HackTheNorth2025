import axios from "axios";

const API_URL = "http://localhost:5000/api";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const sessionAPI = {
  // Get all active sessions
  getAllSessions: async () => {
    const response = await api.get("/sessions");
    return response.data;
  },

  // Create a new session
  createSession: async (sessionData) => {
    const response = await api.post("/sessions", sessionData);
    return response.data;
  },

  // Get session details
  getSession: async (sessionId) => {
    const response = await api.get(`/sessions/${sessionId}`);
    return response.data;
  },

  // Ask AI question with video timestamp context
  askAI: async (message, sessionId, userId, videoTimestamp = 0) => {
    const response = await api.post("/ask", {
      message: message,
      session_id: sessionId,
      user_id: userId,
      video_timestamp: videoTimestamp,
    });
    return response.data;
  },

  // Join a session
  joinSession: async (sessionId, userName = null) => {
    const response = await api.post(`/sessions/${sessionId}/join`, {
      user_name: userName,
    });
    return response.data;
  },
};

export const videoAPI = {
  // Start video processing
  processVideo: async (videoUrl, sessionId) => {
    const response = await api.post("/video/process", {
      video_url: videoUrl,
      session_id: sessionId,
    });
    return response.data;
  },

  // Get video processing status
  getProcessingStatus: async (videoUrl) => {
    const encodedUrl = encodeURIComponent(videoUrl);
    const response = await api.get(`/video/status/${encodedUrl}`);
    return response.data;
  },

  // Get video analysis data
  getVideoAnalysis: async (videoUrl) => {
    const encodedUrl = encodeURIComponent(videoUrl);
    const response = await api.get(`/video-analysis/${encodedUrl}`);
    return response.data;
  },
};

export default api;
