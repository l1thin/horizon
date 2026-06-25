import { useState, useEffect, useCallback, useRef } from 'react';

export function useCountdownTimer(durationSeconds = 300) {
  const [secondsLeft, setSecondsLeft] = useState(durationSeconds);
  const [isRunning, setIsRunning] = useState(false);
  const intervalRef = useRef(null);

  const start = useCallback(() => {
    setIsRunning(true);
  }, []);

  const stop = useCallback(() => {
    setIsRunning(false);
  }, []);

  const reset = useCallback((newDuration) => {
    setIsRunning(false);
    setSecondsLeft(newDuration !== undefined ? newDuration : durationSeconds);
  }, [durationSeconds]);

  useEffect(() => {
    if (isRunning && secondsLeft > 0) {
      intervalRef.current = setInterval(() => {
        setSecondsLeft(prev => prev - 1);
      }, 1000);
    } else if (isRunning && secondsLeft === 0) {
      setIsRunning(false);
      if (intervalRef.current) clearInterval(intervalRef.current);
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isRunning, secondsLeft]);

  const isExpired = secondsLeft === 0;

  return { secondsLeft, isExpired, start, stop, reset };
}
