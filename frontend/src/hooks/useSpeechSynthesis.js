import { useState, useCallback, useRef } from 'react';

export function useSpeechSynthesis() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const synth = window.speechSynthesis;
  const currentChunksRef = useRef([]);
  const onEndCallbackRef = useRef(null);

  const stop = useCallback(() => {
    if (synth) {
      synth.cancel();
    }
    setIsSpeaking(false);
    currentChunksRef.current = [];
    if (onEndCallbackRef.current) {
      onEndCallbackRef.current();
      onEndCallbackRef.current = null;
    }
  }, [synth]);

  const speak = useCallback((text, onEnd) => {
    if (!synth) {
      console.warn("SpeechSynthesis not supported.");
      if (onEnd) onEnd();
      return;
    }
    stop();
    setIsSpeaking(true);
    onEndCallbackRef.current = onEnd;

    let chunks = [text];
    if (text.length > 200) {
      const regex = /([^.!?]+[.!?]+)/g;
      const matched = text.match(regex);
      if (matched && matched.length > 0) {
        chunks = matched.map(s => s.trim()).filter(Boolean);
      }
    }
    currentChunksRef.current = chunks;

    const playNextChunk = () => {
      if (currentChunksRef.current.length === 0) {
        setIsSpeaking(false);
        if (onEndCallbackRef.current) {
          onEndCallbackRef.current();
          onEndCallbackRef.current = null;
        }
        return;
      }
      const chunkText = currentChunksRef.current.shift();
      const utterance = new SpeechSynthesisUtterance(chunkText);
      
      const voices = synth.getVoices();
      const englishVoices = voices.filter(v => v.lang.startsWith('en'));
      const naturalVoice = englishVoices.find(v => v.name.toLowerCase().includes('natural') || v.name.toLowerCase().includes('google'));
      if (naturalVoice) utterance.voice = naturalVoice;
      else if (englishVoices.length > 0) utterance.voice = englishVoices[0];

      utterance.onend = () => {
        playNextChunk();
      };
      utterance.onerror = (e) => {
        console.error("SpeechSynthesisUtterance error:", e);
        playNextChunk();
      };
      synth.speak(utterance);
    };

    if (synth.getVoices().length === 0) {
      synth.onvoiceschanged = () => playNextChunk();
    } else {
      playNextChunk();
    }
  }, [synth, stop]);

  return { speak, stop, isSpeaking };
}
