"""Tests for Prometheus-style Metrics Pipeline."""

import json

import pytest
from src.metrics_pipeline import MetricsPipeline


@pytest.fixture
def pipeline():
    return MetricsPipeline()


def test_register_metric(pipeline):
    metric = pipeline.register_metric("cpu_usage", "gauge", "CPU percentage")
    assert metric["name"] == "cpu_usage"
    assert metric["type"] == "gauge"


def test_register_duplicate_raises(pipeline):
    pipeline.register_metric("dup", "counter")
    with pytest.raises(ValueError, match="already registered"):
        pipeline.register_metric("dup", "counter")


def test_register_invalid_type(pipeline):
    with pytest.raises(ValueError, match="Invalid metric type"):
        pipeline.register_metric("bad", "sparkline")


def test_record_value(pipeline):
    pipeline.register_metric("requests", "counter")
    entry = pipeline.record_value("requests", 42.0)
    assert entry["name"] == "requests"
    assert entry["value"] == 42.0


def test_record_negative_counter_raises(pipeline):
    pipeline.register_metric("neg_counter", "counter")
    with pytest.raises(ValueError, match="non-negative"):
        pipeline.record_value("neg_counter", -5)


def test_record_unregistered_raises(pipeline):
    with pytest.raises(KeyError, match="not registered"):
        pipeline.record_value("ghost", 1.0)


def test_compute_aggregations(pipeline):
    pipeline.register_metric("latency", "histogram")
    for v in [10, 20, 30, 40, 50]:
        pipeline.record_value("latency", v)
    agg = pipeline.compute_aggregations("latency")
    assert agg["count"] == 5
    assert agg["sum"] == 150
    assert agg["mean"] == 30
    assert agg["min"] == 10
    assert agg["max"] == 50
    assert "stddev" in agg


def test_compute_aggregations_no_values(pipeline):
    pipeline.register_metric("empty", "gauge")
    with pytest.raises(ValueError, match="No values"):
        pipeline.compute_aggregations("empty")


def test_export_to_json_single(pipeline):
    pipeline.register_metric("mem", "gauge")
    pipeline.record_value("mem", 75.5)
    exported = json.loads(pipeline.export_to_json("mem"))
    assert len(exported["metrics"]) == 1
    assert exported["metrics"][0]["name"] == "mem"
    assert len(exported["metrics"][0]["values"]) == 1


def test_export_to_json_all(pipeline):
    pipeline.register_metric("a", "counter")
    pipeline.register_metric("b", "gauge")
    exported = json.loads(pipeline.export_to_json())
    assert len(exported["metrics"]) == 2


def test_list_metrics(pipeline):
    pipeline.register_metric("x", "counter")
    pipeline.record_value("x", 1)
    pipeline.record_value("x", 2)
    listing = pipeline.list_metrics()
    assert len(listing) == 1
    assert listing[0]["value_count"] == 2


def test_delete_metric(pipeline):
    pipeline.register_metric("temp", "gauge")
    result = pipeline.delete_metric("temp")
    assert result["deleted"] == "temp"
    assert pipeline.list_metrics() == []
