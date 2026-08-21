"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";

const tooltipStyle = {
  background: "#141a22",
  border: "1px solid #262f3c",
  borderRadius: 12,
  boxShadow: "0 12px 32px -16px rgba(0,0,0,0.6)",
  fontSize: 12,
};

interface VolumeChartProps {
  data: { date: string; volume: number }[];
}

export function VolumeChart({ data }: VolumeChartProps) {
  const formatted = data.map((d) => ({
    ...d,
    label: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={formatted} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="volumeStroke" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#17965c" />
            <stop offset="100%" stopColor="#3dd68c" />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="4 6" stroke="#262f3c" vertical={false} />
        <XAxis dataKey="label" stroke="#6b7380" fontSize={11} tickLine={false} axisLine={false} dy={8} />
        <YAxis
          stroke="#6b7380"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip
          contentStyle={tooltipStyle}
          labelStyle={{ color: "#8b949e", marginBottom: 4 }}
          itemStyle={{ color: "#e8eaed" }}
          formatter={(value: number) => [`${value.toLocaleString()} lbs`, "Volume"]}
        />
        <Line
          type="monotone"
          dataKey="volume"
          stroke="url(#volumeStroke)"
          strokeWidth={2.5}
          dot={{ r: 3, fill: "#3dd68c", strokeWidth: 0 }}
          activeDot={{ r: 5, fill: "#3dd68c", stroke: "#0a0c0f", strokeWidth: 2 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

interface E1RMChartProps {
  data: { date: string; estimated_1rm: number }[];
  color?: string;
}

export function E1RMChart({ data, color = "#3dd68c" }: E1RMChartProps) {
  const formatted = data.map((d) => ({
    ...d,
    label: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={formatted} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="4 6" stroke="#262f3c" vertical={false} />
        <XAxis dataKey="label" stroke="#6b7380" fontSize={11} tickLine={false} axisLine={false} dy={8} />
        <YAxis stroke="#6b7380" fontSize={11} tickLine={false} axisLine={false} />
        <Tooltip
          contentStyle={tooltipStyle}
          formatter={(value: number) => [`${value} lbs`, "Est. 1RM"]}
        />
        <Line
          type="monotone"
          dataKey="estimated_1rm"
          stroke={color}
          strokeWidth={2.5}
          dot={{ r: 3, fill: color, strokeWidth: 0 }}
          activeDot={{ r: 5, fill: color, stroke: "#0a0c0f", strokeWidth: 2 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

interface BarChartSimpleProps {
  data: { name: string; volume: number }[];
}

export function ExerciseBarChart({ data }: BarChartSimpleProps) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="4 6" stroke="#262f3c" horizontal={false} />
        <XAxis
          type="number"
          stroke="#6b7380"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
        />
        <YAxis
          type="category"
          dataKey="name"
          stroke="#8b949e"
          fontSize={11}
          width={128}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          contentStyle={tooltipStyle}
          formatter={(value: number) => [`${value.toLocaleString()} lbs`, "Volume"]}
        />
        <Bar dataKey="volume" fill="#22b872" radius={[0, 6, 6, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

interface ScoreBreakdownProps {
  scores: Record<string, number>;
}

const SCORE_LABELS: Record<string, string> = {
  consistency: "Consistency",
  rpe: "RPE Management",
  volume: "Volume Trend",
  progression: "Long-term Progress",
  recent_performance: "Recent Performance",
};

export function ScoreBreakdown({ scores }: ScoreBreakdownProps) {
  return (
    <div className="space-y-4">
      {Object.entries(scores).map(([key, value]) => (
        <div key={key}>
          <div className="mb-1.5 flex justify-between text-sm">
            <span className="text-surface-muted">{SCORE_LABELS[key] || key}</span>
            <span className="font-display font-semibold text-ink">{value.toFixed(0)}</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded bg-surface-hover">
            <div
              className="h-full rounded transition-all duration-500 ease-out"
              style={{
                width: `${value}%`,
                backgroundColor: value >= 75 ? "#3dd68c" : value >= 50 ? "#d4a017" : "#e55a5a",
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
