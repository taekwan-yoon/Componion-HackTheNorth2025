import React, { useState, useEffect } from "react";
import { videoAPI } from "../services/api";
import "./VideoProcessingStatus.css";

const VideoProcessingStatus = ({ videoUrl, sessionId, onProcessingComplete }) => {
  const [status, setStatus] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (videoUrl) {
      checkVideoStatus();
    }
  }, [videoUrl]);

  // Also check status when component first mounts to get accurate initial state
  useEffect(() => {
    if (videoUrl) {
      // Delay initial check to avoid race conditions
      const timer = setTimeout(() => {
        checkVideoStatus();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, []);

  const checkVideoStatus = async () => {
    try {
      const statusData = await videoAPI.getProcessingStatus(videoUrl);
      setStatus(statusData);
      
      if (statusData.status === 'completed') {
        setIsProcessing(false);
        onProcessingComplete && onProcessingComplete();
        return;
      } else if (statusData.status === 'processing' || statusData.status === 'pending') {
        setTimeout(checkVideoStatus, 2000);
      } else if (statusData.status === 'failed') {
        setIsProcessing(false);
        setError(statusData.error_message || "Processing failed");
      }
    } catch (err) {
      // Don't stop polling on errors - just continue trying
      console.error("Error checking video status:", err);
      setTimeout(checkVideoStatus, 3000);
    }
  };

  const startProcessing = async () => {
    try {
      setIsProcessing(true);
      setError(null);
      
      const result = await videoAPI.processVideo(videoUrl, sessionId);
      console.log("Processing started:", result);
      
      // Start polling for status updates
      setTimeout(checkVideoStatus, 1000);
      
    } catch (err) {
      console.error("Error starting video processing:", err);
      setError("Failed to start video processing");
      setIsProcessing(false);
    }
  };

  const getStatusDisplay = () => {
    if (!status && !isProcessing) return "Checking video status...";
    
    if (isProcessing || (status && (status.status === 'pending' || status.status === 'processing'))) {
      return "Processing video...";
    }
    
    if (status && status.status === 'completed') {
      return "Video processing completed!";
    }
    
    if (status && status.status === 'failed') {
      return `Processing failed: ${status.error_message || 'Unknown error'}`;
    }
    
    return "Video not processed yet";
  };

  const showProcessButton = () => {
    return status && status.status === 'not_started' && !isProcessing;
  };

  const showProcessingIndicator = () => {
    return isProcessing || (status && (status.status === 'pending' || status.status === 'processing'));
  };

  if (error) {
    return (
      <div className="video-processing-status error">
        <h3>❌ Error</h3>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="video-processing-status">
      <h3>📹 Video Processing Status</h3>
      <p className="status-text">{getStatusDisplay()}</p>
      
      
      {showProcessButton() && (
        <div className="process-video-prompt">
          <p>⚠️ This video hasn't been processed yet. Processing is required for AI analysis.</p>
          <p>Video processing may take a few minutes depending on video length.</p>
          <button 
            className="process-button"
            onClick={startProcessing}
            disabled={isProcessing}
          >
            {isProcessing ? 'Starting...' : 'Process Video'}
          </button>
        </div>
      )}
      
      {status && status.status === 'completed' && (
        <div className="completion-message">
          <p>✅ Video is ready for AI analysis!</p>
        </div>
      )}
    </div>
  );
};

export default VideoProcessingStatus;