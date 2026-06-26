import { useState, useCallback, useRef, useEffect } from 'react';

export function useSpeechRecognition({ onSilence, silenceThresholdMs = 3000 } = {}) {
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [isListening, setIsListening] = useState(false);
  
  const recognitionRef = useRef(null);
  const silenceTimerRef = useRef(null);
  const latestTranscriptRef = useRef('');
  const onSilenceRef = useRef(onSilence);

  useEffect(() => {
    onSilenceRef.current = onSilence;
  }, [onSilence]);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn("SpeechRecognition API not supported in this browser.");
      return;
    }
    
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      let finalStr = '';
      let interimStr = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalStr += event.results[i][0].transcript + ' ';
        } else {
          interimStr += event.results[i][0].transcript;
        }
      }
      
      if (finalStr) {
        setTranscript(prev => {
          const updated = (prev + ' ' + finalStr).trim();
          latestTranscriptRef.current = updated;
          return updated;
        });
      }
      setInterimTranscript(interimStr);

      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = setTimeout(() => {
        if (onSilenceRef.current && latestTranscriptRef.current) {
          onSilenceRef.current(latestTranscriptRef.current);
        }
      }, silenceThresholdMs);
    };

    recognition.onerror = (event) => {
      console.error("SpeechRecognition error:", event.error);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      if (recognitionRef.current) recognitionRef.current.abort();
    };
  }, [silenceThresholdMs]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) return;
    try {
      setTranscript('');
      setInterimTranscript('');
      latestTranscriptRef.current = '';
      recognitionRef.current.start();
      setIsListening(true);
      
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = setTimeout(() => {
        if (onSilenceRef.current && latestTranscriptRef.current) {
          onSilenceRef.current(latestTranscriptRef.current);
        }
      }, silenceThresholdMs);
    } catch (e) {
      console.warn("Recognition already started or error:", e);
    }
  }, [silenceThresholdMs]);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    try {
      recognitionRef.current.stop();
    } catch (e) {}
    setIsListening(false);
  }, []);

  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
    latestTranscriptRef.current = '';
  }, []);

  return { transcript, interimTranscript, isListening, startListening, stopListening, resetTranscript };
}
