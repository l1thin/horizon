import React, { useRef, useState } from 'react';
import { uploadResume } from '../services/api';

export default function HeroPage({ onSessionCreated }) {
  const fileInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);
    try {
      const data = await uploadResume(file);
      onSessionCreated(data.session_id);
    } catch (err) {
      console.error("Upload error:", err);
      setError(err.message || "Failed to upload resume.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="hero-container">
      <h1 className="hero-title">Horizon</h1>
      <p className="hero-tagline">Your AI interview partner. Speak freely.</p>
      
      <input 
        type="file" 
        accept=".pdf,.docx" 
        ref={fileInputRef} 
        onChange={handleFileChange} 
        style={{ display: 'none' }} 
      />
      
      <button 
        className="hero-button"
        onClick={() => fileInputRef.current?.click()}
        disabled={isUploading}
      >
        {isUploading ? "Uploading…" : "Upload Your Resume"}
      </button>

      {error && (
        <div style={{ textAlign: 'center', marginTop: '16px' }}>
          <p className="hero-error-text">{error}</p>
          <button 
            className="hero-retry-btn"
            onClick={() => fileInputRef.current?.click()}
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
