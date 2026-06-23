import React, { useState } from 'react';
import { Terminal, ChevronDown, ChevronUp } from 'lucide-react';

export default function LogViewer({ logs = [] }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!logs || logs.length === 0) return null;

  const getLogStyle = (entry) => {
    if (entry.includes('❌')) return 'log-entry error';
    if (entry.includes('⚠️')) return 'log-entry warning';
    if (entry.includes('🚀')) return 'log-entry info';
    return 'log-entry success';
  };

  return (
    <div className="log-viewer-container">
      <button 
        className={`log-viewer-header ${isOpen ? 'open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="header-left">
          <Terminal size={16} />
          <span>Execution Logs ({logs.length} entries)</span>
        </div>
        {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      {isOpen && (
        <div className="logs-content-wrapper">
          <div className="logs-terminal">
            {logs.map((log, index) => (
              <div key={index} className={getLogStyle(log)}>
                <span className="log-timestamp">[{new Date().toLocaleTimeString()}]</span>
                <span className="log-text">{log}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
