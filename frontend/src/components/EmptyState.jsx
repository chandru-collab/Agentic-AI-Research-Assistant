import React from 'react';
import { Target, Search, FileText, Sparkles } from 'lucide-react';

export default function EmptyState() {
  const features = [
    {
      title: 'Smart Planning',
      desc: 'AI creates a structured research plan with objectives, sub-topics, and optimized search queries.',
      icon: <Target size={20} />,
    },
    {
      title: 'Multi-Source Search',
      desc: 'Searches DuckDuckGo and Wikipedia simultaneously, with vision-based relevance reranking.',
      icon: <Search size={20} />,
    },
    {
      title: 'Professional Reports',
      desc: 'Generates detailed reports with citations, exportable as PDF or Markdown.',
      icon: <FileText size={20} />,
    },
  ];

  return (
    <div className="empty-state">
      <div className="welcome-hero animate-fade-in">
        <div className="welcome-icon">🔬</div>
        <h3>Ready to Research</h3>
        <p>
          Enter any research topic above and click <strong>Research</strong>. 
          The AI will plan, search, analyze, summarize, and generate a comprehensive report with citations.
        </p>
      </div>

      <div className="features-section animate-fade-in">
        <h4 className="features-title">
          <Sparkles size={16} /> <span>Features</span>
        </h4>
        <div className="features-grid">
          {features.map((feat, index) => (
            <div key={index} className="feature-card">
              <div className="feature-icon-wrapper">
                {feat.icon}
              </div>
              <h5>{feat.title}</h5>
              <p>{feat.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
