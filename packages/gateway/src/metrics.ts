type Labels = Record<string, string> | undefined;

interface CounterEntry {
  value: number;
  labels: Map<string, Map<string, number>>;
}

interface GaugeEntry {
  value: number;
  labels: Map<string, number>;
}

interface HistogramEntry {
  buckets: Map<string, number>;
  sum: number;
  count: number;
  labels: Map<string, { buckets: Map<string, number>; sum: number; count: number }>;
}

const DEFAULT_BUCKETS = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000];

function labelKey(labels?: Record<string, string>): string {
  if (!labels) return '';
  return Object.keys(labels)
    .sort()
    .map((k) => `${k}="${labels[k]}"`)
    .join(',');
}

export class MetricsCollector {
  private counters = new Map<string, CounterEntry>();
  private gauges = new Map<string, GaugeEntry>();
  private histograms = new Map<string, HistogramEntry>();

  incCounter(name: string, labels?: Labels): void {
    let entry = this.counters.get(name);
    if (!entry) {
      entry = { value: 0, labels: new Map() };
      this.counters.set(name, entry);
    }
    const key = labelKey(labels);
    if (!labels) {
      entry.value++;
    } else {
      entry.value++;
      const inner = entry.labels.get(key) ?? new Map();
      for (const [k, v] of Object.entries(labels)) {
        inner.set(v, (inner.get(v) ?? 0) + 1);
      }
      entry.labels.set(key, inner);
    }
  }

  setGauge(name: string, value: number, labels?: Labels): void {
    const key = labelKey(labels);
    let entry = this.gauges.get(name);
    if (!entry) {
      entry = { value: 0, labels: new Map() };
      this.gauges.set(name, entry);
    }
    if (!labels) {
      entry.value = value;
    } else {
      entry.labels.set(key, value);
    }
  }

  observeHistogram(name: string, value: number, labels?: Labels): void {
    const key = labelKey(labels);
    let entry = this.histograms.get(name);
    if (!entry) {
      entry = { buckets: new Map(), sum: 0, count: 0, labels: new Map() };
      for (const b of DEFAULT_BUCKETS) {
        entry.buckets.set(String(b), 0);
      }
      entry.buckets.set('+Inf', 0);
      this.histograms.set(name, entry);
    }

    entry.sum += value;
    entry.count++;

    for (const b of DEFAULT_BUCKETS) {
      if (value <= b) {
        entry.buckets.set(String(b), (entry.buckets.get(String(b)) ?? 0) + 1);
      }
    }
    entry.buckets.set('+Inf', (entry.buckets.get('+Inf') ?? 0) + 1);

    if (labels) {
      let labelEntry = entry.labels.get(key);
      if (!labelEntry) {
        labelEntry = { buckets: new Map(), sum: 0, count: 0 };
        for (const b of DEFAULT_BUCKETS) {
          labelEntry.buckets.set(String(b), 0);
        }
        labelEntry.buckets.set('+Inf', 0);
        entry.labels.set(key, labelEntry);
      }
      labelEntry.sum += value;
      labelEntry.count++;
      for (const b of DEFAULT_BUCKETS) {
        if (value <= b) {
          labelEntry.buckets.set(String(b), (labelEntry.buckets.get(String(b)) ?? 0) + 1);
        }
      }
      labelEntry.buckets.set('+Inf', (labelEntry.buckets.get('+Inf') ?? 0) + 1);
    }
  }

  getPrometheusFormat(): string {
    const lines: string[] = [];

    for (const [name, entry] of this.counters) {
      lines.push(`# HELP ${name} Total ${name.replace(/_/g, ' ')}`);
      lines.push(`# TYPE ${name} counter`);
      lines.push(`${name} ${entry.value}`);
      for (const [, inner] of entry.labels) {
        for (const [, count] of inner) {
          lines.push(`${name}{...} ${count}`);
        }
      }
    }

    for (const [name, entry] of this.gauges) {
      lines.push(`# HELP ${name} Current ${name.replace(/_/g, ' ')}`);
      lines.push(`# TYPE ${name} gauge`);
      lines.push(`${name} ${entry.value}`);
      for (const [key, val] of entry.labels) {
        lines.push(`${name}{${key}} ${val}`);
      }
    }

    for (const [name, entry] of this.histograms) {
      lines.push(`# HELP ${name} ${name.replace(/_/g, ' ')} histogram`);
      lines.push(`# TYPE ${name} histogram`);

      const sortedBuckets = [...entry.buckets.entries()].sort((a, b) => {
        if (a[0] === '+Inf') return 1;
        if (b[0] === '+Inf') return -1;
        return Number(a[0]) - Number(b[0]);
      });

      let cumulative = 0;
      for (const [le, count] of sortedBuckets) {
        cumulative += count;
        lines.push(`${name}_bucket{le="${le}"} ${cumulative}`);
      }
      lines.push(`${name}_sum ${entry.sum}`);
      lines.push(`${name}_count ${entry.count}`);
    }

    return lines.length > 0 ? lines.join('\n') + '\n' : '';
  }
}

export const metricsCollector = new MetricsCollector();
