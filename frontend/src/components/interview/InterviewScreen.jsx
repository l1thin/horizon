import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';
import { useIntegrityTracker } from '../../hooks/useIntegrityTracker';
import { WS_TYPE } from '../../constants/wsMessageTypes';
import Orb from '../orb/Orb';
import { ORB_STATE } from '../orb/OrbStates';
import ProgressPill from './ProgressPill';
import LiveTranscript from './LiveTranscript';
import StarHintCard from './StarHintCard';

export default function InterviewScreen({ sessionId, onCodingQuestion, onSessionEnd }) {
  const [orbState, setOrbState] = useState(ORB_STATE.IDLE);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [toastMessage, setToastMessage] = useState('');

  const { speak, stop: stopSpeaking, isSpeaking } = useSpeechSynthesis();
  const { markQuestionStart, markSpeechStarted, integritySnapshot, resetIntegrity } = useIntegrityTracker();
  
  const handleMessage = useCallback((msg) => {
    switch (msg.type) {
      case WS_TYPE.QUESTION:
      case WS_TYPE.FOLLOW_UP:
        setCurrentQuestion(msg.payload);
        setOrbState(ORB_STATE.SPEAKING);
        speak(msg.payload.text, () => {
          setOrbState(ORB_STATE.LISTENING);
          resetTranscript();
          startListening();
          markQuestionStart();
        });
        break;
      case WS_TYPE.CODING:
        if (onCodingQuestion) onCodingQuestion(msg.payload);
        break;
      case WS_TYPE.EVAL_ACK:
        setToastMessage('✓');
        setTimeout(() => setToastMessage(''), 1500);
        setOrbState(ORB_STATE.IDLE);
        break;
      case WS_TYPE.END:
        if (onSessionEnd) onSessionEnd(sessionId);
        break;
      case WS_TYPE.ERROR:
        console.error("WS Error:", msg.payload);
        break;
      default:
        break;
    }
  }, [markQuestionStart, onCodingQuestion, onSessionEnd, sessionId, speak]);

  const { sendMessage, connectionStatus } = useWebSocket({
    sessionId,
    onMessage: handleMessage
  });

  const currentQuestionRef = useRef(currentQuestion);
  useEffect(() => {
    currentQuestionRef.current = currentQuestion;
  }, [currentQuestion]);

  const handleSilence = useCallback((finalTranscript) => {
    markSpeechStarted();
    stopListening();
    setOrbState(ORB_STATE.THINKING);
    sendMessage({
      type: WS_TYPE.ANSWER,
      payload: {
        question_id: currentQuestionRef.current?.question_id,
        transcript: finalTranscript,
        integrity: integritySnapshot()
      }
    });
    resetIntegrity();
  }, [integritySnapshot, markSpeechStarted, resetIntegrity, sendMessage]);

  const { transcript, interimTranscript, isListening, startListening, stopListening, resetTranscript } = useSpeechRecognition({
    onSilence: handleSilence,
    silenceThresholdMs: 3000
  });

  // Adding these to the dependency array of handleMessage above would cause cycles or stale closures
  // so we used refs, or we can just ignore it since handleMessage is fully recreated anyway but we fixed useWebSocket.

  // If transcript changes, user is speaking, so mark speech started
  useEffect(() => {
    if (transcript || interimTranscript) {
      markSpeechStarted();
    }
  }, [transcript, interimTranscript, markSpeechStarted]);

  const handleDoneManual = () => {
    const finalTx = transcript + ' ' + interimTranscript;
    handleSilence(finalTx.trim());
  };

  const handleOrbClick = () => {
    if (orbState === ORB_STATE.LISTENING) {
      handleDoneManual();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minHeight: '100vh', backgroundColor: '#0a0a14', color: '#fff', padding: '2rem' }}>
      {toastMessage && (
        <div style={{ position: 'fixed', top: '20px', right: '20px', background: '#22c55e', color: 'white', padding: '10px 20px', borderRadius: '20px', fontWeight: 'bold' }}>
          {toastMessage}
        </div>
      )}
      
      <div style={{ position: 'absolute', top: '20px', left: '20px', color: '#8f93a2' }}>
        Status: {connectionStatus}
      </div>

      <ProgressPill />
      
      <Orb state={orbState} onClick={handleOrbClick} />
      
      {currentQuestion && currentQuestion.type === 'behavioral' && (
        <StarHintCard />
      )}
      
      <LiveTranscript transcript={transcript} interim={interimTranscript} />
      
      {orbState === ORB_STATE.LISTENING && (
        <button 
          onClick={handleDoneManual}
          className="hero-button"
          style={{ marginTop: '2rem', padding: '10px 30px', fontSize: '16px' }}
        >
          Done Speaking
        </button>
      )}
    </div>
  );
}
