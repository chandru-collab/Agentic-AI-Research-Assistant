import React, { useState, useEffect, useRef } from 'react';
import { Search, Loader2, Download, AlertCircle, FileText, SlidersHorizontal, Cpu, Sparkles, RefreshCw } from 'lucide-react';
import { api } from './utils/api';
import Sidebar from './components/Sidebar';
import StatsGrid from './components/StatsGrid';
import ProgressTracker from './components/ProgressTracker';
import ReportViewer from './components/ReportViewer';
import LogViewer from './components/LogViewer';
import EmptyState from './components/EmptyState';

export default function App() {
  // Model Settings (situated in the main workspace search card)
  const [selectedModel, setSelectedModel] = useState('llama-3.3-70b-versatile');
  const [temperature, setTemperature] = useState(0.3);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // App States
  const [backendStatus, setBackendStatus] = useState('checking');
  const [history, setHistory] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [query, setQuery] = useState('');
  
  // Pipeline Progress States
  const [isResearching, setIsResearching] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState(null);
  
  // File Download Flags
  const [pdfLoading, setPdfLoading] = useState(false);
  const [mdLoading, setMdLoading] = useState(false);

  const stepIntervalRef = useRef(null);

  // Health and History checking
  useEffect(() => {
    checkHealthAndFetchHistory();
    return () => clearInterval(stepIntervalRef.current);
  }, []);

  const checkHealthAndFetchHistory = async () => {
    setBackendStatus('checking');
    try {
      const health = await api.healthCheck();
      if (health && health.status === 'healthy') {
        setBackendStatus('healthy');
      } else {
        setBackendStatus('offline');
      }
    } catch (_) {
      setBackendStatus('offline');
    }

    try {
      const historyList = await api.getHistory();
      if (Array.isArray(historyList)) {
        setHistory(historyList);
      }
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  // Simulating step progress indicator (planning -> searching -> analyzing -> summarizing -> reporting -> saving)
  const startStepSimulation = () => {
    setCurrentStep(0);
    clearInterval(stepIntervalRef.current);
    
    stepIntervalRef.current = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < 4) return prev + 1;
        return prev;
      });
    }, 12000); // 12 seconds per step
  };

  const handleResearch = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim() || isResearching) return;

    setIsResearching(true);
    setActiveSession(null);
    setError(null);
    startStepSimulation();

    try {
      const result = await api.runResearch(query, selectedModel);
      
      clearInterval(stepIntervalRef.current);
      setCurrentStep(5); // saving state

      setTimeout(() => {
        setActiveSession(result);
        setIsResearching(false);
        // Refresh history
        api.getHistory().then((historyList) => {
          if (Array.isArray(historyList)) setHistory(historyList);
        });
      }, 5000);

    } catch (err) {
      clearInterval(stepIntervalRef.current);
      setIsResearching(false);
      setError(err.message || 'Research pipeline aborted due to server error.');
    }
  };

  const handleLoadSession = async (sessionId) => {
    if (isResearching) return;
    setError(null);
    setActiveSession(null);
    
    try {
      const sessionData = await api.getReport(sessionId);
      if (sessionData && !sessionData.error) {
        setActiveSession(sessionData);
      } else {
        setError(sessionData.error || 'Failed to retrieve selected report.');
      }
    } catch (err) {
      setError(err.message || 'Error connecting to API host.');
    }
  };

  const downloadPDF = async () => {
    if (!activeSession || pdfLoading) return;
    setPdfLoading(true);
    setError(null);

    try {
      const blob = await api.exportPDF(activeSession.session_id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      const safeQuery = activeSession.query.slice(0, 30).replace(/[^a-z0-9]/gi, '_').toLowerCase();
      link.setAttribute('download', `${safeQuery}_report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      setError(err.message || 'PDF export failed.');
    } finally {
      setPdfLoading(false);
    }
  };

  const downloadMarkdown = async () => {
    if (!activeSession || mdLoading) return;
    setMdLoading(true);
    setError(null);

    try {
      const text = await api.exportMarkdown(activeSession.session_id);
      const blob = new Blob([text], { type: 'text/markdown' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      const safeQuery = activeSession.query.slice(0, 30).replace(/[^a-z0-9]/gi, '_').toLowerCase();
      link.setAttribute('download', `${safeQuery}_report.md`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      setError(err.message || 'Markdown export failed.');
    } finally {
      setMdLoading(false);
    }
  };

  const stats = activeSession ? {
    sources: activeSession.sources ? activeSession.sources.length : 0,
    insights: activeSession.insights ? activeSession.insights.length : 0,
    words: activeSession.final_report ? activeSession.final_report.trim().split(/\s+/).length : 0,
    steps: activeSession.logs ? activeSession.logs.length : 0
  } : { sources: 0, insights: 0, words: 0, steps: 0 };

  return (
    <div className="app-container">
      {/* Decorative Neon Blurs */}
      <div className="neon-glow-orb purple-orb"></div>
      <div className="neon-glow-orb blue-orb"></div>

      {/* Modern Conversational Sidebar */}
      <Sidebar
        backendStatus={backendStatus}
        history={history}
        activeSessionId={activeSession?.session_id}
        onLoadSession={handleLoadSession}
      />

      {/* Main Execution Dashboard */}
      <main className="main-content">
        {/* Sleek App Banner */}
        <div className="app-banner">
          <div className="banner-logo">
            <Sparkles size={16} className="sparkle-icon" />
            <span>Research Assistant PRO</span>
          </div>
          {backendStatus === 'offline' && (
            <button className="reconnect-btn" onClick={checkHealthAndFetchHistory}>
              <RefreshCw size={12} />
              <span>Retry Connection</span>
            </button>
          )}
        </div>

        {/* Floating Search Console (Linear/Perplexity style) */}
        <div className="search-console-wrapper">
          <form onSubmit={handleResearch} className="modern-search-deck">
            <div className="search-deck-input-row">
              <Search size={20} className="search-deck-icon" />
              <input
                type="text"
                placeholder="What topic would you like to research today?"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={isResearching}
                className="search-deck-input"
              />
              <button
                type="submit"
                disabled={isResearching || !query.trim()}
                className="search-deck-submit-btn"
              >
                {isResearching ? (
                  <Loader2 size={16} className="btn-spinner" />
                ) : (
                  <span>Submit</span>
                )}
              </button>
            </div>

            {/* Quick model selectors situated directly inside input card */}
            <div className="search-deck-settings-row">
              <div className="model-selectors-pills">
                <span className="setting-pill-label"><Cpu size={12} /> Model:</span>
                <button
                  type="button"
                  onClick={() => setSelectedModel('llama-3.3-70b-versatile')}
                  className={`model-pill-btn ${selectedModel === 'llama-3.3-70b-versatile' ? 'active' : ''}`}
                  disabled={isResearching}
                >
                  Llama 3.3 Versatile
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedModel('llama-3.1-8b-instant')}
                  className={`model-pill-btn ${selectedModel === 'llama-3.1-8b-instant' ? 'active' : ''}`}
                  disabled={isResearching}
                >
                  Llama 3.1 8B
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedModel('mixtral-8x7b-32768')}
                  className={`model-pill-btn ${selectedModel === 'mixtral-8x7b-32768' ? 'active' : ''}`}
                  disabled={isResearching}
                >
                  Mixtral
                </button>
              </div>

              <button
                type="button"
                className={`advanced-settings-toggle ${showAdvanced ? 'active' : ''}`}
                onClick={() => setShowAdvanced(!showAdvanced)}
              >
                <SlidersHorizontal size={14} />
                <span>Options</span>
              </button>
            </div>

            {/* Expandable Advanced Options Slider */}
            {showAdvanced && (
              <div className="expanded-advanced-panel animate-fade-in">
                <div className="advanced-slider-group">
                  <div className="slider-header-label">
                    <span>Creativity Scale (Temperature)</span>
                    <span className="slider-val-tag">{temperature.toFixed(1)}</span>
                  </div>
                  <input
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="advanced-slider"
                    disabled={isResearching}
                  />
                  <span className="slider-desc">Lower values yield focused, deterministic reports; higher values introduce creative phrasing.</span>
                </div>
              </div>
            )}
          </form>
        </div>

        {/* Error Notification Banner */}
        {error && (
          <div className="glass-error-banner animate-fade-in">
            <AlertCircle size={18} className="banner-error-icon" />
            <div className="error-banner-content">
              <strong>Pipeline Interrupted</strong>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Pipeline Execution Progress Tracker */}
        {isResearching && (
          <ProgressTracker
            currentStep={currentStep}
            isResearching={isResearching}
            isComplete={false}
          />
        )}

        {/* Result Dashboards */}
        {activeSession && !isResearching && (
          <div className="dashboard-results-area animate-fade-in">
            {/* Stat counts row */}
            <StatsGrid
              sourcesCount={stats.sources}
              insightsCount={stats.insights}
              wordCount={stats.words}
              stepsCount={stats.steps}
            />

            {/* Tabbed content displays */}
            <ReportViewer result={activeSession} />

            {/* Monospace Log Viewer */}
            <LogViewer logs={activeSession.logs} />

            {/* Action Bar for Exports */}
            <div className="bottom-export-deck">
              <div className="export-deck-info">
                <h4>Publish Research Report</h4>
                <p>Download the findings locally as a printable PDF or formatted Markdown file.</p>
              </div>
              <div className="export-deck-buttons">
                <button 
                  onClick={downloadPDF} 
                  disabled={pdfLoading}
                  className="export-deck-btn-primary"
                >
                  {pdfLoading ? (
                    <>
                      <Loader2 size={16} className="btn-spinner" />
                      <span>Packaging PDF...</span>
                    </>
                  ) : (
                    <>
                      <Download size={16} />
                      <span>Download PDF</span>
                    </>
                  )}
                </button>
                <button 
                  onClick={downloadMarkdown} 
                  disabled={mdLoading}
                  className="export-deck-btn-secondary"
                >
                  {mdLoading ? (
                    <>
                      <Loader2 size={16} className="btn-spinner" />
                      <span>Packaging Markdown...</span>
                    </>
                  ) : (
                    <>
                      <FileText size={16} />
                      <span>Download Markdown</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Empty State Welcome Dashboard */}
        {!activeSession && !isResearching && <EmptyState />}
      </main>
    </div>
  );
}
