import React, { useState, useRef, useEffect } from 'react';
import './QueryModeSelector.css';

const QueryModeSelector = ({ 
  queryMode, 
  onQueryModeChange, 
  startTime, 
  endTime, 
  onStartTimeChange, 
  onEndTimeChange,
  currentVideoTime,
  videoDuration = 0
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [showTimeWindow, setShowTimeWindow] = useState(false);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 });
  const dropdownRef = useRef(null);

  const formatTime = (seconds) => {
    if (!seconds) return "00:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const parseTime = (timeString) => {
    const parts = timeString.split(':');
    if (parts.length !== 2) return 0;
    const minutes = parseInt(parts[0]) || 0;
    const seconds = parseInt(parts[1]) || 0;
    return minutes * 60 + seconds;
  };

  const calculateDropdownPosition = () => {
    if (dropdownRef.current) {
      const rect = dropdownRef.current.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const dropdownHeight = 180; // Approximate height of dropdown
      
      // Check if there's enough space below, otherwise position above
      const shouldOpenUpward = rect.bottom + dropdownHeight > viewportHeight;
      
      setDropdownPosition({
        top: shouldOpenUpward 
          ? rect.top + window.scrollY - dropdownHeight - 4
          : rect.bottom + window.scrollY + 4,
        left: rect.left + window.scrollX,
        width: rect.width,
        openUpward: shouldOpenUpward
      });
    }
  };

  const handleModeChange = (mode) => {
    onQueryModeChange(mode);
    
    // Set default values for window mode
    if (mode === 'window' && (!startTime || !endTime)) {
      if (!startTime) onStartTimeChange(0);
      if (!endTime) onEndTimeChange(currentVideoTime || 60);
    }
    
    setIsOpen(false);
    
    // Show time window panel for window mode
    if (mode === 'window') {
      calculateDropdownPosition();
      setShowTimeWindow(true);
    } else {
      setShowTimeWindow(false);
    }
  };

  const handleDropdownToggle = () => {
    if (!isOpen) {
      calculateDropdownPosition();
    }
    setIsOpen(!isOpen);
  };

  const getModeDisplay = () => {
    switch (queryMode) {
      case 'omniscient': return { icon: '', name: 'Omniscient', desc: 'Full video' };
      case 'temporal': return { icon: '', name: 'Temporal', desc: `Up to ${formatTime(currentVideoTime)}` };
      case 'window': return { icon: '', name: 'Window', desc: `${formatTime(startTime)}-${formatTime(endTime)}` };
      default: return { icon: '', name: 'Unknown', desc: '' };
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Initialize time window visibility
  useEffect(() => {
    setShowTimeWindow(queryMode === 'window');
  }, [queryMode]);

  const currentMode = getModeDisplay();

  return (
    <div className="query-mode-selector" ref={dropdownRef}>
      <div className="mode-selector-button" onClick={handleDropdownToggle}>
        <div className="mode-current">
          <span className="mode-icon">{currentMode.icon}</span>
          <div className="mode-info">
            <span className="mode-name">{currentMode.name}</span>
            <span className="mode-desc">{currentMode.desc}</span>
          </div>
        </div>
        <span className={`dropdown-arrow ${isOpen ? 'open' : ''}`}>▼</span>
      </div>
      
      {isOpen && (
        <div 
          className="mode-dropdown"
          style={{
            top: `${dropdownPosition.top}px`,
            left: `${dropdownPosition.left}px`,
            width: `${Math.max(dropdownPosition.width, 300)}px`
          }}
        >
          <div className="mode-option" onClick={() => handleModeChange('omniscient')}>
            <span className="mode-option-icon"></span>
            <div className="mode-option-content">
              <div className="mode-option-title">Omniscient Mode</div>
              <div className="mode-option-desc">AI knows entire video content</div>
            </div>
            {queryMode === 'omniscient' && <span className="mode-check">•</span>}
          </div>
          
          <div className="mode-option" onClick={() => handleModeChange('temporal')}>
            <span className="mode-option-icon"></span>
            <div className="mode-option-content">
              <div className="mode-option-title">Temporal Mode</div>
              <div className="mode-option-desc">Only up to current timestamp</div>
            </div>
            {queryMode === 'temporal' && <span className="mode-check">•</span>}
          </div>
          
          <div className="mode-option" onClick={() => handleModeChange('window')}>
            <span className="mode-option-icon"></span>
            <div className="mode-option-content">
              <div className="mode-option-title">Time Window</div>
              <div className="mode-option-desc">Custom time range</div>
            </div>
            {queryMode === 'window' && <span className="mode-check">•</span>}
          </div>
        </div>
      )}
      
      {showTimeWindow && queryMode === 'window' && (
        <div 
          className="time-window-panel"
          style={{
            top: `${dropdownPosition.top}px`,
            left: `${dropdownPosition.left}px`,
            width: `${Math.max(dropdownPosition.width, 250)}px`
          }}
        >
          <div className="time-window-header">
            <span>Time Window Settings</span>
            <button 
              className="close-time-window"
              onClick={() => setShowTimeWindow(false)}
            >
              ×
            </button>
          </div>
          <div className="time-controls">
            <div className="time-input-row">
              <label>From:</label>
              <input
                type="text"
                placeholder="00:00"
                value={formatTime(startTime)}
                onChange={(e) => onStartTimeChange(parseTime(e.target.value))}
                className="time-input"
              />
              <label>To:</label>
              <input
                type="text"
                placeholder="01:00"
                value={formatTime(endTime)}
                onChange={(e) => onEndTimeChange(parseTime(e.target.value))}
                className="time-input"
              />
            </div>
            <div className="time-presets">
              <button 
                className="preset-btn"
                onClick={() => {
                  onStartTimeChange(0);
                  onEndTimeChange(currentVideoTime);
                }}
              >
                Start→Current
              </button>
              <button 
                className="preset-btn"
                onClick={() => {
                  const current = currentVideoTime || 0;
                  onStartTimeChange(Math.max(0, current - 60));
                  onEndTimeChange(current);
                }}
              >
                Last 1min
              </button>
              <button 
                className="preset-btn"
                onClick={() => {
                  const current = currentVideoTime || 0;
                  onStartTimeChange(Math.max(0, current - 300));
                  onEndTimeChange(current);
                }}
              >
                Last 5min
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QueryModeSelector;