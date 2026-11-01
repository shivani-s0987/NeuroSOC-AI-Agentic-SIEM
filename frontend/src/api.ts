import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

export interface Paginated<T> {
  items: T[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
  };
}

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

export interface InvestigationFinding {
  title: string;
  description: string;
  evidence_references: string[];
  confidence: number;
  observed_fact: boolean;
}

export interface Investigation {
  id: number;
  alert_id: number;
  case_id?: number;
  status: string;
  provider: string;
  model?: string;
  started_at: string;
  completed_at?: string;
  error_category?: string;
  version: number;
  fallback: boolean;
  evidence_references: string[];
  result?: {
    executive_summary: string;
    alert_severity: string;
    detection_rule?: string;
    event_count: number;
    affected_assets: string[];
    affected_users: string[];
    findings: InvestigationFinding[];
    timeline: Array<{ timestamp?: string; reference_id?: string; event_type?: string; source?: string }>;
    risk_assessment: { potential_impact: string; severity_assessment: string; confidence: number; uncertainty: string; missing_evidence: string[] };
    recommended_investigation_steps: string[];
    suggested_actions: string[];
    actions_already_performed: string[];
    actions_requiring_approval: string[];
    limitations: string[];
  };
}
