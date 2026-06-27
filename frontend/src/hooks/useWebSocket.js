import { useState, useEffect, useRef, useCallback } from 'react';

export function useWebSocket({ sessionId, onMessage }) {
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const wsRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxAttempts = 3;
  const isComponentMounted = useRef(true);
  const onMessageRef = useRef(onMessage);
  const sessionEnded = useRef(false);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const connect = useCallback(() => {
    if (!sessionId || !isComponentMounted.current || sessionEnded.current) return;
    
    setConnectionStatus('connecting');
    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/session/${sessionId}`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!isComponentMounted.current) {
        ws.close();
        return;
      }
      setConnectionStatus('connected');
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      if (!isComponentMounted.current) return;
      try {
        const parsedJSON = JSON.parse(event.data);
        if (onMessageRef.current) onMessageRef.current(parsedJSON);
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
      }
    };

    ws.onclose = () => {
      if (!isComponentMounted.current) return;
      
      // Don't reconnect if the session ended intentionally
      if (sessionEnded.current) {
        setConnectionStatus('ended');
        return;
      }

      if (reconnectAttempts.current < maxAttempts) {
        setConnectionStatus('disconnected');
        const delay = Math.pow(2, reconnectAttempts.current) * 2000;
        reconnectAttempts.current += 1;
        setTimeout(() => {
          connect();
        }, delay);
      } else {
        setConnectionStatus('failed');
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
    };

  }, [sessionId]);

  useEffect(() => {
    isComponentMounted.current = true;
    sessionEnded.current = false;
    connect();

    return () => {
      isComponentMounted.current = false;
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((obj) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(obj));
    } else {
      console.warn("WebSocket is not open. Cannot send message:", obj);
    }
  }, []);

  const markSessionEnded = useCallback(() => {
    sessionEnded.current = true;
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
    }
    setConnectionStatus('ended');
  }, []);

  return { sendMessage, connectionStatus, markSessionEnded };
}
