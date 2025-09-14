import React, { useState, useEffect, useRef, useCallback } from "react";
import "./VideoPlayer.css";

const VideoPlayer = ({
  videoFile,
  sessionName,
  videoUrl,
  isMaster = false,
  onTimeUpdate,
  syncTime = null,
}) => {
  const [videoError, setVideoError] = useState(false);
  const [videoLoading, setVideoLoading] = useState(true);
  const [videoDuration, setVideoDuration] = useState("0:00");
  const [currentTime, setCurrentTime] = useState("0:00");
  const videoRef = useRef(null);
  const youtubePlayerRef = useRef(null);
  const timeUpdateIntervalRef = useRef(null);
  const playerInitializedRef = useRef(false);
  const mountedRef = useRef(true);
  const onTimeUpdateRef = useRef(onTimeUpdate);

  // Determine video source and YouTube status
  const isYouTube =
    videoUrl &&
    (videoUrl.includes("youtube.com") || videoUrl.includes("youtu.be"));

  useEffect(() => {
    console.log("timeupdate interval active:", !!timeUpdateIntervalRef.current);
  }, []);

  // Update the ref when onTimeUpdate changes
  useEffect(() => {
    onTimeUpdateRef.current = onTimeUpdate;
  }, [onTimeUpdate]);

  // Function to get current video time immediately
  const getCurrentVideoTime = useCallback(() => {
    if (
      isYouTube &&
      youtubePlayerRef.current &&
      youtubePlayerRef.current.getCurrentTime
    ) {
      return youtubePlayerRef.current.getCurrentTime();
    } else if (!isYouTube && videoRef.current) {
      return videoRef.current.currentTime;
    }
    return 0;
  }, [isYouTube]);

  // Expose getCurrentVideoTime to parent component
  useEffect(() => {
    if (onTimeUpdate && typeof onTimeUpdate === "function") {
      // Add the getCurrentVideoTime function as a property
      onTimeUpdate.getCurrentVideoTime = getCurrentVideoTime;
    }
  }, [onTimeUpdate, getCurrentVideoTime]);

  // Load YouTube API script and initialize player
  useEffect(() => {
    if (!isYouTube) {
      setVideoLoading(false);
      return;
    }

    // Only reset if this is a genuinely new URL or if player is in error state
    const shouldReset =
      playerInitializedRef.current &&
      (youtubePlayerRef.current === null || videoError);

    if (shouldReset) {
      console.log("Resetting player state");
      playerInitializedRef.current = false;
      if (youtubePlayerRef.current && youtubePlayerRef.current.destroy) {
        youtubePlayerRef.current.destroy();
        youtubePlayerRef.current = null;
      }
      if (timeUpdateIntervalRef.current) {
        clearInterval(timeUpdateIntervalRef.current);
        timeUpdateIntervalRef.current = null;
      }
    }

    // Skip if already initialized for this URL
    if (playerInitializedRef.current && youtubePlayerRef.current) {
      console.log("Player already initialized, skipping");
      return;
    }

    console.log("Initializing YouTube player for URL:", videoUrl);

    const loadingTimeout = setTimeout(() => {
      console.warn("YouTube player loading timeout");
      setVideoLoading(false);
    }, 15000);

    const handlePlayerReady = (event) => {
      if (!mountedRef.current) return;

      console.log("YouTube player ready");
      clearTimeout(loadingTimeout);
      setVideoLoading(false);
      setVideoError(false);

      // Get video duration
      try {
        const duration = event.target.getDuration();
        if (duration) {
          const minutes = Math.floor(duration / 60);
          const seconds = Math.floor(duration % 60);
          setVideoDuration(`${minutes}:${seconds.toString().padStart(2, "0")}`);
        }
      } catch {
        console.log("Could not get duration");
      }

      // Start time polling function
      const startPolling = () => {
        // Clear any existing interval
        if (timeUpdateIntervalRef.current) {
          clearInterval(timeUpdateIntervalRef.current);
          timeUpdateIntervalRef.current = null;
        }

        console.log("Starting time polling...");
        timeUpdateIntervalRef.current = setInterval(() => {
          if (!mountedRef.current) {
            if (timeUpdateIntervalRef.current) {
              clearInterval(timeUpdateIntervalRef.current);
              timeUpdateIntervalRef.current = null;
            }
            return;
          }

          if (youtubePlayerRef.current) {
            try {
              if (
                typeof youtubePlayerRef.current.getCurrentTime === "function"
              ) {
                const time = youtubePlayerRef.current.getCurrentTime();

                if (time !== undefined && time !== null && !isNaN(time)) {
                  const minutes = Math.floor(time / 60);
                  const seconds = Math.floor(time % 60);
                  const timeString = `${minutes}:${seconds
                    .toString()
                    .padStart(2, "0")}`;
                  setCurrentTime(timeString);

                  if (onTimeUpdateRef.current) {
                    onTimeUpdateRef.current(time);
                  }

                  if (Math.floor(time) % 5 === 0 && time > 0) {
                    console.log(`YouTube time: ${timeString} (${time}s)`);
                  }
                }
              }
            } catch {
              // Silently continue
            }
          }
        }, 1000);
      };

      // Start time polling after a delay
      setTimeout(() => {
        startPolling();
      }, 1000);
    };

    const handlePlayerStateChange = (event) => {
      if (!mountedRef.current) return;
      console.log("YouTube player state:", event.data);

      // The polling is already started from onReady, no need to restart
      // unless the interval was somehow cleared
      if (event.data === 1 && !timeUpdateIntervalRef.current) {
        console.log("Video started playing, restarting time polling");
        // Restart the polling if needed
        if (timeUpdateIntervalRef.current) {
          clearInterval(timeUpdateIntervalRef.current);
        }
        timeUpdateIntervalRef.current = setInterval(() => {
          if (!mountedRef.current || !youtubePlayerRef.current) return;

          try {
            if (typeof youtubePlayerRef.current.getCurrentTime === "function") {
              const time = youtubePlayerRef.current.getCurrentTime();
              if (time !== undefined && time !== null && !isNaN(time)) {
                const minutes = Math.floor(time / 60);
                const seconds = Math.floor(time % 60);
                const timeString = `${minutes}:${seconds
                  .toString()
                  .padStart(2, "0")}`;
                setCurrentTime(timeString);
                if (onTimeUpdateRef.current) {
                  onTimeUpdateRef.current(time);
                }
              }
            }
          } catch {
            // Silently continue
          }
        }, 1000);
      }
    };

    const handlePlayerError = (event) => {
      console.error("YouTube player error:", event.data);
      clearTimeout(loadingTimeout);
      setVideoLoading(false);
      setVideoError(true);
      playerInitializedRef.current = false;
    };

    const initializePlayer = () => {
      const videoId = extractYouTubeId(videoUrl);
      if (!videoId) {
        console.error("Could not extract video ID");
        setVideoError(true);
        setVideoLoading(false);
        return;
      }

      playerInitializedRef.current = true;

      setTimeout(() => {
        const playerDiv = document.getElementById("youtube-player");
        if (!playerDiv || !mountedRef.current) {
          console.error("Player div not found or component unmounted");
          return;
        }

        console.log("Creating YouTube player...");

        try {
          youtubePlayerRef.current = new window.YT.Player("youtube-player", {
            height: "100%",
            width: "100%",
            videoId: videoId,
            playerVars: {
              autoplay: 0,
              controls: 1,
              enablejsapi: 1,
              origin: window.location.origin,
            },
            events: {
              onReady: handlePlayerReady,
              onStateChange: handlePlayerStateChange,
              onError: handlePlayerError,
            },
          });
        } catch (error) {
          console.error("Error creating player:", error);
          setVideoError(true);
          setVideoLoading(false);
          playerInitializedRef.current = false;
        }
      }, 100);
    };

    if (!window.YT) {
      console.log("Loading YouTube API...");
      const script = document.createElement("script");
      script.src = "https://www.youtube.com/iframe_api";
      script.async = true;
      document.body.appendChild(script);

      window.onYouTubeIframeAPIReady = () => {
        console.log("YouTube API loaded");
        initializePlayer();
      };
    } else if (window.YT && window.YT.Player) {
      console.log("YouTube API already loaded");
      initializePlayer();
    }

    return () => {
      clearTimeout(loadingTimeout);
    };
  }, [videoUrl, isYouTube, videoError]);

  // Component mount/unmount tracking
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      // Clean up everything on unmount
      if (timeUpdateIntervalRef.current) {
        clearInterval(timeUpdateIntervalRef.current);
        timeUpdateIntervalRef.current = null;
      }
      if (youtubePlayerRef.current && youtubePlayerRef.current.destroy) {
        youtubePlayerRef.current.destroy();
        youtubePlayerRef.current = null;
      }
      playerInitializedRef.current = false;
    };
  }, []); // Sync video time when received from master
  useEffect(() => {
    if (syncTime !== null && !isMaster) {
      if (
        isYouTube &&
        youtubePlayerRef.current &&
        youtubePlayerRef.current.getCurrentTime
      ) {
        const currentVideoTime = youtubePlayerRef.current.getCurrentTime();
        const timeDiff = Math.abs(currentVideoTime - syncTime);

        // Only sync if time difference is significant (>2 seconds)
        if (timeDiff > 2) {
          youtubePlayerRef.current.seekTo(syncTime, true);
        }
      } else if (!isYouTube && videoRef.current) {
        const video = videoRef.current;
        const timeDiff = Math.abs(video.currentTime - syncTime);

        if (timeDiff > 2) {
          video.currentTime = syncTime;
        }
      }
    }
  }, [syncTime, isMaster, isYouTube]);

  // Determine video source - prioritize YouTube URL, then local file
  const getVideoSource = () => {
    if (
      (videoUrl && videoUrl.includes("youtube.com")) ||
      videoUrl?.includes("youtu.be")
    ) {
      return extractYouTubeEmbedUrl(videoUrl);
    }
    if (videoFile) {
      return `http://localhost:5001/api/video/${videoFile}`;
    }
    return "https://www.w3schools.com/html/mov_bbb.mp4";
  };

  const extractYouTubeEmbedUrl = (url) => {
    const videoId = extractYouTubeId(url);
    if (videoId) {
      return `https://www.youtube.com/embed/${videoId}?enablejsapi=1`;
    }
    return url;
  };

  const extractYouTubeId = (url) => {
    const regExp =
      /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return match && match[2].length === 11 ? match[2] : null;
  };

  const finalVideoSource = getVideoSource();

  const handleVideoLoad = (e) => {
    setVideoLoading(false);
    setVideoError(false);

    // Get video duration
    const duration = e.target.duration;
    if (duration) {
      const minutes = Math.floor(duration / 60);
      const seconds = Math.floor(duration % 60);
      setVideoDuration(`${minutes}:${seconds.toString().padStart(2, "0")}`);
    }
  };

  const handleTimeUpdate = (e) => {
    const video = e.target;
    const time = video.currentTime;

    // Update display time
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    const timeString = `${minutes}:${seconds.toString().padStart(2, "0")}`;
    setCurrentTime(timeString);

    // Always call onTimeUpdate for AI functionality (regardless of master status)
    if (onTimeUpdate) {
      onTimeUpdate(time);
    }

    // Log periodically for debugging (every 10 seconds)
    if (Math.floor(time) % 10 === 0) {
      console.log(`HTML5 video time update: ${timeString} (${time}s)`);
    }
  };

  // Sync video time when received from master
  useEffect(() => {
    if (syncTime !== null && !isMaster && videoRef.current) {
      const video = videoRef.current;
      const timeDiff = Math.abs(video.currentTime - syncTime);

      // Only sync if time difference is significant (>2 seconds)
      if (timeDiff > 2) {
        video.currentTime = syncTime;
      }
    }
  }, [syncTime, isMaster]);

  const handleVideoError = (e) => {
    console.error("Video load error:", e);
    setVideoLoading(false);
    setVideoError(true);
  };

  const handleVideoLoadStart = () => {
    setVideoLoading(true);
    setVideoError(false);
  };

  useEffect(() => {
    console.log("VideoPlayer - URL:", finalVideoSource);
    console.log("VideoPlayer - State:", {
      videoLoading,
      videoError,
      isYouTube,
      currentTime,
      videoDuration,
    });
  }, [
    finalVideoSource,
    videoLoading,
    videoError,
    isYouTube,
    currentTime,
    videoDuration,
  ]);

  return (
    <div className="video-player">
      {/* <div className="video-header">
        <h2>{sessionName || "Video Session"}</h2>
        <div className="video-controls-info">
          <span className="video-status">🔴 Live Session</span>
          {isMaster && <span className="master-badge">👑 Master Control</span>}
          <span className="video-time">
            {currentTime} / {videoDuration}
          </span>
        </div>
      </div> */}

      <div className="video-container">
        {videoLoading && !videoError && (
          <div className="video-loading">
            <div className="loading-spinner"></div>
            <p>Loading video...</p>
          </div>
        )}

        {videoError && (
          <div className="video-error">
            <div className="error-content">
              <div className="error-icon">⚠️</div>
              <h3>Video Load Error</h3>
              <p>
                Could not load video: {videoFile || videoUrl || "test video"}
              </p>
              <p className="error-url">URL: {finalVideoSource}</p>
              <button
                className="retry-button"
                onClick={() => {
                  setVideoError(false);
                  setVideoLoading(true);
                  // Force video reload
                  const video = document.querySelector("video");
                  if (video) {
                    video.load();
                  }
                }}
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {isYouTube ? (
          <div
            style={{
              width: "100%",
              height: "100%",
              minHeight: "400px",
              display: videoLoading || videoError ? "none" : "block",
              backgroundColor: "#000",
            }}
          >
            <div
              id="youtube-player"
              style={{
                width: "100%",
                height: "100%",
              }}
              ref={(div) => {
                if (div) {
                  console.log("YouTube player div ref:", {
                    display: div.style.display,
                    width: div.style.width,
                    height: div.style.height,
                    children: div.children.length,
                    innerHTML:
                      div.innerHTML.length > 0 ? "has content" : "empty",
                  });
                }
              }}
            />
          </div>
        ) : (
          <video
            ref={videoRef}
            controls
            width="100%"
            height="100%"
            style={{
              display: videoLoading || videoError ? "none" : "block",
              backgroundColor: "#000",
            }}
            onLoadStart={handleVideoLoadStart}
            onLoadedData={handleVideoLoad}
            onTimeUpdate={handleTimeUpdate}
            onError={handleVideoError}
            preload="metadata"
          >
            <source src={finalVideoSource} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        )}
      </div>

      <div className="video-info-bar">
        <div className="video-meta">
          <span className="video-duration">📹 Duration: {videoDuration}</span>
          <span className="video-format">
            {isYouTube ? "🎥 YouTube" : "📁 MP4"} • 720p
          </span>
        </div>
        <div className="video-url-container">
          <span className="video-url-label">🔗 Source:</span>
          <input 
            type="text" 
            value={finalVideoSource} 
            readOnly 
            className="video-url-input"
            title={finalVideoSource}
          />
        </div>
      </div>

    </div>
  );
};

export default VideoPlayer;
