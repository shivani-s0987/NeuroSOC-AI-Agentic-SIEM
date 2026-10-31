import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

export interface Summary {
  events: number;
  alerts: number;
  cases: number;
  detections: number;
  mitre: number;
  high_severity: number;
}

export interface EventRecord {
  id: number;
  timestamp: string;
  source: string;
  event_type: string;
  severity: string;
  host?: string;
  user?: string;
  src_ip?: string;
  message: string;
}

export interface AlertRecord {
  id: number;
  title: string;
  severity: string;
  status: string;
  source: string;
  summary?: string;
  created_at: string;
}

export interface DetectionRecord {
  id: number;
  name: string;
  severity: string;
  rule_id?: string;
  description?: string;
  mitre: Array<{ technique_id: string; name: string }>;
}

export interface CaseRecord {
  id: number;
  title: string;
  status: string;
  priority: string;
  assigned_to?: string;
  summary?: string;
  created_at: string;
}
