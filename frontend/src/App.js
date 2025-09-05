import React, { useState } from 'react';
import './App.css';

function App() {
  const [repoUrl, setRepoUrl] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('');
  const [docsUrl, setDocsUrl] = useState('');
  const [error, setError] = useState('');

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
    setDocsUrl('');
    setProcessingStatus('Processing your request...');

    try {
      // Send repo URL to backend
      const response = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ repo_url: repoUrl.trim() }),
      });

      if (!response.ok) {
        throw new Error('Failed to process request');
      }

      const data = await response.json();
      console.log('Processing completed:', data);
      
      // Mark as completed
      setProcessingStatus('Completed!');
      setIsProcessing(false);
      
      // If there's a docs URL in the response, set it
      if (data.docs_url || data.docsUrl) {
        setDocsUrl(data.docs_url || data.docsUrl);
      }
    } catch (err) {
      setError(err.message);
      setProcessingStatus('Failed');
    }
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
                  <button onClick={() => {
                    setIsProcessing(false);
                    setError('');
                    setProcessingStatus('');
                    setDocsUrl('');
                  }} className="retry-btn">
                    Try Again
                  </button>
                </div>
              ) : processingStatus === 'Completed!' && docsUrl && (
                <button onClick={handleViewDocs} className="view-docs-btn">
                  View Generated Docs
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
