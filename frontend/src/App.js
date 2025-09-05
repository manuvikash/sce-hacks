import React, { useState } from 'react';
import './App.css';

function App() {
  const [repoUrl, setRepoUrl] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('');
  const [error, setError] = useState('');

  const DOCS_HOST = 'http://localhost:3333';

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
    setError('');
    setProcessingStatus('Processing your request...');

    try {
      const response = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl.trim() }),
      });

      if (!response.ok) throw new Error('Failed to process request');

      const data = await response.json();
      console.log('Processing completed:', data);

      // Mark as completed (✓ will show) and allow viewing docs
      setProcessingStatus('Completed!');
      setIsProcessing(false);
    } catch (err) {
      setError(err.message);
      setProcessingStatus('Failed');
    }
  };

  const handleViewDocs = () => {
    window.open(DOCS_HOST, '_blank');
  };

  return (
    <div className="App">
      <div className="container">
        {!isProcessing ? (
          <div className="landing-page">
            <div className="hero-section">
              <h1 className="hero-title">Generate API docs in seconds!</h1>
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

              <div className="processing-status">
                <div className="status-indicator">
                  {error ? (
                    <div className="status-icon failed">✕</div>
                  ) : processingStatus === 'Completed!' ? (
                    <div className="status-icon completed">✓</div>
                  ) : (
                    <div className="spinner"></div>
                  )}
                </div>
                <div className="status-text">
                  {error ? 'Processing Failed' : processingStatus}
                </div>
              </div>

              {error ? (
                <div className="error-container">
                  <div className="error-message-processing">{error}</div>
                  <button
                    onClick={() => {
                      setIsProcessing(false);
                      setError('');
                      setProcessingStatus('');
                    }}
                    className="retry-btn"
                  >
                    Try Again
                  </button>
                </div>
              ) : (
                processingStatus === 'Completed!' && (
                  <button onClick={handleViewDocs} className="view-docs-btn">
                    View Generated Docs
                  </button>
                )
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
