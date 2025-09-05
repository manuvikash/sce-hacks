import React, { useState } from 'react';
import './App.css';

function App() {
  const [repoUrl, setRepoUrl] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [processingStatus, setProcessingStatus] = useState('');
  const [docsUrl, setDocsUrl] = useState('');
  const [error, setError] = useState('');
  const [stepStatuses, setStepStatuses] = useState({});

  const steps = [
    'Processing',
    'Cloning Repo',
    'Parsing files',
    'Identifying APIs',
    'Creating OpenAPI Specs yaml',
    'Creating Docs'
  ];

  const validateGitHubUrl = (url) => {
    const githubRegex = /^https:\/\/github\.com\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+\/?$/;
    return githubRegex.test(url.trim());
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!repoUrl.trim()) {
      setError('Please enter a GitHub repository URL');
      return;
    }

    if (!validateGitHubUrl(repoUrl)) {
      setError('Please enter a valid GitHub repository URL (e.g., https://github.com/username/repository)');
      return;
    }

    setIsProcessing(true);
    setCurrentStep(0);
    setError('');
    setDocsUrl('');
    setStepStatuses({});

    try {
      // Send repo URL to backend
      const response = await fetch('/api/generate-docs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ repoUrl: repoUrl.trim() }),
      });

      if (!response.ok) {
        throw new Error('Failed to start processing');
      }

      const data = await response.json();
      console.log('Processing started:', data);
      
      // Start polling for status
      pollStatus();
    } catch (err) {
      // Move to processing page to show error
      setIsProcessing(true);
      setStepStatuses({ 0: 'failed' });
      setError(err.message);
    }
  };

  const pollStatus = async () => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        setProcessingStatus(data.status);
        setCurrentStep(data.currentStep || 0);
        
        // Update step statuses based on current step
        const newStepStatuses = {};
        for (let i = 0; i < steps.length; i++) {
          if (i < (data.currentStep || 0)) {
            newStepStatuses[i] = 'completed';
          } else if (i === (data.currentStep || 0)) {
            newStepStatuses[i] = 'active';
          } else {
            newStepStatuses[i] = 'pending';
          }
        }
        setStepStatuses(newStepStatuses);
        
        if (data.completed) {
          clearInterval(pollInterval);
          setIsProcessing(false);
          // Mark all steps as completed
          const completedStatuses = {};
          for (let i = 0; i < steps.length; i++) {
            completedStatuses[i] = 'completed';
          }
          setStepStatuses(completedStatuses);
          if (data.docsUrl) {
            setDocsUrl(data.docsUrl);
          }
        } else if (data.error) {
          clearInterval(pollInterval);
          // Mark current step as failed
          const failedStatuses = { ...newStepStatuses };
          failedStatuses[data.currentStep || 0] = 'failed';
          setStepStatuses(failedStatuses);
          setError(data.error);
        }
      } catch (err) {
        console.error('Error polling status:', err);
      }
    }, 2000); // Poll every 2 seconds
  };

  const handleViewDocs = () => {
    if (docsUrl) {
      window.open(docsUrl, '_blank');
    }
  };

  return (
    <div className="App">
      <div className="container">
        {!isProcessing ? (
          <div className="landing-page">
            <div className="hero-section">
              <h1 className="hero-title">
                Generate API docs in seconds!
              </h1>
              <p className="hero-subtitle">
                Transform your GitHub repository into beautiful, comprehensive API documentation.
              </p>
              
              <form onSubmit={handleSubmit} className="input-form">
                <div className="input-container">
                  <div className="input-field-wrapper">
                    <input
                      type="url"
                      value={repoUrl}
                      onChange={(e) => setRepoUrl(e.target.value)}
                      placeholder="Ask me to generate docs for https://github.com/username/repository"
                      className="repo-input"
                    />
                    <button type="submit" className="send-btn">
                      <span className="send-icon">↑</span>
                    </button>
                  </div>
                </div>
                {error && <div className="error-message">{error}</div>}
              </form>
            </div>
          </div>
        ) : (
          <div className="processing-page">
            <div className="processing-container">
              <h2 className="processing-title">Generating Your API Documentation</h2>
              <div className="steps-container">
                {steps.map((step, index) => {
                  const status = stepStatuses[index] || 'pending';
                  return (
                    <div
                      key={index}
                      className={`step ${status}`}
                    >
                      <div className="step-number">
                        {status === 'completed' ? (
                          <span className="step-icon">✓</span>
                        ) : status === 'failed' ? (
                          <span className="step-icon">✕</span>
                        ) : status === 'active' ? (
                          <div className="spinner"></div>
                        ) : (
                          <span className="step-number-text">{index + 1}</span>
                        )}
                      </div>
                      <div className="step-text">{step}</div>
                    </div>
                  );
                })}
              </div>
              {error ? (
                <div className="error-container">
                  <div className="error-icon">⚠️</div>
                  <div className="error-title">Processing Failed</div>
                  <div className="error-message-processing">{error}</div>
                  <button onClick={() => {
                    setIsProcessing(false);
                    setError('');
                    setCurrentStep(0);
                    setProcessingStatus('');
                    setDocsUrl('');
                    setStepStatuses({});
                  }} className="retry-btn">
                    Try Again
                  </button>
                </div>
              ) : (
                <>
                  <div className="status-message">
                    {processingStatus || `Step ${currentStep + 1}: ${steps[currentStep]}`}
                  </div>
                  {docsUrl && (
                    <button onClick={handleViewDocs} className="view-docs-btn">
                      View Generated Docs
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
