import React from 'react';
import { Loader2 } from 'lucide-react';

const PIPELINE_STEPS = [
  { name: 'Planning', icon: '📋', desc: 'Creating research strategy' },
  { name: 'Searching', icon: '🔍', desc: 'Gathering information' },
  { name: 'Analyzing', icon: '🔬', desc: 'Extracting insights' },
  { name: 'Summarizing', icon: '📝', desc: 'Generating summary' },
  { name: 'Reporting', icon: '📄', desc: 'Creating report' },
  { name: 'Saving', icon: '💾', desc: 'Storing to memory' },
];

export default function ProgressTracker({ currentStep = 0, isComplete = false, isResearching = false }) {
  const totalSteps = PIPELINE_STEPS.length;
  
  let percent = 0;
  if (isComplete) {
    percent = 100;
  } else if (isResearching) {
    percent = Math.min(((currentStep + 1) / totalSteps) * 100, 90);
  }

  return (
    <div className="progress-tracker-container">
      <div className="progress-header">
        <h4>{isComplete ? '✅ Research Complete' : '🔄 Research Pipeline'}</h4>
        {isResearching && <span className="running-label">Pipeline Active...</span>}
      </div>

      {/* Progress Bar */}
      <div className="progress-bar-bg">
        <div 
          className={`progress-bar-fill ${isComplete ? 'complete' : 'active'}`} 
          style={{ width: `${percent}%` }}
        />
      </div>

      {/* Steps Indicators */}
      <div className="steps-row">
        {PIPELINE_STEPS.map((step, index) => {
          let stepState = 'pending'; // complete, active, pending
          
          if (isComplete || (isResearching && index < currentStep)) {
            stepState = 'complete';
          } else if (isResearching && index === currentStep) {
            stepState = 'active';
          }

          return (
            <div key={index} className={`step-item ${stepState}`}>
              <div className="step-icon-container">
                {stepState === 'complete' ? (
                  <span className="step-checkmark">✓</span>
                ) : stepState === 'active' ? (
                  <span className="step-icon active-pulse">{step.icon}</span>
                ) : (
                  <span className="step-icon">{step.icon}</span>
                )}
              </div>
              <div className="step-name">{step.name}</div>
              <div className="step-desc">{step.desc}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
