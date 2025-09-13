import React, { useState, useRef, useEffect, useCallback } from "react";
import "./ChatBox.css";

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
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize speech services
  useEffect(() => {
    // Check for speech recognition support
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    const speechSynthesis = window.speechSynthesis;

    if (SpeechRecognition && speechSynthesis) {
      setSpeechSupported(true);

      // Initialize speech recognition
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

      // Initialize speech synthesis
      synthRef.current = speechSynthesis;
    }
  }, []);

  // Auto-speak AI responses
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (
        lastMessage.message_type === "ai" &&
        synthRef.current &&
        speechSupported
      ) {
        speakText(lastMessage.message);
      }
    }
  }, [messages, speechSupported]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Speech recognition functions
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

  // Speech synthesis functions
  const speakText = useCallback(
    (text) => {
      if (synthRef.current && speechSupported && text) {
        // Stop any ongoing speech
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

  const stopSpeaking = () => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  // Check if message starts with @Componion or contains "hey componion", "componion", or "companion"
  const isAIMessage = () => {
    const message = messageInput.trim().toLowerCase();
    return (
      message.startsWith("@componion") ||
      message.includes("hey componion") ||
      message.includes("componion") ||
      message.includes("companion")
    );
  };

  // Extract AI question from message
  const extractAIQuestion = (message) => {
    const lowerMessage = message.toLowerCase();

    // Remove @Componion prefix
    if (lowerMessage.startsWith("@componion")) {
      return message.replace(/@componion\s*/i, "").trim();
    }

    // Remove "hey componion" prefix
    if (lowerMessage.includes("hey componion")) {
      return message.replace(/hey componion[,\s]*/i, "").trim();
    }

    // For messages containing "componion", use the whole message as context
    if (lowerMessage.includes("componion")) {
      return message.replace(/componion[,\s]*/i, "").trim() || message;
    }

    // For messages containing "companion", use the whole message as context
    if (lowerMessage.includes("companion")) {
      return message.replace(/companion[,\s]*/i, "").trim() || message;
    }

    return message;
  };

  // Handle autocomplete for @Componion and natural language
  const handleInputChange = (e) => {
    const value = e.target.value;
    setMessageInput(value);

    // Show suggestions when typing @ or "hey componion/companion" patterns
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
      // Replace partial "comp", "companion" or similar with "Hey Componion, "
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
    
    // Check if this is an AI-directed message
    if (isAIMessage()) {
      // Pass video timestamp for AI-directed messages
      onSendMessage(message, currentVideoTime);
    } else {
      // Regular message without timestamp
      onSendMessage(message);
    }

    setMessageInput("");
    setShowSuggestions(false);
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  // Helper function to get first few words of a message
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
      <div className="chat-header">
        <div className="chat-title">
          <h3>💬 Chat & AI Assistant</h3>
          <p className="chat-subtitle">
            Say "Hey Componion", "Companion", or use @Componion to ask AI
            questions
          </p>
        </div>
        <div className="connection-status">
          <span
            className={`status-indicator ${
              isConnected ? "connected" : "disconnected"
            }`}
          >
            {isConnected ? "🟢 Connected" : "🔴 Disconnected"}
          </span>
        </div>
      </div>

      <div className="messages-container">
        <div className="messages-list">
          {messages.length === 0 ? (
            <div className="no-messages">
              <p>No messages yet. Start the conversation!</p>
              <p className="ai-hint">
                💡 Say "Hey Componion", "Companion" or type @Componion to ask
                the AI assistant
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`message ${message.message_type} ${
                  isCurrentUser(message) ? "own-message" : ""
                } ${message.is_ai_directed ? "ai-directed" : ""}`}
              >
                {/* Reply indicator for AI messages */}
                {message.message_type === "ai" && message.reply_to_message && (
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
                      <span className="ai-badge">🤖 Componion</span>
                    ) : (
                      <>
                        {message.is_ai_directed && (
                          <span className="ai-directed-icon">🎯</span>
                        )}
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
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="chat-input-container">
        <form onSubmit={handleSubmit} className="unified-form">
          <div className="input-wrapper">
            {speechSupported && (
              <div className="voice-controls">
                <button
                  type="button"
                  className={`voice-button ${isListening ? "listening" : ""}`}
                  onClick={isListening ? stopListening : startListening}
                  disabled={!isConnected}
                  title={isListening ? "Stop listening" : "Start voice input"}
                >
                  {isListening ? "🔴" : "🎤"}
                </button>
                {isSpeaking && (
                  <button
                    type="button"
                    className="voice-button stop-speaking"
                    onClick={stopSpeaking}
                    title="Stop speaking"
                  >
                    🔇
                  </button>
                )}
              </div>
            )}
            <input
              ref={inputRef}
              type="text"
              value={messageInput}
              onChange={handleInputChange}
              placeholder={
                isConnected
                  ? speechSupported
                    ? "Type a message, use 🎤 for voice, say 'Hey Componion', 'Companion' or use @Componion..."
                    : "Type a message, say 'Hey Componion', 'Companion' or use @Componion..."
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
                  <span className="suggestion-icon">🤖</span>
                  <span className="suggestion-text">@Componion</span>
                  <span className="suggestion-desc">Ask AI assistant</span>
                </div>
                <div
                  className="suggestion-item"
                  onClick={() => handleSuggestionClick("hey")}
                >
                  <span className="suggestion-icon">👋</span>
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
