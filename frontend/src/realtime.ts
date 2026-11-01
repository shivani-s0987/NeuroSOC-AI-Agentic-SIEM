import { api } from "./api";
import { getAccessToken } from "./auth";

export type RealtimeStatus = "connecting" | "connected" | "disconnected";
export type RealtimeNotification = {
  event_id: string;
  event_type: string;
  schema_version: number;
  timestamp: string;
  resource: { type: string; id: string };
  data: Record<string, unknown>;
};

let socket: WebSocket | null = null;
let reconnectTimer: number | undefined;
let pollTimer: number | undefined;
let cursor = "";
let reconnectCount = 0;

function status(value: RealtimeStatus) {
  window.dispatchEvent(new CustomEvent("neurosoc:connection", { detail: value }));
}

export function startRealtime(onNotification: (notification: RealtimeNotification) => void) {
  stopRealtime();
  const token = getAccessToken();
  if (!token) return () => undefined;

  const reconnect = () => {
    window.clearTimeout(reconnectTimer);
    reconnectTimer = window.setTimeout(() => connect(), Math.min(30000, 1000 * 2 ** reconnectCount++) + Math.random() * 500);
  };

  const reconcile = async () => {
    try {
      const query = cursor ? `?after=${encodeURIComponent(cursor)}` : "";
      const { data } = await api.get<RealtimeNotification[]>(`/realtime/notifications${query}`);
      for (const notification of data) {
        if (notification.event_id) onNotification(notification);
      }
      if (data.length) cursor = data[data.length - 1].timestamp;
    } catch {
      // The next reconciliation interval is an authorized API refresh fallback.
    }
  };

  const connect = () => {
    status("connecting");
    if (typeof WebSocket === "undefined") {
      status("disconnected");
      return;
    }
    const apiBase = api.defaults?.baseURL || window.location.origin;
    const wsBase = apiBase.replace(/^http/, "ws");
    socket = new WebSocket(`${wsBase}/realtime/ws`);
    socket.onopen = () => socket?.send(JSON.stringify({ type: "auth", token }));
    socket.onmessage = (message) => {
      try {
        const payload = JSON.parse(message.data);
        if (payload.type === "connected") {
          status("connected");
          reconnectCount = 0;
          void reconcile();
        } else if (payload.event_id) {
          onNotification(payload as RealtimeNotification);
        }
      } catch {
        // Ignore malformed server frames; notifications are reconciled by API.
      }
    };
    socket.onclose = () => {
      status("disconnected");
      reconnect();
    };
  };

  connect();
  pollTimer = window.setInterval(() => void reconcile(), 5000);
  return stopRealtime;
}

export function stopRealtime() {
  window.clearTimeout(reconnectTimer);
  window.clearInterval(pollTimer);
  socket?.close();
  socket = null;
}
