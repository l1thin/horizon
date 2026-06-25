import React, { useState } from 'react';
import HeroPage from './pages/HeroPage';
import LoadingPage from './pages/LoadingPage';
import LanguagePage from './pages/LanguagePage';
import InterviewPage from './pages/InterviewPage';

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
      {stage === 'hero' && <HeroPage onSessionCreated={handleSessionCreated} />}
      {stage === 'loading' && <LoadingPage sessionId={sessionId} onReady={handleReady} />}
      {stage === 'language' && <LanguagePage sessionId={sessionId} onInterviewStart={handleInterviewStart} />}
      {stage === 'interview' && <InterviewPage sessionId={sessionId} />}
      {stage === 'report' && <div>Report Page (Stub)</div>}
    </>
  );
}
