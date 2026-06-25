import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { submitCode } from '../../services/api';
import { useCountdownTimer } from '../../hooks/useCountdownTimer';
import CountdownTimer from './CountdownTimer';
import TerminalOutput from './TerminalOutput';

export default function CodingSection({ question, sessionId, preferredLanguage, sendMessage, onComplete }) {
  const [code, setCode] = useState('');
  const [isTerminalVisible, setIsTerminalVisible] = useState(false);
  const [terminalState, setTerminalState] = useState({ stdout: '', stderr: '', status: '', isLoading: false });
  const [toastMessage, setToastMessage] = useState('');

  const timeLimit = question?.time_limit_seconds || 300;
  const { secondsLeft, isExpired, start } = useCountdownTimer(timeLimit);

  useEffect(() => {
    start();
  }, [start]);

  useEffect(() => {
    if (isExpired) {
      handleTimeout();
    }
  }, [isExpired]);

  const handleTimeout = () => {
    sendMessage({ type: 'code_submit', payload: { code, language: preferredLanguage, question_id: question?.question_id, timed_out: true } });
    setToastMessage("Time's up — submitting your code…");
    setTimeout(() => {
      if (onComplete) onComplete();
    }, 2000);
  };

  const handleRun = async () => {
    setIsTerminalVisible(true);
    setTerminalState({ stdout: '', stderr: '', status: '', isLoading: true });
    try {
      const res = await submitCode(sessionId, { code, language: preferredLanguage, question_id: question?.question_id });
      setTerminalState({
        stdout: res.stdout || '',
        stderr: res.stderr || '',
        status: res.status || 'Accepted',
        isLoading: false
      });
    } catch (err) {
      setTerminalState({
        stdout: '',
        stderr: err.message,
        status: 'Runtime Error',
        isLoading: false
      });
    }
  };

  const handleSubmit = () => {
    sendMessage({ type: 'code_submit', payload: { code, language: preferredLanguage, question_id: question?.question_id, timed_out: false } });
    if (onComplete) onComplete();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100%', backgroundColor: 'transparent', textAlign: 'left' }}>
      {toastMessage && (
        <div style={{ position: 'fixed', top: '20px', left: '50%', transform: 'translateX(-50%)', background: '#ef4444', color: 'white', padding: '10px 20px', borderRadius: '20px', fontWeight: 'bold', zIndex: 1000 }}>
          {toastMessage}
        </div>
      )}
      
      {/* Top bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 2rem', backgroundColor: '#ffffff', borderBottom: '1px solid #e5e7eb' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          {/* Small floating orb circle */}
          <div style={{ width: '16px', height: '16px', borderRadius: '50%', background: 'conic-gradient(from 0deg, #6366f1, #a78bfa, #6366f1)', animation: 'spin 3s linear infinite' }}></div>
          <div style={{ color: '#111827', fontSize: '16px', fontWeight: '500' }}>{question?.text || 'Coding Challenge'}</div>
        </div>
        <CountdownTimer secondsLeft={secondsLeft} isExpired={isExpired} />
      </div>

      {/* Editor */}
      <div style={{ flex: 1, position: 'relative' }}>
        <Editor 
          height="100%" 
          defaultLanguage={(preferredLanguage || 'python').toLowerCase()} 
          theme="vs-light"
          options={{ fontSize: 14, minimap: { enabled: false }, scrollBeyondLastLine: false }}
          onChange={value => setCode(value || '')} 
        />
      </div>

      {/* Terminal */}
      {isTerminalVisible && (
        <TerminalOutput 
          stdout={terminalState.stdout} 
          stderr={terminalState.stderr} 
          status={terminalState.status} 
          isLoading={terminalState.isLoading} 
        />
      )}

      {/* Bottom bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem 2rem', backgroundColor: '#ffffff', borderTop: '1px solid #e5e7eb' }}>
        <button onClick={handleRun} style={{ background: 'transparent', color: '#6b7280', border: '1px solid #e5e7eb', borderRadius: '5px', padding: '8px 20px', cursor: 'pointer', fontWeight: 'bold' }}>
          Run
        </button>
        <button onClick={handleSubmit} style={{ background: 'transparent', color: '#6b7280', border: '1px solid #e5e7eb', borderRadius: '5px', padding: '8px 20px', cursor: 'pointer', fontWeight: 'bold' }}>
          Submit Early
        </button>
      </div>
      
      <style>{`
        @keyframes spin { 100% { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
