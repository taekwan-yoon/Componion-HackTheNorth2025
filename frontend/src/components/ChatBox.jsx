import React, { useState, useRef, useEffect, useCallback } from "react";
import "./ChatBox.css";
import QueryModeSelector from "./QueryModeSelector";
import { ttsAPI } from "../services/api";

const ChatBox = ({
  messages,
  onSendMessage,
  onAskQuestion,
  currentUser,
  isConnected,
  isMaster = false,
  currentVideoTime = 0,
}) => {
  const [messageInput, setMessageInput] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [isTextToSpeechEnabled, setIsTextToSpeechEnabled] = useState(false);
  const [isThinking, setIsThinking] = useState(false); // NEW STATE

  // Query mode states
  const [queryMode, setQueryMode] = useState("omniscient"); // 'omniscient', 'temporal', 'window'
  const [startTime, setStartTime] = useState(0);
  const [endTime, setEndTime] = useState(60);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      // Reset isThinking when an AI response arrives
      if (lastMessage.message_type === "ai") {
        console.log("AI response received, clearing thinking state");
        setIsThinking(false);
      }
    }
  }, [messages]);

  // Debug log for thinking state changes
  useEffect(() => {
    console.log("isThinking state changed to:", isThinking);
  }, [isThinking]);

  // Speech synthesis functions (keeping as fallback)
  const speakText = useCallback(
    (text) => {
      if (synthRef.current && speechSupported && text) {
        synthRef.current.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1;
        utterance.volume = 0.8;

        utterance.onstart = () => {
          setIsSpeaking(true);
        };

        utterance.onend = () => {
          setIsSpeaking(false);
        };

        utterance.onerror = (event) => {
          console.error("Speech synthesis error:", event.error);
          setIsSpeaking(false);
        };

        synthRef.current.speak(utterance);
      }
    },
    [speechSupported]
  );

  // Cloudflare TTS functions
  const speakTextWithCloudflare = useCallback(
    async (text) => {
      if (!text || !isTextToSpeechEnabled) return;

      try {
        setIsSpeaking(true);

        // Call our TTS API
        const audioBlob = await ttsAPI.textToSpeech(text, "luna");

        // Create blob URL and play audio
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);

        audio.onended = () => {
          setIsSpeaking(false);
          URL.revokeObjectURL(audioUrl); // Clean up memory
        };

        audio.onerror = (error) => {
          console.error("Audio playback error:", error);
          setIsSpeaking(false);
          URL.revokeObjectURL(audioUrl);
        };

        await audio.play();
      } catch (error) {
        console.error("TTS error:", error);
        setIsSpeaking(false);

        // Fallback to browser TTS if Cloudflare fails
        if (synthRef.current && speechSupported) {
          console.log("Falling back to browser TTS");
          speakText(text);
        }
      }
    },
    [isTextToSpeechEnabled, speechSupported, speakText]
  );

  const stopSpeaking = () => {
    // Stop browser speech synthesis
    if (synthRef.current) {
      synthRef.current.cancel();
    }

    // Stop any currently playing audio
    const audioElements = document.querySelectorAll("audio");
    audioElements.forEach((audio) => {
      audio.pause();
      audio.currentTime = 0;
    });

    setIsSpeaking(false);
  };

  // Initialize speech services
  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    const speechSynthesis = window.speechSynthesis;

    if (SpeechRecognition && speechSynthesis) {
      setSpeechSupported(true);

      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = "en-US";

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setMessageInput(transcript);
        setIsListening(false);
      };

      recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;

      synthRef.current = speechSynthesis;
    }
  }, []);

  // Auto-speak AI responses using Cloudflare TTS when enabled
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.message_type === "ai" && isTextToSpeechEnabled) {
        speakTextWithCloudflare(lastMessage.message);
      }
    }
  }, [messages, isTextToSpeechEnabled, speakTextWithCloudflare]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const startListening = () => {
    if (recognitionRef.current && speechSupported && !isListening) {
      try {
        recognitionRef.current.start();
      } catch (error) {
        console.error("Error starting speech recognition:", error);
      }
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  };

  const isAIMessage = () => {
    const message = messageInput.trim().toLowerCase();
    return (
      message.startsWith("@componion") ||
      message.includes("hey componion") ||
      message.includes("componion") ||
      message.includes("companion")
    );
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    setMessageInput(value);

    if (
      value.endsWith("@") ||
      (value.includes("@") && !value.toLowerCase().includes("componion")) ||
      value.toLowerCase().includes("hey comp") ||
      (value.toLowerCase().includes("comp") && value.length > 4) ||
      (value.toLowerCase().includes("companion") && value.length > 4)
    ) {
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (suggestionType) => {
    const currentValue = messageInput;
    let newValue;

    if (suggestionType === "at") {
      const atIndex = currentValue.lastIndexOf("@");
      newValue = currentValue.substring(0, atIndex) + "@Componion ";
    } else if (suggestionType === "hey") {
      const lowerValue = currentValue.toLowerCase();
      if (
        lowerValue.includes("hey comp") ||
        lowerValue.includes("comp") ||
        lowerValue.includes("companion")
      ) {
        newValue = currentValue
          .replace(/hey comp\w*/i, "Hey Componion, ")
          .replace(/comp\w*/i, "Hey Componion, ")
          .replace(/companion\w*/i, "Hey Componion, ");
      } else {
        newValue =
          currentValue +
          (currentValue.endsWith(" ") ? "" : " ") +
          "Hey Componion, ";
      }
    }

    setMessageInput(newValue);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!messageInput.trim() || !isConnected) return;

    const message = messageInput.trim();

    if (isAIMessage()) {
      console.log("Setting thinking state to true for AI message:", message);
      setIsThinking(true); // SET THINKING STATE
      onSendMessage(message, currentVideoTime, queryMode, startTime, endTime);

      // Add timeout to clear thinking state if no response comes
      setTimeout(() => {
        console.log("Timeout: clearing thinking state");
        setIsThinking(false);
      }, 30000); // 30 second timeout
    } else {
      onSendMessage(message);
    }

    setMessageInput("");
    setShowSuggestions(false);
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const getMessagePreview = (message) => {
    if (!message) return "";
    const words = message.split(" ").slice(0, 3).join(" ");
    return words.length < message.length ? `${words}...` : words;
  };

  const isCurrentUser = (message) => {
    return currentUser && message.user_id === currentUser.user_id;
  };

  return (
    <div className="chat-box">
      <div className="messages-container">
        <div className="messages-list">
          {messages.length === 0 && !isThinking ? (
            <div className="no-messages">
              <p>No messages yet. Start the conversation!</p>
              <p className="ai-hint">
                Say "Hey Componion", "Companion" or type @Componion to ask
                the AI assistant
              </p>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`message ${message.message_type} ${
                    isCurrentUser(message) ? "own-message" : ""
                  } ${message.is_ai_directed ? "ai-directed" : ""}`}
                >
                  {message.message_type === "ai" &&
                    message.reply_to_message && (
                      <div className="reply-indicator">
                        <span className="reply-icon">↳</span>
                        <span className="reply-text">
                          Replying to: "
                          {getMessagePreview(message.reply_to_message)}"
                        </span>
                      </div>
                    )}

                  <div className="message-header">
                    <span className="message-author">
                      {message.message_type === "ai" ? (
                        <span className="ai-badge">Componion</span>
                      ) : (
                        <>
                          {message.is_ai_directed}
                          {message.display_name || "Unknown User"}
                        </>
                      )}
                    </span>
                    <span className="message-time">
                      {formatTime(message.created_at)}
                    </span>
                  </div>
                  <div className="message-content">{message.message}</div>
                </div>
              ))}

              {/* AI Thinking Indicator - Show when thinking regardless of message count */}
              {isThinking && (
                <div className="message ai thinking-message">
                  <div className="message-header">
                    <span className="message-author">
                      <span className="ai-badge">Componion</span>
                    </span>
                    <span className="message-time">...</span>
                  </div>
                  <div className="message-content">
                    <div className="thinking-indicator">
                      <span className="thinking-text">
                        Componion is thinking
                      </span>
                      <div className="thinking-dots">
                        <span className="dot"></span>
                        <span className="dot"></span>
                        <span className="dot"></span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="chat-input-container">
        <div className="input-controls-row">
          <QueryModeSelector
            queryMode={queryMode}
            onQueryModeChange={setQueryMode}
            startTime={startTime}
            endTime={endTime}
            onStartTimeChange={setStartTime}
            onEndTimeChange={setEndTime}
            currentVideoTime={currentVideoTime}
          />
          {speechSupported && (
            <div className="voice-controls">
              <button
                type="button"
                className={`voice-button ${
                  isTextToSpeechEnabled ? "active" : ""
                }`}
                onClick={() =>
                  setIsTextToSpeechEnabled(!isTextToSpeechEnabled)
                }
                title={
                  isTextToSpeechEnabled
                    ? "Turn off text-to-speech"
                    : "Turn on text-to-speech"
                }
              >
                🔉
              </button>

              <button
                type="button"
                className={`voice-button ${isListening ? "listening" : ""}`}
                onClick={isListening ? stopListening : startListening}
                disabled={!isConnected}
                title={isListening ? "Stop listening" : "Start voice input"}
              >
                {isListening ? "🔴" : "🎙️"}
              </button>
              {isSpeaking && (
                <button
                  type="button"
                  className="voice-button stop-speaking"
                  onClick={stopSpeaking}
                  title="Stop speaking"
                >
                  ⏹️
                </button>
              )}
            </div>
          )}
        </div>
        <form onSubmit={handleSubmit} className="unified-form">
          <div className="input-wrapper">
            <input
              ref={inputRef}
              type="text"
              value={messageInput}
              onChange={handleInputChange}
              placeholder={
                isConnected
                  ? "Type a message, say 'Hey Componion', 'Companion' or use @Componion..."
                  : "Connecting..."
              }
              disabled={!isConnected}
              maxLength={500}
            />
            {showSuggestions && (
              <div className="autocomplete-suggestions">
                <div
                  className="suggestion-item"
                  onClick={() => handleSuggestionClick("at")}
                >
                  <span className="suggestion-text">@Componion</span>
                  <span className="suggestion-desc">Ask AI assistant</span>
                </div>
                <div
                  className="suggestion-item"
                  onClick={() => handleSuggestionClick("hey")}
                >
                  <span className="suggestion-text">Hey Componion,</span>
                  <span className="suggestion-desc">Natural conversation</span>
                </div>
              </div>
            )}
          </div>
          <button
            type="submit"
            disabled={!messageInput.trim() || !isConnected}
            className={`submit-button ${
              isAIMessage() ? "ai-button" : "send-button"
            }`}
          >
            {isAIMessage() ? "Ask Componion" : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatBox;
