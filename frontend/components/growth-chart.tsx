"use client";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function GrowthChart({ history }: { history: { timestamp: string; points: number }[] }) {
  const data = history.map((item) => ({ ...item, label: new Date(item.timestamp).toLocaleDateString("fr-FR", { day: "2-digit", month: "short" }) }));
  if (!data.length) return <p className="empty">Les courbes apparaîtront après les prochains snapshots.</p>;
  return <div className="growth-chart"><ResponsiveContainer width="100%" height={220}><AreaChart data={data}><defs><linearGradient id="points" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#54d4ff" stopOpacity={.6}/><stop offset="100%" stopColor="#54d4ff" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#273246" vertical={false}/><XAxis dataKey="label" stroke="#8ea0bb" tickLine={false}/><YAxis stroke="#8ea0bb" tickLine={false} width={54}/><Tooltip contentStyle={{ background: "#111827", border: "1px solid #273246" }}/><Area dataKey="points" stroke="#54d4ff" fill="url(#points)" strokeWidth={2}/></AreaChart></ResponsiveContainer></div>;
}
