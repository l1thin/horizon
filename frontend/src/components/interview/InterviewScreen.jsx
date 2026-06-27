import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useIntegrityTracker } from '../../hooks/useIntegrityTracker';
import { WS_TYPE } from '../../constants/wsMessageTypes';
import ProgressPill from './ProgressPill';
import StarHintCard from './StarHintCard';

export default function InterviewScreen({ sessionId, sendMessage, connectionStatus, incomingMessage, clearIncomingMessage, onCodingQuestion, onSessionEnd }) {
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [toastMessage, setToastMessage] = useState('');
  const [answerText, setAnswerText] = useState('');
  const [isThinking, setIsThinking] = useState(false);

  const { markQuestionStart, markSpeechStarted, integritySnapshot, resetIntegrity } = useIntegrityTracker();
  
  const handleMessage = useCallback((msg) => {
    if (msg.type === WS_TYPE.CODING) {
      if (onCodingQuestion) onCodingQuestion(msg.payload);
    } else if (msg.type === WS_TYPE.EVAL_ACK) {
      setToastMessage('✓');
      setTimeout(() => setToastMessage(''), 1500);
      setIsThinking(false);
    } else if (msg.type === WS_TYPE.END) {
      if (onSessionEnd) onSessionEnd(sessionId);
    } else if (msg.type === WS_TYPE.ERROR) {
      console.error("WS Error:", msg.payload);
      setIsThinking(false);
    } else if (msg.payload && msg.payload.question_id) {
      setCurrentQuestion(msg.payload);
      setIsThinking(false);
      markQuestionStart();
    }
  }, [markQuestionStart, onCodingQuestion, onSessionEnd, sessionId]);

  useEffect(() => {
    if (incomingMessage) {
      handleMessage(incomingMessage);
      if (clearIncomingMessage) clearIncomingMessage();
    }
  }, [incomingMessage]); // eslint-disable-line react-hooks/exhaustive-deps

  const currentQuestionRef = useRef(currentQuestion);
  useEffect(() => {
    currentQuestionRef.current = currentQuestion;
  }, [currentQuestion]);

  const handleSubmit = useCallback(() => {
    if (!answerText.trim()) return;
    
    setIsThinking(true);
    sendMessage({
      type: WS_TYPE.ANSWER,
      payload: {
        question_id: currentQuestionRef.current?.question_id,
        transcript: answerText.trim(),
        integrity: integritySnapshot()
      }
    });
    setAnswerText('');
    resetIntegrity();
  }, [answerText, integritySnapshot, resetIntegrity, sendMessage]);

  // When user starts typing, we can mark "speech started" for integrity
  const handleTextChange = (e) => {
    if (!answerText) {
      markSpeechStarted();
    }
    setAnswerText(e.target.value);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minHeight: '100vh', backgroundColor: 'transparent', color: '#111827', padding: '2rem' }}>
      {toastMessage && (
        <div style={{ position: 'fixed', top: '20px', right: '20px', background: '#22c55e', color: 'white', padding: '10px 20px', borderRadius: '20px', fontWeight: 'bold' }}>
          {toastMessage}
        </div>
      )}
      
      <div style={{ position: 'absolute', top: '20px', left: '20px', color: '#6b7280' }}>
        Status: {connectionStatus}
      </div>

      <ProgressPill />
      
      {currentQuestion && currentQuestion.type === 'behavioral' && (
        <StarHintCard />
      )}
      
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', width: '100%', maxWidth: '800px' }}>
        {currentQuestion ? (
          <div style={{ width: '100%', background: 'white', padding: '2rem', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', marginBottom: '2rem' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1.5rem', color: '#1f2937' }}>
              {currentQuestion.text}
            </h2>
            
            <textarea
              value={answerText}
              onChange={handleTextChange}
              placeholder="Type your answer here..."
              disabled={isThinking}
              style={{
                width: '100%',
                minHeight: '150px',
                padding: '1rem',
                borderRadius: '8px',
                border: '1px solid #d1d5db',
                fontSize: '1rem',
                fontFamily: 'inherit',
                resize: 'vertical',
                marginBottom: '1rem',
                backgroundColor: isThinking ? '#f3f4f6' : 'white'
              }}
            />
            
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button 
                onClick={handleSubmit}
                disabled={isThinking || !answerText.trim()}
                className="hero-button"
                style={{ 
                  padding: '10px 30px', 
                  fontSize: '16px',
                  opacity: (isThinking || !answerText.trim()) ? 0.5 : 1,
                  cursor: (isThinking || !answerText.trim()) ? 'not-allowed' : 'pointer'
                }}
              >
                {isThinking ? 'Sending...' : 'Submit Answer'}
              </button>
            </div>
          </div>
        ) : (
          <div style={{ fontSize: '1.25rem', color: '#6b7280', animation: 'pulse 2s infinite' }}>
            Waiting for next question...
          </div>
        )}
      </div>
    </div>
  );
}
