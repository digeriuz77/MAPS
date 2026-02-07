"use client";

import { useState, useRef, useEffect } from "react";
import { blobToBase64 } from "@/lib/voice/mistral-client";

interface AudioRecorderProps {
  onTranscript: (text: string) => void;
  onError?: (error: string) => void;
  language?: string;
}

export function AudioRecorder({ onTranscript, onError, language }: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm",
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());

        // Process the audio
        setIsProcessing(true);
        try {
          const base64 = await blobToBase64(blob);

          const response = await fetch("/api/voice/transcribe", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              audio: base64,
              language,
            }),
          });

          if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || "Transcription failed");
          }

          const result = await response.json();
          onTranscript(result.text);
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : "Failed to transcribe audio";
          onError?.(errorMessage);
        } finally {
          setIsProcessing(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to access microphone";
      onError?.(errorMessage);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);

      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex items-center gap-3">
      {/* Recording Time */}
      {(isRecording || isProcessing) && (
        <div className="text-sm text-gray-600">
          {isRecording ? (
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
              {formatTime(recordingTime)}
            </span>
          ) : (
            <span>Processing...</span>
          )}
        </div>
      )}

      {/* Record Button */}
      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isProcessing}
        className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
          isRecording
            ? "bg-red-500 hover:bg-red-600 text-white"
            : "bg-maps-teal hover:bg-maps-teal-dark text-white"
        } ${isProcessing ? "opacity-50 cursor-not-allowed" : ""}`}
        title={isRecording ? "Stop recording" : "Start recording"}
      >
        {isRecording ? (
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <rect x="6" y="6" width="8" height="8" />
          </svg>
        ) : (
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path d="M7 4a3 3 0 016 0v6a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8H3a7 7 0 008 6.93V17h6v-2.07z" />
          </svg>
        )}
      </button>
    </div>
  );
}
