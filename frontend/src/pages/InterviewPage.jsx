import React, { useState, useCallback, useRef } from 'react';
import InterviewScreen from '../components/interview/InterviewScreen';
import CodingSection from '../components/coding/CodingSection';
import { useWebSocket } from '../hooks/useWebSocket';
import { WS_TYPE } from '../constants/wsMessageTypes';

export default function InterviewPage({ sessionId, onSessionEnd }) {
  const [showCoding, setShowCoding] = useState(false);
  const [codingPayload, setCodingPayload] = useState(null);
  const [interviewScreenMsg, setInterviewScreenMsg] = useState(null);
  const markSessionEndedRef = useRef(null);

  const handleMessage = useCallback((msg) => {
    if (msg.type === WS_TYPE.CODING) {
      setCodingPayload(msg.payload);
      setShowCoding(true);
    } else if (msg.type === WS_TYPE.END) {
      console.log("Session Ended:", sessionId);
      // Stop reconnection and transition to report
      if (markSessionEndedRef.current) markSessionEndedRef.current();
      if (onSessionEnd) onSessionEnd(sessionId);
    } else {
      // Pass down to InterviewScreen
      setInterviewScreenMsg(msg);
    }
  }, [sessionId, onSessionEnd]);

  const { sendMessage, connectionStatus, markSessionEnded } = useWebSocket({
    sessionId,
    onMessage: handleMessage
  });

  // Keep the ref in sync
  markSessionEndedRef.current = markSessionEnded;

  const handleCodingComplete = () => {
    setShowCoding(false);
  };

  if (showCoding) {
    return (
      <CodingSection 
        question={codingPayload} 
        sessionId={sessionId} 
        preferredLanguage="python" 
        sendMessage={sendMessage}
        onComplete={handleCodingComplete}
      />
    );
  }

  return (
    <InterviewScreen 
      sessionId={sessionId} 
      sendMessage={sendMessage}
      connectionStatus={connectionStatus}
      incomingMessage={interviewScreenMsg}
      clearIncomingMessage={() => setInterviewScreenMsg(null)}
    />
  );
}
