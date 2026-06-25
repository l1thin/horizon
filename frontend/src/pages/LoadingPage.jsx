import React, { useState, useEffect } from 'react';
import { LOADING_MESSAGES } from '../constants/loadingMessages';
import { getSessionStatus } from '../services/api';

export default function LoadingPage({ sessionId, onReady }) {
  const [messageIndex, setMessageIndex] = useState(0);
  const [error, setError] = useState(false);

  useEffect(() => {
    const messageInterval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 3000);

    return () => clearInterval(messageInterval);
  }, []);

  useEffect(() => {
    if (!sessionId) return;

    const pollStatus = async () => {
      try {
        const data = await getSessionStatus(sessionId);
        if (data.status === 'ready') {
          onReady();
        } else if (data.status === 'error') {
          setError(true);
        }
      } catch (err) {
        console.error("Polling error:", err);
        setError(true);
      }
    };

    const pollInterval = setInterval(() => {
      if (!error) {
        pollStatus();
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [sessionId, onReady, error]);

  if (error) {
    return (
      <div className="loading-container">
        <p className="hero-error-text" style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>
          Something went wrong. Please try again.
        </p>
        <button 
          className="hero-button" 
          onClick={() => window.location.reload()}
        >
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="loading-container">
      <div className="spinner"></div>
      <p className="loading-text">{LOADING_MESSAGES[messageIndex]}</p>
    </div>
  );
}
