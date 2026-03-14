"""
Prometheus-style Metrics Pipeline.

Collects, stores, and processes time-series metrics with support for
counters, gauges, and histograms.  Exports to JSON for downstream
consumption.
"""

import json
import statistics
from datetime import datetime, timezone


class MetricsPipeline:
    """Collects and processes Prometheus-style metrics."""

    VALID_METRIC_TYPES = {"counter", "gauge", "histogram"}

    def __init__(self):
        self._metrics = {}     # name -> metadata
        self._values = {}      # name -> list of (timestamp, value)

    def register_metric(
        self, name: str, metric_type: str, description: str = ""
    ) -> dict:
        """Register a new metric.

        Args:
            name: Unique metric name.
            metric_type: One of counter, gauge, histogram.
            description: Human-readable description.

        Returns:
            Metric registration dict.

        Raises:
            ValueError: If the metric already exists or the type is invalid.
        """
        if name in self._metrics:
            raise ValueError(f"Metric '{name}' already registered")
        if metric_type not in self.VALID_METRIC_TYPES:
            raise ValueError(
                f"Invalid metric type '{metric_type}'. "
                f"Valid: {self.VALID_METRIC_TYPES}"
            )

        self._metrics[name] = {
            "name": name,
            "type": metric_type,
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._values[name] = []
        return self._metrics[name]

    def record_value(
        self, name: str, value: float, timestamp: str | None = None
    ) -> dict:
        """Record a value for a registered metric.

        Args:
            name: Metric name.
            value: Numeric value to record.
            timestamp: Optional ISO-8601 timestamp (defaults to now).

        Returns:
            dict with name, value, and timestamp.

        Raises:
            KeyError: If the metric is not registered.
            ValueError: If the value violates type constraints.
        """
        if name not in self._metrics:
            raise KeyError(f"Metric '{name}' not registered")

        metric_type = self._metrics[name]["type"]
        if metric_type == "counter" and value < 0:
            raise ValueError("Counter values must be non-negative")

        ts = timestamp or datetime.now(timezone.utc).isoformat()
        entry = {"timestamp": ts, "value": value}
        self._values[name].append(entry)
        return {"name": name, **entry}

    def compute_aggregations(self, name: str) -> dict:
        """Compute aggregations for a metric.

        Returns:
            dict with count, sum, mean, min, max (and stddev where applicable).

        Raises:
            KeyError: If the metric is not registered.
            ValueError: If no values have been recorded.
        """
        if name not in self._metrics:
            raise KeyError(f"Metric '{name}' not registered")

        values = [e["value"] for e in self._values[name]]
        if not values:
            raise ValueError(f"No values recorded for metric '{name}'")

        agg = {
            "metric": name,
            "count": len(values),
            "sum": sum(values),
            "mean": statistics.mean(values),
            "min": min(values),
            "max": max(values),
        }
        if len(values) >= 2:
            agg["stddev"] = statistics.stdev(values)
        return agg

    def export_to_json(self, name: str | None = None) -> str:
        """Export metrics and their values to a JSON string.

        Args:
            name: If provided, export only this metric; otherwise export all.

        Returns:
            JSON string.
        """
        if name:
            if name not in self._metrics:
                raise KeyError(f"Metric '{name}' not registered")
            data = {
                "metrics": [
                    {**self._metrics[name], "values": self._values[name]}
                ]
            }
        else:
            data = {
                "metrics": [
                    {**meta, "values": self._values[n]}
                    for n, meta in self._metrics.items()
                ]
            }
        return json.dumps(data, indent=2)

    def list_metrics(self) -> list:
        """Return a list of all registered metric summaries."""
        return [
            {
                "name": m["name"],
                "type": m["type"],
                "value_count": len(self._values[m["name"]]),
            }
            for m in self._metrics.values()
        ]

    def delete_metric(self, name: str) -> dict:
        """Delete a metric and its recorded values.

        Raises:
            KeyError: If the metric is not registered.
        """
        if name not in self._metrics:
            raise KeyError(f"Metric '{name}' not registered")
        meta = self._metrics.pop(name)
        self._values.pop(name)
        return {"deleted": meta["name"]}
