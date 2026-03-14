"""Tests for Grafana-style Observability Manager."""

import json

import pytest
from src.observability import ObservabilityManager


@pytest.fixture
def obs():
    return ObservabilityManager()


def test_create_dashboard(obs):
    dash = obs.create_dashboard("Cluster Overview", "Main cluster dashboard")
    assert dash["title"] == "Cluster Overview"
    assert dash["panels"] == []


def test_create_dashboard_duplicate_raises(obs):
    obs.create_dashboard("dup")
    with pytest.raises(ValueError, match="already exists"):
        obs.create_dashboard("dup")


def test_add_panel(obs):
    obs.create_dashboard("Metrics")
    panel = obs.add_panel("Metrics", "CPU Usage", "graph", "avg(cpu_usage)")
    assert panel["title"] == "CPU Usage"
    assert panel["type"] == "graph"
    assert panel["query"] == "avg(cpu_usage)"


def test_add_panel_invalid_type(obs):
    obs.create_dashboard("Bad Panel")
    with pytest.raises(ValueError, match="Invalid panel type"):
        obs.add_panel("Bad Panel", "X", "pie_chart", "query")


def test_export_dashboard_json(obs):
    obs.create_dashboard("Export Test")
    obs.add_panel("Export Test", "P1", "stat", "sum(requests)")
    exported = json.loads(obs.export_dashboard("Export Test"))
    assert exported["title"] == "Export Test"
    assert len(exported["panels"]) == 1


def test_create_alert_rule(obs):
    rule = obs.create_alert_rule(
        "HighCPU", "avg(cpu_usage)", threshold=90.0, severity="critical"
    )
    assert rule["name"] == "HighCPU"
    assert rule["threshold"] == 90.0
    assert rule["severity"] == "critical"
    assert rule["enabled"] is True


def test_evaluate_alert_firing(obs):
    obs.create_alert_rule("HighMem", "avg(mem_usage)", threshold=80.0)
    result = obs.evaluate_alert("HighMem", current_value=95.0)
    assert result["firing"] is True


def test_evaluate_alert_not_firing(obs):
    obs.create_alert_rule("LowLatency", "avg(latency)", threshold=500.0)
    result = obs.evaluate_alert("LowLatency", current_value=200.0)
    assert result["firing"] is False


def test_list_alert_rules(obs):
    obs.create_alert_rule("A1", "q1", threshold=10.0, severity="info")
    obs.create_alert_rule("A2", "q2", threshold=20.0, severity="warning")
    rules = obs.list_alert_rules()
    assert len(rules) == 2
    names = {r["name"] for r in rules}
    assert names == {"A1", "A2"}


def test_delete_alert_rule(obs):
    obs.create_alert_rule("ToDelete", "q", threshold=1.0)
    result = obs.delete_alert_rule("ToDelete")
    assert result["deleted"] == "ToDelete"
    assert obs.list_alert_rules() == []
