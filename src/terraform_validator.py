"""
Terraform Configuration Validator.

Validates Terraform-style configuration dicts for required fields,
resource type correctness, and circular dependency detection.
"""

from collections import defaultdict


class TerraformValidator:
    """Validates Terraform configuration represented as Python dicts."""

    VALID_RESOURCE_TYPES = {
        "google_compute_instance",
        "google_container_cluster",
        "google_container_node_pool",
        "google_storage_bucket",
        "google_pubsub_topic",
        "google_pubsub_subscription",
        "google_bigquery_dataset",
        "google_bigquery_table",
        "google_cloud_run_service",
        "google_sql_database_instance",
        "google_monitoring_alert_policy",
        "google_logging_metric",
    }

    REQUIRED_FIELDS = {
        "google_compute_instance": ["name", "machine_type", "zone"],
        "google_container_cluster": ["name", "location", "initial_node_count"],
        "google_storage_bucket": ["name", "location"],
        "google_pubsub_topic": ["name"],
        "google_bigquery_dataset": ["dataset_id", "location"],
        "google_cloud_run_service": ["name", "location"],
    }

    def validate_config(self, config: dict) -> dict:
        """Validate a full Terraform configuration.

        Args:
            config: Dict with a top-level ``"resources"`` key containing
                    a list of resource definitions.

        Returns:
            dict with ``valid`` (bool) and ``errors`` (list of str).
        """
        errors = []

        if "resources" not in config:
            return {"valid": False, "errors": ["Missing top-level 'resources' key"]}

        resources = config["resources"]
        if not isinstance(resources, list):
            return {"valid": False, "errors": ["'resources' must be a list"]}

        for idx, resource in enumerate(resources):
            errors.extend(self._validate_resource(resource, idx))

        dep_errors = self.detect_circular_dependencies(config)
        errors.extend(dep_errors)

        return {"valid": len(errors) == 0, "errors": errors}

    def validate_resource_type(self, resource_type: str) -> bool:
        """Check whether a resource type is valid."""
        return resource_type in self.VALID_RESOURCE_TYPES

    def check_required_fields(self, resource: dict) -> list:
        """Return a list of missing required fields for a resource.

        Args:
            resource: A resource dict with at least ``type`` and ``config``.

        Returns:
            List of error strings (empty if all required fields present).
        """
        rtype = resource.get("type", "")
        config = resource.get("config", {})
        required = self.REQUIRED_FIELDS.get(rtype, [])
        missing = [f for f in required if f not in config]
        return [
            f"Resource '{resource.get('name', 'unknown')}' ({rtype}): "
            f"missing required field '{f}'"
            for f in missing
        ]

    def detect_circular_dependencies(self, config: dict) -> list:
        """Detect circular dependencies among resources.

        Each resource may declare a ``depends_on`` list referencing other
        resource names.

        Returns:
            List of error strings describing cycles found.
        """
        resources = config.get("resources", [])
        graph = defaultdict(list)
        names = set()

        for r in resources:
            name = r.get("name", "")
            names.add(name)
            for dep in r.get("depends_on", []):
                graph[name].append(dep)

        errors = []
        visited = set()
        rec_stack = set()

        def _dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in names:
                    continue
                if neighbor not in visited:
                    _dfs(neighbor, path + [neighbor])
                elif neighbor in rec_stack:
                    cycle = path[path.index(neighbor):] + [neighbor]
                    errors.append(
                        f"Circular dependency detected: {' -> '.join(cycle)}"
                    )
            rec_stack.discard(node)

        for name in names:
            if name not in visited:
                _dfs(name, [name])

        return errors

    # ---- internal helpers ----

    def _validate_resource(self, resource: dict, idx: int) -> list:
        errors = []
        if "type" not in resource:
            errors.append(f"Resource at index {idx}: missing 'type'")
            return errors

        rtype = resource["type"]
        if not self.validate_resource_type(rtype):
            errors.append(
                f"Resource at index {idx}: invalid type '{rtype}'"
            )

        errors.extend(self.check_required_fields(resource))
        return errors
