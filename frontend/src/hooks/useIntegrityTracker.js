import { useRef, useCallback, useEffect } from 'react';

export function useIntegrityTracker() {
  const metricsRef = useRef({
    tab_switches: 0,
    think_time_ms: 0
  });
  
  const timestampsRef = useRef({
    questionStart: null,
    speechStarted: null
  });

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        metricsRef.current.tab_switches += 1;
      }
    };
    
    const handleBlur = () => {
      metricsRef.current.tab_switches += 1;
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleBlur);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleBlur);
    };
  }, []);

  const markQuestionStart = useCallback(() => {
    timestampsRef.current.questionStart = Date.now();
    timestampsRef.current.speechStarted = null;
  }, []);

  const markSpeechStarted = useCallback(() => {
    if (!timestampsRef.current.speechStarted && timestampsRef.current.questionStart) {
      timestampsRef.current.speechStarted = Date.now();
      metricsRef.current.think_time_ms += (timestampsRef.current.speechStarted - timestampsRef.current.questionStart);
    }
  }, []);

  const integritySnapshot = useCallback(() => {
    let currentThinkTime = metricsRef.current.think_time_ms;
    if (!timestampsRef.current.speechStarted && timestampsRef.current.questionStart) {
      currentThinkTime += (Date.now() - timestampsRef.current.questionStart);
    }

    return {
      tab_switches: metricsRef.current.tab_switches,
      think_time_ms: currentThinkTime,
      wpm_estimate: 0
    };
  }, []);

  const resetIntegrity = useCallback(() => {
    metricsRef.current = { tab_switches: 0, think_time_ms: 0 };
    timestampsRef.current = { questionStart: null, speechStarted: null };
  }, []);

  return { markQuestionStart, markSpeechStarted, integritySnapshot, resetIntegrity };
}
