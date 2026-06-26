import React, { useState } from 'react';
import { createSession } from '../services/api';

export default function LanguagePage({ sessionId, onInterviewStart }) {
  const [language, setLanguage] = useState('Python');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      await createSession(sessionId, language);
      onInterviewStart(language);
    } catch (err) {
      console.error("Language selection error:", err);
      setError(err.message || "Failed to start session.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="language-container">
      <div className="language-card">
        <h2 className="language-title">What language will you code in today?</h2>
        
        <select 
          className="language-select" 
          value={language} 
          onChange={(e) => setLanguage(e.target.value)}
          disabled={isSubmitting}
        >
          <option value="Python">Python</option>
          <option value="JavaScript">JavaScript</option>
          <option value="Java">Java</option>
          <option value="C++">C++</option>
        </select>
        
        <button 
          className="hero-button language-button"
          onClick={handleSubmit}
          disabled={isSubmitting}
        >
          {isSubmitting ? "Starting..." : "Start Interview \u2192"}
        </button>
        
        {error && (
          <p className="hero-error-text" style={{ marginTop: '16px', fontSize: '14px' }}>
            {error}
          </p>
        )}
      </div>
    </div>
  );
}
