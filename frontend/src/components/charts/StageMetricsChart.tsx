import { ResponsiveContainer, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Bar, Cell, LabelList } from 'recharts';

import type { StageMetrics } from '@/types/api';

export type StageMetricType = 'success_rate' | 'completed_count' | 'failed_count' | 'avg_duration_seconds';

interface StageMetricsChartProps {
  data?: StageMetrics[] | null;
  metric?: StageMetricType;
}

const metricConfig: Record<StageMetricType, { label: string; formatter: (stage: StageMetrics) => number; suffix?: string; decimals?: number }> = {
  success_rate: {
    label: 'Success Rate (%)',
    formatter: (stage) => stage.success_rate * 100,
    suffix: '%',
    decimals: 0,
  },
  completed_count: {
    label: 'Completed',
    formatter: (stage) => stage.completed_count,
  },
  failed_count: {
    label: 'Failed',
    formatter: (stage) => stage.failed_count,
  },
  avg_duration_seconds: {
    label: 'Avg Duration (s)',
    formatter: (stage) => stage.avg_duration_seconds,
    decimals: 1,
  },
};

const palette = ['#2563eb', '#16a34a', '#f97316', '#dc2626', '#7c3aed', '#0ea5e9'];

export default function StageMetricsChart({ data, metric = 'success_rate' }: StageMetricsChartProps) {
  const config = metricConfig[metric];

  const stages = data ?? [];

  const chartData = stages.map((stage, index) => ({
    stage: stage.stage_name,
    value: Number(config.formatter(stage).toFixed(config.decimals ?? 0)),
    fill: palette[index % palette.length],
  }));

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 16, right: 24, bottom: 24, left: 16 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis dataKey="stage" tickLine={false} axisLine={false} className="text-xs text-muted-foreground" interval={0} angle={-30} dy={10} dx={-10} />
          <YAxis tickLine={false} axisLine={false} className="text-xs text-muted-foreground" allowDecimals />
          <Tooltip
            labelFormatter={(label) => label}
            formatter={(value: number) => [`${value}${config.suffix ?? ''}`, config.label]}
            cursor={{ fill: 'hsl(var(--muted)/0.25)' }}
          />
          <Bar dataKey="value" radius={[6, 6, 0, 0]}>
            <LabelList dataKey="value" position="top" className="text-xs text-muted-foreground" formatter={(value: number) => `${value}${config.suffix ?? ''}`} />
            {chartData.map((entry) => (
              <Cell key={entry.stage} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
