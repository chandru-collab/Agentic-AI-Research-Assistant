import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Target, List, Search, AlertCircle, FileText, Globe, Lightbulb } from 'lucide-react';

export default function ReportViewer({ result }) {
  const [activeTab, setActiveTab] = useState('plan'); // plan, sources, insights, summary, report

  if (!result) return null;

  const plan = result.research_plan || {};
  const sources = result.sources || [];
  const insights = result.insights || [];
  const summary = result.summary || '';
  const report = result.final_report || '';

  const tabs = [
    { id: 'plan', label: 'Research Plan', icon: <Target size={16} /> },
    { id: 'sources', label: `Sources (${sources.length})`, icon: <Globe size={16} /> },
    { id: 'insights', label: `Insights (${insights.length})`, icon: <Lightbulb size={16} /> },
    { id: 'summary', label: 'Summary', icon: <AlertCircle size={16} /> },
    { id: 'report', label: 'Full Report', icon: <FileText size={16} /> },
  ];

  return (
    <div className="report-viewer">
      {/* Tabs Menu */}
      <div className="tabs-header">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
          >
            {tab.icon}
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content Panels */}
      <div className="tab-content">
        
        {/* RESEARCH PLAN TAB */}
        {activeTab === 'plan' && (
          <div className="tab-pane animate-fade-in">
            {Object.keys(plan).length > 0 ? (
              <div className="plan-grid">
                <div className="plan-card">
                  <h4>🎯 Objectives</h4>
                  {plan.objectives && plan.objectives.length > 0 ? (
                    <ul>
                      {plan.objectives.map((obj, i) => (
                        <li key={i}>{obj}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="no-data">No objectives defined.</p>
                  )}
                </div>

                <div className="plan-card">
                  <h4>📂 Sub-Topics</h4>
                  {plan.sub_topics && plan.sub_topics.length > 0 ? (
                    <ul>
                      {plan.sub_topics.map((topic, i) => (
                        <li key={i}>{topic}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="no-data">No sub-topics defined.</p>
                  )}
                </div>

                <div className="plan-card full-width">
                  <h4>🔎 Search Queries</h4>
                  {plan.search_queries && plan.search_queries.length > 0 ? (
                    <div className="queries-list">
                      {plan.search_queries.map((q, i) => (
                        <code key={i} className="query-code">{q}</code>
                      ))}
                    </div>
                  ) : (
                    <p className="no-data">No search queries defined.</p>
                  )}
                </div>
              </div>
            ) : (
              <div className="info-box">No research plan available.</div>
            )}
          </div>
        )}

        {/* SOURCES TAB */}
        {activeTab === 'sources' && (
          <div className="tab-pane animate-fade-in">
            {sources.length > 0 ? (
              <div className="sources-list">
                <p className="sources-count">{sources.length} sources crawled during research:</p>
                {sources.map((source, index) => {
                  const title = source.title || 'Untitled';
                  const url = source.url || '#';
                  const srcType = source.source || 'unknown';
                  const score = source.relevance_score;

                  return (
                    <div key={index} className="source-card">
                      <div className="source-card-header">
                        <span className="source-index">{index + 1}.</span>
                        <a href={url} target="_blank" rel="noopener noreferrer" className="source-link">
                          {title}
                        </a>
                        <span className={`source-badge ${srcType}`}>
                          {srcType}
                        </span>
                      </div>
                      <p className="source-snippet">{source.snippet}</p>
                      {score !== undefined && score !== null && (
                        <div className="source-score">
                          <span>Relevance Match:</span>
                          <span className="score-value">{(score * 100).toFixed(0)}%</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="info-box">No sources available.</div>
            )}
          </div>
        )}

        {/* INSIGHTS TAB */}
        {activeTab === 'insights' && (
          <div className="tab-pane animate-fade-in">
            {insights.length > 0 ? (
              <div className="insights-list">
                <p className="insights-subtitle">{insights.length} key findings extracted:</p>
                {insights.map((insight, index) => (
                  <div key={index} className="insight-card">
                    <div className="insight-number">#{index + 1}</div>
                    <div className="insight-text">{insight}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="info-box">No insights available.</div>
            )}
          </div>
        )}

        {/* SUMMARY TAB */}
        {activeTab === 'summary' && (
          <div className="tab-pane animate-fade-in markdown-container">
            {summary ? (
              <ReactMarkdown className="markdown-body">{summary}</ReactMarkdown>
            ) : (
              <div className="info-box">No summary available.</div>
            )}
          </div>
        )}

        {/* FULL REPORT TAB */}
        {activeTab === 'report' && (
          <div className="tab-pane animate-fade-in markdown-container">
            {report ? (
              <ReactMarkdown className="markdown-body">{report}</ReactMarkdown>
            ) : (
              <div className="info-box">No report available.</div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
