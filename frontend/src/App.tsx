import { FormEvent, ReactNode, useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { api, Investigation, Paginated } from "./api";
import { getAccessToken, login, logout, register, setAccessToken } from "./auth";
import { startRealtime } from "./realtime";

type User = { id: number; username: string; email: string; role: string; disabled: number };
const nav = [
  ["Overview", "Security Overview", "/"],
  ["Detection & Monitoring", "Events Explorer", "/events"],
  ["Detection & Monitoring", "Alert Center", "/alerts"],
  ["Detection & Monitoring", "Detection Engine", "/detections"],
  ["Detection & Monitoring", "Threat Intelligence", "/threat-intelligence"],
  ["Investigation", "Cases", "/cases"],
  ["Investigation", "AI Investigation", "/investigations"],
  ["Investigation", "Log Search", "/search"],
  ["Investigation", "MITRE ATT&CK", "/mitre"],
  ["Administration", "User Management", "/users", "ADMIN"],
  ["Administration", "Audit Logs", "/audit", "ADMIN"],
  ["Administration", "Reports", "/reports"],
  ["Administration", "Settings", "/settings", "ADMIN"],
] as const;

function Header({ title, description }: { title: string; description: string }) {
  return <header className="mb-6"><h1 className="text-2xl font-semibold">{title}</h1><p className="mt-1 text-sm text-slate-400">{description}</p></header>;
}

function State({ loading, error, empty, children }: { loading?: boolean; error?: string; empty?: boolean; children?: ReactNode }) {
  if (loading) return <div role="status" className="rounded-xl border border-slate-800 bg-slate-900 p-6 text-slate-400">Loading…</div>;
  if (error) return <div role="alert" className="rounded-xl border border-red-900 bg-red-950/30 p-6 text-red-300">{error}</div>;
  if (empty) return <div className="rounded-xl border border-slate-800 bg-slate-900 p-8 text-center text-slate-400">No records match this view.</div>;
  return <>{children}</>;
}

function Severity({ value }: { value?: unknown }) {
  const v = String(value || "unknown").toLowerCase();
  const colors = v === "critical" || v === "high" ? "border-red-800 bg-red-950 text-red-300" : v === "medium" ? "border-amber-800 bg-amber-950 text-amber-300" : "border-slate-700 bg-slate-800 text-slate-300";
  return <span className={`rounded-full border px-2 py-0.5 text-xs ${colors}`}>{v}</span>;
}

async function list<T>(endpoint: string, params: Record<string, unknown> = {}) {
  const response = await api.get<Paginated<T> | T[]>(endpoint, { params });
  return Array.isArray(response.data) ? response.data : response.data.items;
}

function Overview() {
  const [summary, setSummary] = useState<Record<string, number>>();
  const [error, setError] = useState("");
  useEffect(() => { api.get<Record<string, number>>("/analytics/summary").then(({ data }) => setSummary(data)).catch(() => setError("Unable to load security overview.")); }, []);
  const cards = [["events", "Total events", "/events"], ["alerts", "Total alerts", "/alerts"], ["high_severity", "High-severity alerts", "/alerts?severity=high"], ["cases", "Cases", "/cases"], ["detections", "Detection records", "/detections"], ["mitre", "MITRE techniques", "/mitre"]] as const;
  return <><Header title="Security Overview" description="Current database totals with live backend data." /><State loading={!summary && !error} error={error || undefined}><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{cards.map(([key, label, path]) => <Link key={key} to={path} className="rounded-xl border border-slate-800 bg-slate-900 p-5 hover:border-cyan-800"><p className="text-sm text-slate-400">{label}</p><p className="mt-2 text-3xl font-semibold">{summary?.[key] ?? 0}</p></Link>)}</div><div className="mt-6 rounded-xl border border-slate-800 bg-slate-900 p-5 text-sm text-slate-400">The backend provides aggregate totals only. Trend, source-IP, and alert-status charts are unavailable and are not simulated.</div></State></>;
}

function Events() {
  const [rows, setRows] = useState<Record<string, unknown>[]>();
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("");
  const [selected, setSelected] = useState<Record<string, unknown>>();
  useEffect(() => { setRows(undefined); api.get<Paginated<Record<string, unknown>>>("/events", { params: { page: 1, page_size: 50, message: query || undefined, severity: severity || undefined } }).then(({ data }) => setRows(data.items)).catch(() => setError("Unable to load events.")); }, [query, severity]);
  return <><Header title="Events Explorer" description="Paginated event data from the events API." /><div className="mb-4 grid gap-3 md:grid-cols-[1fr_180px]"><input aria-label="Search event message" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search event message" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" /><select aria-label="Severity filter" value={severity} onChange={(e) => setSeverity(e.target.value)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"><option value="">All severities</option>{["info", "low", "medium", "high", "critical"].map((v) => <option key={v}>{v}</option>)}</select></div><State loading={!rows && !error} error={error || undefined} empty={rows?.length === 0}><div className="overflow-x-auto rounded-xl border border-slate-800"><table className="w-full min-w-[760px] text-left text-sm"><thead className="bg-slate-900 text-slate-400"><tr>{["ID", "Time", "Type", "Severity", "Source IP", "Host", "User"].map((h) => <th key={h} className="px-4 py-3">{h}</th>)}</tr></thead><tbody>{rows?.map((row) => <tr key={String(row.id)} onClick={() => setSelected(row)} className="cursor-pointer border-t border-slate-800 hover:bg-slate-900"><td className="px-4 py-3 font-mono">{String(row.id)}</td><td className="px-4 py-3 text-slate-400">{String(row.timestamp || "")}</td><td className="px-4 py-3">{String(row.event_type || "")}</td><td className="px-4 py-3"><Severity value={row.severity} /></td><td className="px-4 py-3 font-mono">{String(row.src_ip || "—")}</td><td className="px-4 py-3">{String(row.host || "—")}</td><td className="px-4 py-3">{String(row.user || "—")}</td></tr>)}</tbody></table></div></State>{selected && <aside className="fixed inset-y-0 right-0 z-20 w-full max-w-xl overflow-auto border-l border-slate-700 bg-slate-950 p-6" aria-label="Event details"><button onClick={() => setSelected(undefined)} className="rounded border border-slate-700 px-3 py-1">Close</button><h2 className="mt-5 text-xl font-semibold">Event {String(selected.id)}</h2><dl className="mt-5 space-y-4 text-sm">{Object.entries(selected).map(([key, value]) => <div key={key}><dt className="text-slate-500">{key}</dt><dd className="mt-1 break-all font-mono text-slate-200">{typeof value === "object" ? JSON.stringify(value, null, 2) : String(value ?? "—")}</dd></div>)}</dl></aside>}</>;
}

function Alerts() {
  const [rows, setRows] = useState<Record<string, unknown>[]>();
  const [error, setError] = useState("");
  const [severity, setSeverity] = useState("");
  const [selected, setSelected] = useState<Record<string, unknown>>();
  const [notice, setNotice] = useState("");
  useEffect(() => { setRows(undefined); api.get<Paginated<Record<string, unknown>>>("/alerts", { params: { page: 1, page_size: 50, severity: severity || undefined } }).then(({ data }) => setRows(data.items)).catch(() => setError("Unable to load alerts.")); }, [severity]);
  async function investigate(id: number) { setNotice(""); try { const { data } = await api.post<Investigation>(`/assistant/alerts/${id}/investigate`, {}); setNotice(`Investigation ${data.id}: ${data.status}`); } catch { setNotice("Unable to start investigation."); } }
  return <><Header title="Alert Center" description="Alert records from detection output." /><div className="mb-4 flex items-center gap-3"><select aria-label="Alert severity" value={severity} onChange={(e) => setSeverity(e.target.value)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"><option value="">All severities</option>{["low", "medium", "high", "critical"].map((v) => <option key={v}>{v}</option>)}</select>{notice && <span role="status" className="text-sm text-cyan-300">{notice}</span>}</div><State loading={!rows && !error} error={error || undefined} empty={rows?.length === 0}><div className="grid gap-3">{rows?.map((row) => <button key={String(row.id)} onClick={() => setSelected(row)} className="grid gap-3 rounded-xl border border-slate-800 bg-slate-900 p-4 text-left hover:border-cyan-800 md:grid-cols-[1fr_auto_auto]"><span><strong>{String(row.title)}</strong><small className="mt-1 block text-slate-400">Alert {String(row.id)} · {String(row.created_at || "")}</small></span><Severity value={row.severity} /><span className="text-sm text-slate-400">{String(row.status)}</span></button>)}</div></State>{selected && <aside className="fixed inset-y-0 right-0 z-20 w-full max-w-lg overflow-auto border-l border-slate-700 bg-slate-950 p-6" aria-label="Alert details"><button onClick={() => setSelected(undefined)} className="rounded border border-slate-700 px-3 py-1">Close</button><h2 className="mt-5 text-xl font-semibold">{String(selected.title)}</h2><div className="mt-3"><Severity value={selected.severity} /></div><p className="mt-5 text-slate-300">{String(selected.summary || "No summary is stored.")}</p><button onClick={() => investigate(Number(selected.id))} className="mt-6 rounded-lg bg-cyan-700 px-4 py-2">Start investigation</button></aside>}</>;
}

function Generic({ title, description, endpoint, fields }: { title: string; description: string; endpoint: string; fields: string[] }) {
  const [rows, setRows] = useState<Record<string, unknown>[]>();
  const [error, setError] = useState("");
  useEffect(() => { setRows(undefined); list<Record<string, unknown>>(endpoint).then(setRows).catch(() => setError(`Unable to load ${title.toLowerCase()}.`)); }, [endpoint, title]);
  return <><Header title={title} description={description} /><State loading={!rows && !error} error={error || undefined} empty={rows?.length === 0}><div className="space-y-3">{rows?.map((row, index) => <article key={String(row.id ?? row.rule_id ?? row.key ?? index)} className="rounded-xl border border-slate-800 bg-slate-900 p-4">{fields.map((field) => <div key={field} className="mb-1 text-sm"><span className="mr-2 text-slate-500">{field}:</span>{typeof row[field] === "object" ? JSON.stringify(row[field]) : String(row[field] ?? "—")}</div>)}</article>)}</div></State></>;
}

function Cases() {
  const [rows, setRows] = useState<Record<string, unknown>[]>();
  const [error, setError] = useState("");
  const [title, setTitle] = useState("");
  const reload = () => list<Record<string, unknown>>("/cases", { page: 1, page_size: 50 }).then(setRows).catch(() => setError("Unable to load cases."));
  useEffect(() => { reload(); }, []);
  async function create(event: FormEvent) { event.preventDefault(); try { await api.post("/cases", { title, priority: "medium" }); setTitle(""); await reload(); } catch { setError("Unable to create case."); } }
  return <><Header title="Cases" description="Incident cases managed by the backend cases API." /><form onSubmit={create} className="mb-5 flex gap-3"><input aria-label="Case title" required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Case title" className="max-w-md flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" /><button className="rounded-lg bg-cyan-700 px-4 py-2">Create case</button></form><State loading={!rows && !error} error={error || undefined} empty={rows?.length === 0}><div className="space-y-3">{rows?.map((row) => <article key={String(row.id)} className="rounded-xl border border-slate-800 bg-slate-900 p-4"><strong>{String(row.title)}</strong><p className="mt-1 text-sm text-slate-400">#{String(row.id)} · {String(row.status)} · {String(row.priority)}</p></article>)}</div></State></>;
}

function Investigations() {
  const [alertId, setAlertId] = useState("");
  const [investigation, setInvestigation] = useState<Investigation>();
  const [history, setHistory] = useState<Investigation[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  useEffect(() => { list<Investigation>("/assistant/investigations", { page: 1, page_size: 20 }).then(setHistory).catch(() => undefined); }, []);
  async function start() { setLoading(true); setError(""); try { const { data } = await api.post<Investigation>(`/assistant/alerts/${alertId}/investigate`, {}); setInvestigation(data); } catch { setError("Unable to start investigation."); } finally { setLoading(false); } }
  async function retry() { if (!investigation) return; try { const { data } = await api.post<Investigation>(`/assistant/investigations/${investigation.id}/retry`); setInvestigation(data); } catch { setError("Retry failed."); } }
  async function feedback(category: string) { if (investigation) await api.post(`/assistant/investigations/${investigation.id}/feedback`, { category }); }
  return <><Header title="AI Investigation" description="Evidence references, uncertainty, fallback state, and analyst feedback." /><div className="mb-5 flex gap-3"><input aria-label="Alert ID" type="number" value={alertId} onChange={(e) => setAlertId(e.target.value)} className="w-40 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" /><button disabled={!alertId || loading} onClick={start} className="rounded-lg bg-cyan-700 px-4 py-2 disabled:opacity-50">{loading ? "Working…" : "Investigate alert"}</button></div>{error && <p role="alert" className="mb-4 text-red-300">{error}</p>}{investigation && <article className="rounded-xl border border-slate-800 bg-slate-900 p-5"><div className="flex justify-between gap-3"><h2 className="font-semibold">Alert {investigation.alert_id} · {investigation.status}</h2>{investigation.fallback && <span className="rounded-full bg-amber-950 px-3 py-1 text-xs text-amber-300">Deterministic fallback</span>}</div><p className="mt-2 text-sm text-slate-400">{investigation.provider}{investigation.model ? ` · ${investigation.model}` : ""}</p>{investigation.status === "FAILED" && <button onClick={retry} className="mt-4 rounded border border-cyan-700 px-3 py-2">Retry</button>}{investigation.result && <><h3 className="mt-5 font-semibold">Executive summary</h3><p className="mt-2 text-slate-300">{investigation.result.executive_summary}</p>{investigation.result.findings.map((finding, index) => <div key={index} className="mt-3 rounded-lg border border-slate-700 p-3"><strong>{finding.title}</strong><p className="mt-1 text-sm text-slate-300">{finding.description}</p><p className="mt-2 text-xs text-slate-400">{finding.observed_fact ? "Observed fact" : "Hypothesis"} · {Math.round(finding.confidence * 100)}% confidence</p><p className="mt-1 font-mono text-xs text-cyan-300">{finding.evidence_references.join(" ")}</p></div>)}<div className="mt-5 flex gap-2"><button onClick={() => feedback("helpful")} className="rounded border border-slate-700 px-3 py-2 text-sm">Helpful</button><button onClick={() => feedback("not_helpful")} className="rounded border border-slate-700 px-3 py-2 text-sm">Not helpful</button></div></>}</article>}<details className="mt-6 rounded-xl border border-slate-800 bg-slate-900 p-4"><summary className="cursor-pointer">Investigation history ({history.length})</summary>{history.map((item) => <p key={item.id} className="mt-2 text-sm text-slate-300">#{item.id} · alert {item.alert_id} · {item.status} · v{item.version}</p>)}</details></>;
}

function Search() {
  const [query, setQuery] = useState("");
  const [rows, setRows] = useState<Array<{ id: string; message: string; severity: string }>>();
  const [error, setError] = useState("");
  async function submit(event: FormEvent) { event.preventDefault(); setError(""); try { const { data } = await api.get<Array<{ id: string; message: string; severity: string }>>("/search", { params: { query: query || undefined } }); setRows(data); } catch { setError("Search failed."); } }
  return <><Header title="Log Search" description="Substring search supported by the backend. No unimplemented query language is assumed." /><form onSubmit={submit} className="mb-5 flex gap-3"><input aria-label="Search query" value={query} onChange={(e) => setQuery(e.target.value)} className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" /><button className="rounded-lg bg-cyan-700 px-4 py-2">Search</button></form>{error && <p role="alert" className="text-red-300">{error}</p>}<State empty={rows?.length === 0}>{rows?.map((row) => <article key={row.id} className="mb-3 rounded-xl border border-slate-800 bg-slate-900 p-4"><span className="font-mono text-xs text-cyan-300">event:{row.id}</span><Severity value={row.severity} /><p className="mt-2 break-words text-sm">{row.message}</p></article>)}</State></>;
}

function Users() {
  const [rows, setRows] = useState<User[]>();
  const [error, setError] = useState("");
  const reload = () => api.get<Paginated<User>>("/admin/users", { params: { page: 1, page_size: 50 } }).then(({ data }) => setRows(data.items)).catch(() => setError("Unable to load users."));
  useEffect(() => { reload(); }, []);
  async function change(id: number, path: "role" | "status", value: string | boolean) { if (!confirm("Apply this account change?")) return; try { await api.patch(`/admin/users/${id}/${path}`, undefined, { params: path === "role" ? { role: value } : { disabled: value } }); await reload(); } catch { setError("Backend denied the account change."); } }
  return <><Header title="User Management" description="Administrator-only account operations." /><State loading={!rows && !error} error={error || undefined} empty={rows?.length === 0}><div className="space-y-3">{rows?.map((user) => <article key={user.id} className="grid gap-3 rounded-xl border border-slate-800 bg-slate-900 p-4 md:grid-cols-[1fr_auto_auto]"><div><strong>{user.username}</strong><p className="text-sm text-slate-400">{user.email} · {user.disabled ? "disabled" : "active"}</p></div><select aria-label={`Role for ${user.username}`} defaultValue={user.role} onChange={(e) => change(user.id, "role", e.target.value)} className="rounded border border-slate-700 bg-slate-950 px-2">{["SECURITY_VIEWER", "SOC_ANALYST", "ADMIN"].map((role) => <option key={role}>{role}</option>)}</select><button onClick={() => change(user.id, "status", !Boolean(user.disabled))} className="rounded border border-slate-700 px-3 py-2">{user.disabled ? "Activate" : "Deactivate"}</button></article>)}</div></State></>;
}

function Reports() {
  const [rows, setRows] = useState<Record<string, unknown>[]>();
  const [error, setError] = useState("");
  const reload = () => api.get<Paginated<Record<string, unknown>>>("/reports", { params: { page: 1, page_size: 50 } }).then(({ data }) => setRows(data.items)).catch(() => setError("Unable to load reports."));
  useEffect(() => { reload(); }, []);
  async function generate() { try { await api.post("/reports", { title: "SOC Investigation Report", report_type: "investigation", format: "markdown" }); await reload(); } catch { setError("Report generation failed."); } }
  return <><Header title="Reports" description="Report records generated by the backend." /><button onClick={generate} className="mb-5 rounded-lg bg-cyan-700 px-4 py-2">Generate report</button><State loading={!rows && !error} error={error || undefined} empty={rows?.length === 0}><div className="space-y-3">{rows?.map((row) => <article key={String(row.id)} className="rounded-xl border border-slate-800 bg-slate-900 p-4"><strong>{String(row.title)}</strong><p className="text-sm text-slate-400">{String(row.report_type)} · {String(row.created_at)}</p></article>)}</div></State></>;
}

function Settings() {
  const [rows, setRows] = useState<Array<{ key: string; value: string }>>();
  const [error, setError] = useState("");
  useEffect(() => { api.get<Array<{ key: string; value: string }>>("/settings").then(({ data }) => setRows(data)).catch(() => setError("Unable to load settings.")); }, []);
  return <><Header title="Settings" description="Administrative backend configuration. Secret values are not exposed by a public provider-status endpoint." /><State loading={!rows && !error} error={error || undefined} empty={rows?.length === 0}><div className="space-y-3">{rows?.map((row) => <div key={row.key} className="rounded-xl border border-slate-800 bg-slate-900 p-4"><span className="font-mono text-cyan-300">{row.key}</span><p className="mt-1 break-all text-sm text-slate-300">{row.value}</p></div>)}</div></State></>;
}

function Auth({ complete }: { complete: () => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState(""); const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [error, setError] = useState("");
  async function submit(event: FormEvent) { event.preventDefault(); setError(""); try { if (mode === "login") { await login(username, password); complete(); } else { await register(username, email, password); setMode("login"); } } catch { setError(mode === "login" ? "Sign-in failed." : "Registration failed."); } }
  return <main className="grid min-h-screen place-items-center px-4"><form onSubmit={submit} className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-8"><p className="text-xs uppercase tracking-[0.3em] text-cyan-400">NeuroSOC</p><h1 className="mt-2 text-2xl font-semibold">{mode === "login" ? "Sign in to SOC" : "Create account"}</h1><label className="mt-6 block text-sm">Username<input required value={username} onChange={(e) => setUsername(e.target.value)} className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" /></label>{mode === "register" && <label className="mt-4 block text-sm">Email<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" /></label>}<label className="mt-4 block text-sm">Password<input required type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" /></label>{error && <p role="alert" className="mt-4 text-red-300">{error}</p>}<button className="mt-6 w-full rounded-lg bg-cyan-700 py-2 font-semibold">{mode === "login" ? "Sign in" : "Register"}</button><button type="button" onClick={() => setMode(mode === "login" ? "register" : "login")} className="mt-4 text-sm text-cyan-300">{mode === "login" ? "Create account" : "Sign in instead"}</button></form></main>;
}

export default function App() {
  const [, refresh] = useState(0); const [user, setUser] = useState<User>(); const [collapsed, setCollapsed] = useState(false); const location = useLocation();
  const authenticated = Boolean(getAccessToken());
  const [realtimeStatus, setRealtimeStatus] = useState("disconnected");
  useEffect(() => { if (authenticated) api.get<User>("/auth/me").then(({ data }) => setUser(data)).catch(() => { logout(); refresh((v) => v + 1); }); }, [authenticated]);
  useEffect(() => {
    if (!authenticated) return;
    const connectionHandler = (event: Event) => setRealtimeStatus((event as CustomEvent<string>).detail);
    window.addEventListener("neurosoc:connection", connectionHandler);
    const stop = startRealtime((notification) => {
      window.dispatchEvent(new CustomEvent("neurosoc:notification", { detail: notification }));
    });
    return () => {
      stop();
      window.removeEventListener("neurosoc:connection", connectionHandler);
    };
  }, [authenticated]);
  if (!authenticated) return <Auth complete={() => refresh((v) => v + 1)} />;
  const role = user?.role || "SECURITY_VIEWER";
  const available = nav.filter((item) => item.length < 4 || item[3] === role);
  const sections = [...new Set(available.map((item) => item[0]))];
  return <div className="min-h-screen bg-slate-950 text-slate-100"><div className="flex"><aside className={`${collapsed ? "w-20" : "w-72"} hidden shrink-0 border-r border-slate-800 p-4 lg:block`}><button aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} onClick={() => setCollapsed(!collapsed)} className="mb-5 rounded border border-slate-700 px-2 py-1">{collapsed ? "»" : "«"}</button>{!collapsed && <><p className="text-xs uppercase tracking-[0.3em] text-cyan-400">NeuroSOC</p><p className="mt-1 font-semibold">Enterprise SOC</p></>}<nav>{sections.map((section) => <div key={section} className="mt-5">{!collapsed && <p className="mb-1 px-3 text-[11px] uppercase text-slate-500">{section}</p>}{available.filter((item) => item[0] === section).map((item) => <Link key={item[2]} to={item[2]} aria-current={location.pathname === item[2] ? "page" : undefined} className={`mb-1 block rounded-lg px-3 py-2 text-sm ${location.pathname === item[2] ? "bg-cyan-950 text-cyan-300" : "text-slate-300 hover:bg-slate-900"}`}>{collapsed ? item[1][0] : item[1]}</Link>)}</div>)}</nav></aside><div className="min-w-0 flex-1"><header className="flex h-16 items-center justify-between border-b border-slate-800 px-5">  <span className="text-sm text-slate-400">SOC workspace</span><span className="ml-auto mr-4 text-xs text-slate-400" title="Live update connection">{realtimeStatus}</span><div className="flex gap-3 text-sm"><span>{user?.username || "Loading user…"}</span><button onClick={() => { logout(); refresh((v) => v + 1); }} className="rounded border border-slate-700 px-3 py-1.5">Sign out</button></div></header><main className="mx-auto max-w-[1600px] p-4 sm:p-6"><Routes><Route path="/" element={<Overview />} /><Route path="/events" element={<Events />} /><Route path="/alerts" element={<Alerts />} /><Route path="/detections" element={<Generic title="Detection Engine" description="Detection instances returned by the backend." endpoint="/detections" fields={["id", "name", "severity", "rule_id", "enabled"]} />} /><Route path="/threat-intelligence" element={<Generic title="Threat Intelligence" description="The backend has no IOC listing endpoint. No unverified or fabricated intelligence is shown." endpoint="/missing/threat-intelligence" fields={["indicator"]} />} /><Route path="/cases" element={<Cases />} /><Route path="/investigations" element={<Investigations />} /><Route path="/search" element={<Search />} /><Route path="/mitre" element={<Generic title="MITRE ATT&CK" description="Only an aggregate MITRE count exists. Technique and tactic listings require a backend endpoint." endpoint="/missing/mitre" fields={["technique_id"]} />} /><Route path="/users" element={role === "ADMIN" ? <Users /> : <Navigate to="/" replace />} /><Route path="/audit" element={role === "ADMIN" ? <Generic title="Audit Logs" description="Read-only audit entries from the administrator API." endpoint="/admin/audit-logs" fields={["created_at", "actor", "action", "target_type", "outcome", "request_id"]} /> : <Navigate to="/" replace />} /><Route path="/reports" element={<Reports />} /><Route path="/settings" element={role === "ADMIN" ? <Settings /> : <Navigate to="/" replace />} /><Route path="*" element={<Navigate to="/" replace />} /></Routes></main></div></div></div>;
}
