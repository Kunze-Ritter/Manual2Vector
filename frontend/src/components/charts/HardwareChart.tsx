import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell } from 'recharts';

import type { HardwareStatus } from '@/types/api';

interface HardwareChartProps {
  data?: HardwareStatus | null;
}

const palette = {
  cpu: '#2563eb',
  ram: '#16a34a',
  gpu: '#a855f7',
};

export default function HardwareChart({ data }: HardwareChartProps) {
  const chartData = data
    ? [
        { name: 'CPU', value: data.cpu_percent, fill: palette.cpu },
        { name: 'RAM', value: data.ram_percent, fill: palette.ram },
        ...(data.gpu_available && data.gpu_percent !== null
          ? [{ name: 'GPU', value: data.gpu_percent, fill: palette.gpu }]
          : []),
      ]
    : [];

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="vertical" margin={{ top: 16, right: 24, bottom: 16, left: 32 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis type="number" domain={[0, 100]} tickLine={false} axisLine={false} className="text-sm text-muted-foreground" />
          <YAxis type="category" dataKey="name" tickLine={false} width={80} className="text-sm text-muted-foreground" />
          <Tooltip cursor={{ fill: 'hsl(var(--muted)/0.25)' }} />
          <Bar dataKey="value" radius={[0, 6, 6, 0]}>
            {chartData.map((entry) => (
              <Cell key={entry.name} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
