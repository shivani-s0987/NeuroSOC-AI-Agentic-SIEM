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
  { label: "Events", value: "12.4K" },
  { label: "Alerts", value: "284" },
  { label: "Cases", value: "17" },
  { label: "MITRE", value: "43" },
];

function HomePage() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        {overviewStats.map((stat) => (
          <div key={stat.label} className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
            <p className="text-sm text-slate-400">{stat.label}</p>
            <p className="mt-2 text-3xl font-semibold text-white">{stat.value}</p>
          </div>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6">
          <h2 className="text-lg font-semibold">Events over time</h2>
          <Line
            data={{
              labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
              datasets: [
                {
                  label: "Events",
                  data: [120, 190, 240, 180, 260, 300, 220],
                  borderColor: "#38bdf8",
                  backgroundColor: "rgba(56,189,248,0.2)",
                },
              ],
            }}
          />
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6">
          <h2 className="text-lg font-semibold">Alert severity</h2>
          <Doughnut
            data={{
              labels: ["Critical", "High", "Medium", "Low"],
              datasets: [
                {
                  data: [12, 48, 90, 25],
                  backgroundColor: ["#ef4444", "#f59e0b", "#3b82f6", "#10b981"],
                },
              ],
            }}
          />
        </div>
      </div>
    </div>
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

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <aside className="w-full border-b border-slate-800 bg-slate-950/70 p-4 lg:w-72 lg:border-b-0 lg:border-r">
          <div className="mb-6">
            <p className="text-sm uppercase tracking-[0.3em] text-cyan-400">NeuroSOC</p>
            <h1 className="text-2xl font-semibold">AI-Assisted SOC</h1>
          </div>
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
            <Route path="/events" element={<PlaceholderPage title="Events" />} />
            <Route path="/alerts" element={<PlaceholderPage title="Alerts" />} />
            <Route path="/detections" element={<PlaceholderPage title="Detections" />} />
            <Route path="/intel" element={<PlaceholderPage title="Threat Intelligence" />} />
            <Route path="/cases" element={<PlaceholderPage title="Cases" />} />
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
