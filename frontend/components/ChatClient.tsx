"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type Entity = {
  name: string;
  value: string;
  confidence?: number;
};

type Result = {
  interaction_id: string;
  text: string;
  entities: Entity[];
  status: "pending" | "awaiting_confirmation" | "confirmed";
};

type ServerMessage =
  | { type: "ready" }
  | { type: "result"; result: Result }
  | { type: "prompt_confirmation"; interaction_id: string; prompt: string }
  | { type: "retry"; interaction_id: string }
  | { type: "state"; results: Result[] };

const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8000/ws";

export function ChatClient() {
  const [connected, setConnected] = useState(false);
  const [results, setResults] = useState<Record<string, Result>>({});
  const [confirmPrompt, setConfirmPrompt] = useState<string | null>(null);
  const [confirmInteractionId, setConfirmInteractionId] = useState<string | null>(null);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);
  const [inputText, setInputText] = useState("This is a demo utterance");
  const [log, setLog] = useState<string[]>([]);
  const [isRecording, setIsRecording] = useState(false);

  const socketRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  useEffect(() => {
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      setConnected(true);
      pushLog("Connected to backend");
    };

    socket.onerror = (error) => {
      console.error("WebSocket error observed:", error);
      pushLog(`WebSocket error. State: ${socket.readyState}`);
    };

    socket.onclose = (event) => {
      setConnected(false);
      pushLog(`Disconnected: ${event.code} ${event.reason}`);
    };

    socket.onmessage = (event) => {
      const msg: ServerMessage = JSON.parse(event.data);
      handleServerMessage(msg);
    };

    return () => {
      if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
        socket.close();
      }
      stopRecording();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0 && socketRef.current?.readyState === WebSocket.OPEN) {
          // Send raw bytes
          const arrayBuffer = await event.data.arrayBuffer();
          socketRef.current.send(arrayBuffer);
        }
      };

      mediaRecorder.start(100); // Send chunks every 100ms
      setIsRecording(true);
      pushLog("Started recording");
    } catch (err) {
      console.error("Error accessing microphone:", err);
      pushLog("Error accessing microphone");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
      setIsRecording(false);
      pushLog("Stopped recording");
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleServerMessage = (msg: ServerMessage) => {
    switch (msg.type) {
      case "ready":
        pushLog("Backend ready");
        break;
      case "result":
        setResults((prev) => ({ ...prev, [msg.result.interaction_id]: msg.result }));
        break;
      case "prompt_confirmation":
        setConfirmPrompt(msg.prompt);
        setConfirmInteractionId(msg.interaction_id);
        setAwaitingConfirmation(true);
        break;
      case "retry":
        setConfirmPrompt(null);
        setConfirmInteractionId(null);
        setAwaitingConfirmation(false);
        pushLog(`Retry interaction ${msg.interaction_id}`);
        break;
      case "state":
        setResults((prev) => ({ ...prev, ...toRecord(msg.results) }));
        break;
      default:
        break;
    }
  };

  const sendJson = (payload: object) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      pushLog("Socket not connected");
      return;
    }
    socketRef.current.send(JSON.stringify(payload));
  };

  const handleTranscript = (text: string) => {
    const classification = classifyConfirmation(text);

    if (awaitingConfirmation && confirmInteractionId) {
      if (classification === "yes") {
        sendConfirm(true);
        pushLog(`Auto-confirmed ${confirmInteractionId}`);
        return;
      }
      if (classification === "no") {
        sendConfirm(false);
        pushLog(`Auto-declined ${confirmInteractionId}`);
        return;
      }
      // Treat as a fresh interaction if not a confirmation keyword
      pushLog("Not a yes/no, treating as new interaction");
      clearConfirmation();
    }

    sendJson({
      type: "stt_result",
      text,
      entities: [],
    });
    pushLog(`Sent STT text: ${text}`);
  };

  const handleSendStt = () => {
    handleTranscript(inputText);
  };

  const sendConfirm = (confirmed: boolean) => {
    if (!confirmInteractionId) return;
    sendJson({ type: "confirm", interaction_id: confirmInteractionId, confirmed });
    clearConfirmation();
  };

  const clearConfirmation = () => {
    setConfirmPrompt(null);
    setConfirmInteractionId(null);
    setAwaitingConfirmation(false);
  };

  const pushLog = (entry: string) => {
    setLog((prev) => [entry, ...prev].slice(0, 30));
  };

  const resultList = useMemo(() => Object.values(results), [results]);

  return (
    <div style={{ maxWidth: 960, margin: "0 auto", padding: "24px" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>Voice Agent</div>
          <div style={{ fontSize: 14, color: "#94a3b8" }}>Entity capture with confirmation</div>
        </div>
        <div
          style={{
            padding: "6px 10px",
            borderRadius: 12,
            background: connected ? "#10b981" : "#f43f5e",
            color: "#0f172a",
            fontWeight: 700,
          }}
        >
          {connected ? "Connected" : "Disconnected"}
        </div>
      </header>

      <section style={{ marginTop: 16, padding: 16, background: "#1e293b", borderRadius: 12 }}>
        <div style={{ fontWeight: 700, marginBottom: 8 }}>Voice Input</div>
        <button
          onClick={toggleRecording}
          style={{
            padding: "12px 20px",
            borderRadius: 8,
            background: isRecording ? "#ef4444" : "#3b82f6",
            color: "#ffffff",
            border: "none",
            fontWeight: 700,
            fontSize: 16,
            width: "100%",
            marginBottom: 16,
          }}
        >
          {isRecording ? "Stop Recording" : "Start Recording"}
        </button>

        <div style={{ fontWeight: 700, marginBottom: 8 }}>Simulate STT payload</div>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Say something..."
          style={{ width: "100%", minHeight: 80, padding: 12, borderRadius: 8, border: "1px solid #334155", background: "#0f172a", color: "#e2e8f0" }}
        />
        <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
          <button
            onClick={handleSendStt}
            style={{ padding: "10px 14px", borderRadius: 8, background: "#38bdf8", color: "#0f172a", border: "none", fontWeight: 700 }}
          >
            Send STT result
          </button>
          <button
            onClick={() => {
              setInputText("This is a demo utterance");
              handleSendStt();
            }}
            style={{ padding: "10px 14px", borderRadius: 8, background: "#22c55e", color: "#0f172a", border: "none", fontWeight: 700 }}
          >
            Send demo
          </button>
          <button
            onClick={() => sendJson({ type: "request_state" })}
            style={{ padding: "10px 14px", borderRadius: 8, background: "#c084fc", color: "#0f172a", border: "none", fontWeight: 700 }}
          >
            Sync state
          </button>
        </div>
      </section>

      {confirmPrompt && (
        <section style={{ marginTop: 16, padding: 16, background: "#0f172a", borderRadius: 12, border: "1px solid #334155" }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>{confirmPrompt}</div>
          <div style={{ color: "#94a3b8", marginBottom: 8, fontSize: 14 }}>
            Say "yes" / "no" (or provide a new answer to replace).
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={() => sendConfirm(true)}
              style={{ padding: "10px 14px", borderRadius: 8, background: "#22c55e", color: "#0f172a", border: "none", fontWeight: 700 }}
            >
              Yes
            </button>
            <button
              onClick={() => sendConfirm(false)}
              style={{ padding: "10px 14px", borderRadius: 8, background: "#f97316", color: "#0f172a", border: "none", fontWeight: 700 }}
            >
              No, retry
            </button>
          </div>
        </section>
      )}

      <section style={{ marginTop: 16, padding: 16, background: "#0f172a", borderRadius: 12, border: "1px solid #334155" }}>
        <div style={{ fontWeight: 700, marginBottom: 8 }}>Results</div>
        {resultList.length === 0 && <div style={{ color: "#94a3b8" }}>No results yet.</div>}
        {resultList.map((r) => (
          <div key={r.interaction_id} style={{ marginBottom: 10, padding: 12, borderRadius: 8, background: "#1e293b" }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <div style={{ fontWeight: 700 }}>{r.interaction_id}</div>
              <span style={{ color: statusColor(r.status), fontWeight: 700 }}>{r.status}</span>
            </div>
            <div style={{ marginTop: 4 }}>{r.text}</div>
            <div style={{ marginTop: 6, color: "#94a3b8", fontSize: 14 }}>
              Entities: {r.entities.map((e) => `${e.name}=${e.value}`).join(", ") || "none"}
            </div>
          </div>
        ))}
      </section>

      <section style={{ marginTop: 16, padding: 16, background: "#0f172a", borderRadius: 12, border: "1px solid #334155" }}>
        <div style={{ fontWeight: 700, marginBottom: 8 }}>Log</div>
        <div style={{ maxHeight: 200, overflowY: "auto", display: "grid", gap: 6 }}>
          {log.map((l, idx) => (
            <div key={idx} style={{ color: "#94a3b8" }}>
              {l}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function statusColor(status: Result["status"]) {
  if (status === "confirmed") return "#22c55e";
  if (status === "awaiting_confirmation") return "#f59e0b";
  return "#94a3b8";
}

function toRecord(list: Result[]) {
  return list.reduce<Record<string, Result>>((acc, item) => {
    acc[item.interaction_id] = item;
    return acc;
  }, {});
}

const YES_TERMS = ["yes", "yeah", "yep", "correct", "confirm", "looks good", "that is right", "that's right", "right", "sure"];
const NO_TERMS = ["no", "nope", "wrong", "try again", "not correct", "redo", "retry"];

function classifyConfirmation(text: string): "yes" | "no" | "other" {
  const normalized = normalize(text);
  if (!normalized) return "other";
  if (YES_TERMS.some((t) => normalized === t)) return "yes";
  if (NO_TERMS.some((t) => normalized === t)) return "no";
  return "other";
}

function normalize(text: string) {
  return text.trim().toLowerCase().replace(/[.!?\s]+$/g, "");
}
