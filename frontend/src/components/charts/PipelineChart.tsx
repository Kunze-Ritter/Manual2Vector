import { ResponsiveContainer, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Bar, Cell } from 'recharts';

import type { PipelineMetrics } from '@/types/api';

interface PipelineChartProps {
  data?: PipelineMetrics | null;
}

const palette = {
  pending: '#f59e0b',
  processing: '#2563eb',
  completed: '#16a34a',
  failed: '#dc2626',
};

export default function PipelineChart({ data }: PipelineChartProps) {
  const chartData = data
    ? [
        { name: 'Pending', value: data.documents_pending, fill: palette.pending },
        { name: 'Processing', value: data.documents_processing, fill: palette.processing },
        { name: 'Completed', value: data.documents_completed, fill: palette.completed },
        { name: 'Failed', value: data.documents_failed, fill: palette.failed },
      ]
    : [];

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} barSize={28}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis dataKey="name" tickLine={false} axisLine={false} className="text-sm text-muted-foreground" />
          <YAxis allowDecimals={false} tickLine={false} className="text-sm text-muted-foreground" />
          <Tooltip cursor={{ fill: 'hsl(var(--muted)/0.25)' }} />
          <Bar dataKey="value" radius={[6, 6, 0, 0]}>
            {chartData.map((entry) => (
              <Cell key={entry.name} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
