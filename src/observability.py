"""
Grafana-style Observability Dashboard & Alert Manager.

Generates dashboard configurations and manages alert rules that
can be serialised to JSON for import into real Grafana instances.
"""

import json
import uuid
from datetime import datetime, timezone


class ObservabilityManager:
    """Manages Grafana-style dashboards and alert rules."""

    VALID_PANEL_TYPES = {"graph", "stat", "gauge", "table", "heatmap", "logs"}
    VALID_SEVERITIES = {"critical", "warning", "info"}

    def __init__(self):
        self._dashboards = {}
        self._alert_rules = {}

    # ---- Dashboard management ----

    def create_dashboard(self, title: str, description: str = "") -> dict:
        """Create a new dashboard.

        Args:
            title: Dashboard title (must be unique).
            description: Optional description.

        Returns:
            Dashboard dict.

        Raises:
            ValueError: If a dashboard with the same title already exists.
        """
        if title in self._dashboards:
            raise ValueError(f"Dashboard '{title}' already exists")

        dashboard = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "description": description,
            "panels": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._dashboards[title] = dashboard
        return dashboard

    def add_panel(
        self,
        dashboard_title: str,
        panel_title: str,
        panel_type: str,
        metric_query: str,
    ) -> dict:
        """Add a panel to an existing dashboard.

        Args:
            dashboard_title: Title of the target dashboard.
            panel_title: Title of the new panel.
            panel_type: One of the VALID_PANEL_TYPES.
            metric_query: PromQL-style query string.

        Returns:
            The created panel dict.

        Raises:
            KeyError: If the dashboard does not exist.
            ValueError: If the panel type is invalid.
        """
        if dashboard_title not in self._dashboards:
            raise KeyError(f"Dashboard '{dashboard_title}' not found")
        if panel_type not in self.VALID_PANEL_TYPES:
            raise ValueError(
                f"Invalid panel type '{panel_type}'. "
                f"Valid: {self.VALID_PANEL_TYPES}"
            )

        panel = {
            "id": str(uuid.uuid4())[:8],
            "title": panel_title,
            "type": panel_type,
            "query": metric_query,
        }
        self._dashboards[dashboard_title]["panels"].append(panel)
        return panel

    def get_dashboard(self, title: str) -> dict:
        """Retrieve a dashboard by title.

        Raises:
            KeyError: If not found.
        """
        if title not in self._dashboards:
            raise KeyError(f"Dashboard '{title}' not found")
        return self._dashboards[title]

    def export_dashboard(self, title: str) -> str:
        """Export a dashboard configuration as a JSON string.

        Raises:
            KeyError: If not found.
        """
        dashboard = self.get_dashboard(title)
        return json.dumps(dashboard, indent=2)

    def list_dashboards(self) -> list:
        """Return summary list of all dashboards."""
        return [
            {
                "title": d["title"],
                "panel_count": len(d["panels"]),
                "created_at": d["created_at"],
            }
            for d in self._dashboards.values()
        ]

    # ---- Alert rule management ----

    def create_alert_rule(
        self,
        name: str,
        metric_query: str,
        threshold: float,
        severity: str = "warning",
        description: str = "",
    ) -> dict:
        """Create a new alert rule.

        Args:
            name: Unique alert rule name.
            metric_query: PromQL-style query.
            threshold: Numeric threshold to trigger the alert.
            severity: One of critical, warning, info.
            description: Optional human-readable description.

        Returns:
            Alert rule dict.

        Raises:
            ValueError: If the name is taken or severity is invalid.
        """
        if name in self._alert_rules:
            raise ValueError(f"Alert rule '{name}' already exists")
        if severity not in self.VALID_SEVERITIES:
            raise ValueError(
                f"Invalid severity '{severity}'. "
                f"Valid: {self.VALID_SEVERITIES}"
            )

        rule = {
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "query": metric_query,
            "threshold": threshold,
            "severity": severity,
            "description": description,
            "enabled": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._alert_rules[name] = rule
        return rule

    def evaluate_alert(self, name: str, current_value: float) -> dict:
        """Evaluate an alert rule against a current metric value.

        Returns:
            dict with firing (bool) and details.

        Raises:
            KeyError: If the alert rule does not exist.
        """
        if name not in self._alert_rules:
            raise KeyError(f"Alert rule '{name}' not found")

        rule = self._alert_rules[name]
        firing = current_value > rule["threshold"]
        return {
            "alert": name,
            "firing": firing,
            "current_value": current_value,
            "threshold": rule["threshold"],
            "severity": rule["severity"],
        }

    def list_alert_rules(self) -> list:
        """Return summary of all alert rules."""
        return [
            {
                "name": r["name"],
                "severity": r["severity"],
                "threshold": r["threshold"],
                "enabled": r["enabled"],
            }
            for r in self._alert_rules.values()
        ]

    def delete_alert_rule(self, name: str) -> dict:
        """Delete an alert rule.

        Raises:
            KeyError: If not found.
        """
        if name not in self._alert_rules:
            raise KeyError(f"Alert rule '{name}' not found")
        rule = self._alert_rules.pop(name)
        return {"deleted": rule["name"]}
