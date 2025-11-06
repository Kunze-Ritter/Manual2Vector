import { ResponsiveContainer, LineChart, CartesianGrid, XAxis, YAxis, Tooltip, Line, ReferenceLine } from 'recharts';

interface ThroughputPoint {
  timestamp: string;
  throughput: number;
}

interface ThroughputChartProps {
  data?: ThroughputPoint[];
}

export default function ThroughputChart({ data = [] }: ThroughputChartProps) {
  const hasData = data.length > 0;
  const chartData = hasData
    ? data.map((point) => ({ ...point, label: new Date(point.timestamp).toLocaleTimeString() }))
    : [];

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 16, right: 24, bottom: 16, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis dataKey="label" tickLine={false} axisLine={false} className="text-xs text-muted-foreground" minTickGap={24} />
          <YAxis tickLine={false} axisLine={false} className="text-xs text-muted-foreground" allowDecimals={false} />
          <Tooltip cursor={{ stroke: 'hsl(var(--muted-foreground))', strokeWidth: 1 }} />
          <ReferenceLine y={0} stroke="hsl(var(--muted))" />
          <Line type="monotone" dataKey="throughput" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
