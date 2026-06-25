import React, { useState } from 'react';
import InterviewScreen from '../components/interview/InterviewScreen';

export default function InterviewPage({ sessionId }) {
  const [showCoding, setShowCoding] = useState(false);
  const [codingPayload, setCodingPayload] = useState(null);

  const handleCodingQuestion = (payload) => {
    setCodingPayload(payload);
    setShowCoding(true);
  };

  const handleSessionEnd = (id) => {
    // Parent handles this usually, or we can just log for now
    console.log("Session Ended:", id);
  };

  if (showCoding) {
    return <div style={{ color: 'white', textAlign: 'center', marginTop: '2rem' }}>Coding Section (Stub) - Payload: {JSON.stringify(codingPayload)}</div>;
  }

  return (
    <InterviewScreen 
      sessionId={sessionId} 
      onCodingQuestion={handleCodingQuestion} 
      onSessionEnd={handleSessionEnd} 
    />
  );
}
