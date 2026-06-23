import React from 'react';
import { History, FileText, CheckCircle, AlertCircle, Database, MessageSquare, Terminal } from 'lucide-react';

export default function Sidebar({
  backendStatus,
  history,
  activeSessionId,
  onLoadSession,
}) {
  return (
    <aside className="sidebar">
      {/* Brand Header with Glowing Orb background */}
      <div className="brand-container">
        <div className="brand-logo-wrapper">
          <span className="brand-logo-icon">🔬</span>
        </div>
        <div className="brand-text">
          <h2>Research.AI</h2>
          <p>Agentic Intelligence Deck</p>
        </div>
      </div>

      <hr className="divider" />

      {/* Backend Status Section - Compact & Glowing */}
      <div className="sidebar-section">
        <div className={`backend-status-card ${backendStatus}`}>
          <div className="status-indicator-dot"></div>
          <div className="status-details">
            {backendStatus === 'healthy' ? (
              <>
                <span className="status-label-text">System Online</span>
                <span className="status-desc-text">Groq & FastAPI Active</span>
              </>
            ) : backendStatus === 'offline' ? (
              <>
                <span className="status-label-text">System Offline</span>
                <span className="status-desc-text">Click to restart server</span>
              </>
            ) : (
              <>
                <span className="status-label-text">Connecting...</span>
                <span className="status-desc-text">Checking API gateways</span>
              </>
            )}
          </div>
        </div>

        {backendStatus === 'offline' && (
          <div className="status-guide-box">
            <p>Run backend via terminal:</p>
            <code>python -m uvicorn backend.main:app --reload</code>
          </div>
        )}
      </div>

      <hr className="divider" />

      {/* History section styled like chat threads */}
      <div className="sidebar-section history-section-wrapper">
        <h3 className="section-title-clean">
          <History size={14} /> <span>Recent Researches</span>
        </h3>
        
        <div className="chat-history-list">
          {history.length === 0 ? (
            <div className="empty-history-visual">
              <MessageSquare size={24} className="empty-icon" />
              <p>No queries logged yet</p>
            </div>
          ) : (
            history.slice(0, 15).map((item) => {
              const isActive = item.session_id === activeSessionId;
              return (
                <button
                  key={item.session_id}
                  onClick={() => onLoadSession(item.session_id)}
                  className={`chat-history-item ${isActive ? 'active' : ''}`}
                  title={item.query}
                >
                  <MessageSquare size={14} className="thread-icon" />
                  <div className="thread-content">
                    <span className="thread-title">{item.query}</span>
                    <span className="thread-date">
                      {item.created_at ? new Date(item.created_at).toLocaleDateString(undefined, {month: 'short', day: 'numeric'}) : 'Recent'}
                    </span>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      <div className="sidebar-bottom-meta">
        <div className="tech-stack-row">
          <span>FastAPI</span> • <span>React</span> • <span>LangGraph</span>
        </div>
        <p className="copyright-label">v1.1.0 • Premium Edition</p>
      </div>
    </aside>
  );
}
