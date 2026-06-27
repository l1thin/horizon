import React, { useState } from 'react';
import HeroPage from './pages/HeroPage';
import LoadingPage from './pages/LoadingPage';
import LanguagePage from './pages/LanguagePage';
import InterviewPage from './pages/InterviewPage';
import ReportPage from './pages/ReportPage';
import AntiGravityBackground from './components/AntiGravityBackground';

export default function App() {
  const [stage, setStage] = useState('hero'); // "hero" | "loading" | "language" | "interview" | "report"
  const [sessionId, setSessionId] = useState(null);

  const handleSessionCreated = (id) => {
    setSessionId(id);
    setStage('loading');
  };

  const handleReady = () => {
    setStage('language');
  };

  const handleInterviewStart = (language) => {
    console.log("Starting interview with language:", language);
    setStage('interview');
  };

  return (
    <>
      <AntiGravityBackground isActive={stage === 'hero'} />
      {stage === 'hero' && <HeroPage onSessionCreated={handleSessionCreated} />}
      {stage === 'loading' && <LoadingPage sessionId={sessionId} onReady={handleReady} />}
      {stage === 'language' && <LanguagePage sessionId={sessionId} onInterviewStart={handleInterviewStart} />}
      {stage === 'interview' && <InterviewPage sessionId={sessionId} />}
      {stage === 'report' && <ReportPage sessionId={sessionId} />}

      {/* Temporary Dev Navigation */}
      <div className="print-btn-container" style={{ position: 'fixed', bottom: 0, left: 0, right: 0, padding: '10px', background: 'rgba(0,0,0,0.8)', display: 'flex', justifyContent: 'center', gap: '10px', zIndex: 9999, borderTop: '1px solid #333' }}>
        {['hero', 'loading', 'language', 'interview', 'report'].map(s => (
          <button 
            key={s} 
            onClick={() => setStage(s)} 
            style={{ 
              padding: '5px 10px', 
              background: stage === s ? '#3b82f6' : '#333', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px', 
              cursor: 'pointer', 
              textTransform: 'capitalize',
              fontSize: '12px'
            }}
          >
            {s}
          </button>
        ))}
      </div>
    </>
  );
}
