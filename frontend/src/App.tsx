import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { Bar, Doughnut, Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend,
} from "chart.js";
import { api, AlertRecord, CaseRecord, DetectionRecord, EventRecord, Investigation, Summary } from "./api";
import { getAccessToken, login, logout, register } from "./auth";

ChartJS.register(ArcElement, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend);

const menu = [
  { name: "Overview", path: "/" },
  { name: "Events", path: "/events" },
  { name: "Alerts", path: "/alerts" },
  { name: "Investigations", path: "/investigations" },
  { name: "Detections", path: "/detections" },
  { name: "Threat Intelligence", path: "/intel" },
  { name: "Cases", path: "/cases" },
  { name: "Search", path: "/search" },
  { name: "Rules", path: "/rules" },
  { name: "Users", path: "/users" },
  { name: "Settings", path: "/settings" },
  { name: "Reports", path: "/reports" },
  { name: "Analytics", path: "/analytics" },
];

const overviewStats = [
  { label: "Events", key: "events" },
  { label: "Alerts", key: "alerts" },
  { label: "Cases", key: "cases" },
  { label: "MITRE", key: "mitre" },
] as const;

function HomePage() {
  const [summary, setSummary] = useState<Summary>();
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<Summary>("/analytics/summary").then(({ data }) => setSummary(data)).catch(() => setError("Unable to load dashboard data."));
  }, []);

  if (error) return <p role="alert" className="text-red-400">{error}</p>;
  if (!summary) return <p className="text-slate-400">Loading dashboard...</p>;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        {overviewStats.map((stat) => (
          <div key={stat.label} className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
            <p className="text-sm text-slate-400">{stat.label}</p>
            <p className="mt-2 text-3xl font-semibold text-white">{summary[stat.key]}</p>
          </div>
        ))}
      </div>
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6">
        <h2 className="text-lg font-semibold">Operational totals</h2>
        <p className="mt-2 text-slate-400">{summary.alerts} alerts, including {summary.high_severity} high-severity alerts, and {summary.detections} detections.</p>
      </div>
    </div>
  );
}

function ResourcePage({ title, endpoint }: { title: string; endpoint: string }) {
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<Record<string, unknown>[] | { items: Record<string, unknown>[] }>(endpoint).then(({ data }) => setRows(Array.isArray(data) ? data : data.items)).catch(() => setError(`Unable to load ${title.toLowerCase()}.`));
  }, [endpoint, title]);

  return (
    <section>
      <h1 className="mb-4 text-2xl font-semibold">{title}</h1>
      {error && <p role="alert" className="text-red-400">{error}</p>}
      {!error && rows.length === 0 && <p className="text-slate-400">No records or data is loading.</p>}
      <div className="space-y-3">
        {rows.map((row, index) => (
          <article key={String(row.id ?? index)} className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
            <p className="font-medium">{String(row.name ?? row.title ?? row.message ?? `Record ${index + 1}`)}</p>
            <p className="mt-1 text-sm text-slate-400">{String(row.severity ?? row.status ?? row.event_type ?? row.priority ?? row.source ?? "")}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-8">
      <h1 className="text-2xl font-semibold">{title}</h1>
      <p className="mt-3 text-slate-400">This workspace includes a complete backend and UI shell for the {title.toLowerCase()} experience.</p>
    </div>
  );
}

function InvestigationsPage() {
  const [alertId, setAlertId] = useState("");
  const [investigation, setInvestigation] = useState<Investigation>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState("");

  async function start() {
    if (!alertId) return;
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post<Investigation>("/assistant/alerts/" + alertId + "/investigate", {});
      setInvestigation(data);
    } catch {
      setError("Unable to start this investigation. Verify that the alert exists and you have analyst access.");
    } finally {
      setLoading(false);
    }
  }

  async function retry() {
    if (!investigation) return;
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post<Investigation>(`/assistant/investigations/${investigation.id}/retry`);
      setInvestigation(data);
    } catch {
      setError("Retry failed. The investigation remains available in its history.");
    } finally {
      setLoading(false);
    }
  }

  async function submitFeedback(category: string) {
    if (!investigation) return;
    await api.post(`/assistant/investigations/${investigation.id}/feedback`, { category, comments: feedback || null });
    setFeedback("");
  }

  const result = investigation?.result;
  return (
    <section>
      <h1 className="mb-4 text-2xl font-semibold">AI Investigations</h1>
      <div className="mb-6 flex gap-3">
        <input aria-label="Alert ID" type="number" value={alertId} onChange={(event) => setAlertId(event.target.value)} className="w-40 rounded border border-slate-700 bg-slate-900 p-2" />
        <button onClick={start} disabled={loading} className="rounded bg-cyan-700 px-4 py-2 disabled:opacity-50">{loading ? "Investigating..." : "Investigate alert"}</button>
        {investigation?.status === "FAILED" && <button onClick={retry} className="rounded border border-cyan-700 px-4 py-2">Retry</button>}
      </div>
      {error && <p role="alert" className="text-red-400">{error}</p>}
      {!investigation && !loading && <p className="text-slate-400">Enter an alert ID to retrieve and assess real database evidence.</p>}
      {investigation && (
        <div className="space-y-5">
          <article className="rounded-lg border border-slate-800 bg-slate-900/80 p-5">
            <div className="flex flex-wrap justify-between gap-2">
              <h2 className="text-lg font-semibold">Alert {investigation.alert_id}</h2>
              <span>{investigation.status}</span>
            </div>
            <p className="mt-2 text-sm text-slate-400">Provider: {investigation.provider}{investigation.model ? ` / ${investigation.model}` : ""}{investigation.fallback ? " (deterministic fallback)" : ""}</p>
            {investigation.error_category && <p className="mt-2 text-red-300">Provider error: {investigation.error_category}</p>}
          </article>
          {result && (
            <>
              <article className="rounded-lg border border-slate-800 bg-slate-900/80 p-5">
                <h2 className="font-semibold">Executive summary</h2>
                <p className="mt-2 text-slate-300">{result.executive_summary}</p>
                <p className="mt-3 text-sm text-slate-400">{result.event_count} events; severity {result.alert_severity}</p>
              </article>
              <article className="rounded-lg border border-slate-800 bg-slate-900/80 p-5">
                <h2 className="font-semibold">Findings</h2>
                <div className="mt-3 space-y-3">
                  {result.findings.map((finding, index) => (
                    <div key={index} className="rounded border border-slate-700 p-3">
                      <p className="font-medium">{finding.title}</p>
                      <p className="text-sm text-slate-300">{finding.description}</p>
                      <p className="mt-2 text-xs text-slate-400">{finding.observed_fact ? "Observed fact" : "Analytical hypothesis"} · confidence {Math.round(finding.confidence * 100)}%</p>
                      {finding.evidence_references.map((reference) => <code key={reference} className="mr-2 text-xs text-cyan-300">{reference}</code>)}
                    </div>
                  ))}
                </div>
              </article>
              <article className="rounded-lg border border-slate-800 bg-slate-900/80 p-5">
                <h2 className="font-semibold">Timeline</h2>
                {result.timeline.length === 0 ? <p className="mt-2 text-slate-400">No timeline events available.</p> : result.timeline.map((event, index) => (
                  <p key={index} className="mt-2 text-sm text-slate-300">{event.timestamp || "Unknown timestamp"} · {event.reference_id} · {event.event_type || "event"}</p>
                ))}
              </article>
              <article className="rounded-lg border border-slate-800 bg-slate-900/80 p-5">
                <h2 className="font-semibold">Recommended analyst actions</h2>
                <p className="text-xs text-amber-300">Advisory only; analyst approval is required for containment actions.</p>
                <ol className="mt-3 list-decimal space-y-1 pl-5">{result.recommended_investigation_steps.map((step, index) => <li key={index}>{step}</li>)}</ol>
              </article>
              {investigation.status === "COMPLETED" && (
                <article className="rounded-lg border border-slate-800 bg-slate-900/80 p-5">
                  <h2 className="font-semibold">Analyst feedback</h2>
                  <textarea aria-label="Feedback comments" value={feedback} onChange={(event) => setFeedback(event.target.value)} className="mt-3 min-h-20 w-full rounded border border-slate-700 bg-slate-950 p-3" />
                  <div className="mt-3 flex flex-wrap gap-2">
                    {["helpful", "not_helpful", "finding_confirmed", "finding_incorrect", "false_positive", "needs_further_investigation"].map((category) => (
                      <button key={category} onClick={() => submitFeedback(category)} className="rounded border border-slate-700 px-3 py-2 text-sm">{category.replace(/_/g, " ")}</button>
                    ))}
                  </div>
                </article>
              )}
            </>
          )}
        </div>
      )}
    </section>
  );
}

function AuthPage({ onAuthenticated }: { onAuthenticated: () => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      if (mode === "login") {
        await login(username, password);
        onAuthenticated();
      } else {
        await register(username, email, password);
        setMode("login");
      }
    } catch {
      setError("Authentication request failed. Check your credentials and try again.");
    }
  }

  return <main className="mx-auto max-w-md p-8"><h1 className="text-2xl font-semibold">{mode === "login" ? "Sign in" : "Register"}</h1><form onSubmit={submit} className="mt-6 space-y-3"><input aria-label="Username" value={username} onChange={(e) => setUsername(e.target.value)} className="w-full rounded border border-slate-700 bg-slate-900 p-3" /><input aria-label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded border border-slate-700 bg-slate-900 p-3" />{mode === "register" && <input aria-label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded border border-slate-700 bg-slate-900 p-3" />}<button className="rounded bg-cyan-700 px-4 py-2">Continue</button><button type="button" onClick={() => setMode(mode === "login" ? "register" : "login")} className="ml-3 text-cyan-300">{mode === "login" ? "Create account" : "Sign in instead"}</button>{error && <p role="alert" className="text-red-400">{error}</p>}</form></main>;
}

export default function App() {
  const [, forceRender] = useState(0);
  if (!getAccessToken()) return <AuthPage onAuthenticated={() => forceRender((value) => value + 1)} />;
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <aside className="w-full border-b border-slate-800 bg-slate-950/70 p-4 lg:w-72 lg:border-b-0 lg:border-r">
          <div className="mb-6">
            <p className="text-sm uppercase tracking-[0.3em] text-cyan-400">NeuroSOC</p>
            <h1 className="text-2xl font-semibold">AI-Assisted SOC</h1>
          </div>
          <button type="button" onClick={() => { logout(); forceRender((value) => value + 1); }} className="mb-4 text-sm text-cyan-300">Sign out</button>
          <nav className="space-y-2">
            {menu.map((item) => (
              <Link key={item.path} to={item.path} className="block rounded-lg px-3 py-2 text-sm text-slate-300 transition hover:bg-slate-800">
                {item.name}
              </Link>
            ))}
          </nav>
        </aside>
        <main className="flex-1 p-6">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/events" element={<ResourcePage title="Events" endpoint="/events" />} />
            <Route path="/alerts" element={<ResourcePage title="Alerts" endpoint="/alerts" />} />
            <Route path="/investigations" element={<InvestigationsPage />} />
            <Route path="/detections" element={<ResourcePage title="Detections" endpoint="/detections" />} />
            <Route path="/intel" element={<PlaceholderPage title="Threat Intelligence" />} />
            <Route path="/cases" element={<ResourcePage title="Cases" endpoint="/cases" />} />
            <Route path="/search" element={<PlaceholderPage title="Search" />} />
            <Route path="/rules" element={<PlaceholderPage title="Rules" />} />
            <Route path="/users" element={<PlaceholderPage title="Users" />} />
            <Route path="/settings" element={<PlaceholderPage title="Settings" />} />
            <Route path="/reports" element={<PlaceholderPage title="Reports" />} />
            <Route path="/analytics" element={<PlaceholderPage title="Analytics" />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
