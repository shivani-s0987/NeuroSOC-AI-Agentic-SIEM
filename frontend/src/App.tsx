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
import { api, AlertRecord, CaseRecord, DetectionRecord, EventRecord, Summary } from "./api";
import { getAccessToken, login, logout, register } from "./auth";

ChartJS.register(ArcElement, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend);

const menu = [
  { name: "Overview", path: "/" },
  { name: "Events", path: "/events" },
  { name: "Alerts", path: "/alerts" },
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
