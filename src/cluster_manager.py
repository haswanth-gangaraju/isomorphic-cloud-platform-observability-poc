"""
GCP Kubernetes Cluster Manager Simulator.

Simulates core GKE cluster operations including creation, scaling,
health checks, and node listing without requiring actual GCP credentials.
"""

import uuid
from datetime import datetime, timezone


class ClusterManager:
    """Simulates GCP Kubernetes cluster management operations."""

    VALID_MACHINE_TYPES = [
        "e2-standard-2", "e2-standard-4", "e2-standard-8",
        "n2-standard-2", "n2-standard-4", "n2-standard-8",
        "c2-standard-4", "c2-standard-8",
    ]

    VALID_REGIONS = [
        "us-central1", "us-east1", "us-west1",
        "europe-west1", "europe-west2",
        "asia-east1", "asia-southeast1",
    ]

    def __init__(self):
        self._clusters = {}

    def create_cluster(
        self,
        name: str,
        region: str,
        node_count: int = 3,
        machine_type: str = "e2-standard-4",
    ) -> dict:
        """Create a new Kubernetes cluster.

        Args:
            name: Unique cluster name.
            region: GCP region for the cluster.
            node_count: Initial number of nodes (must be >= 1).
            machine_type: GCP machine type for the nodes.

        Returns:
            dict describing the created cluster.

        Raises:
            ValueError: If parameters are invalid or cluster already exists.
        """
        if name in self._clusters:
            raise ValueError(f"Cluster '{name}' already exists")
        if region not in self.VALID_REGIONS:
            raise ValueError(
                f"Invalid region '{region}'. Valid: {self.VALID_REGIONS}"
            )
        if machine_type not in self.VALID_MACHINE_TYPES:
            raise ValueError(
                f"Invalid machine type '{machine_type}'. "
                f"Valid: {self.VALID_MACHINE_TYPES}"
            )
        if node_count < 1:
            raise ValueError("node_count must be >= 1")

        cluster_id = str(uuid.uuid4())[:8]
        nodes = self._generate_nodes(name, node_count, machine_type)

        cluster = {
            "id": cluster_id,
            "name": name,
            "region": region,
            "status": "RUNNING",
            "node_count": node_count,
            "machine_type": machine_type,
            "nodes": nodes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "kubernetes_version": "1.28.3-gke.1200",
        }
        self._clusters[name] = cluster
        return cluster

    def scale_cluster(self, name: str, target_node_count: int) -> dict:
        """Scale a cluster to the target node count.

        Args:
            name: Cluster name.
            target_node_count: Desired number of nodes.

        Returns:
            Updated cluster dict.

        Raises:
            KeyError: If cluster does not exist.
            ValueError: If target_node_count < 1.
        """
        if name not in self._clusters:
            raise KeyError(f"Cluster '{name}' not found")
        if target_node_count < 1:
            raise ValueError("target_node_count must be >= 1")

        cluster = self._clusters[name]
        machine_type = cluster["machine_type"]
        cluster["nodes"] = self._generate_nodes(
            name, target_node_count, machine_type
        )
        cluster["node_count"] = target_node_count
        return cluster

    def health_check(self, name: str) -> dict:
        """Run a health check on the cluster.

        Returns:
            dict with overall status and per-node health.

        Raises:
            KeyError: If cluster does not exist.
        """
        if name not in self._clusters:
            raise KeyError(f"Cluster '{name}' not found")

        cluster = self._clusters[name]
        node_health = []
        all_healthy = True
        for node in cluster["nodes"]:
            healthy = node["status"] == "READY"
            node_health.append({
                "node_name": node["name"],
                "healthy": healthy,
                "status": node["status"],
            })
            if not healthy:
                all_healthy = False

        return {
            "cluster": name,
            "overall_healthy": all_healthy,
            "node_count": len(cluster["nodes"]),
            "nodes": node_health,
        }

    def list_nodes(self, name: str) -> list:
        """List all nodes in a cluster.

        Args:
            name: Cluster name.

        Returns:
            List of node dicts.

        Raises:
            KeyError: If cluster does not exist.
        """
        if name not in self._clusters:
            raise KeyError(f"Cluster '{name}' not found")
        return list(self._clusters[name]["nodes"])

    def delete_cluster(self, name: str) -> dict:
        """Delete a cluster.

        Args:
            name: Cluster name.

        Returns:
            Confirmation dict.

        Raises:
            KeyError: If cluster does not exist.
        """
        if name not in self._clusters:
            raise KeyError(f"Cluster '{name}' not found")
        cluster = self._clusters.pop(name)
        return {"deleted": name, "id": cluster["id"]}

    def list_clusters(self) -> list:
        """List all clusters.

        Returns:
            List of cluster summary dicts.
        """
        return [
            {
                "name": c["name"],
                "region": c["region"],
                "status": c["status"],
                "node_count": c["node_count"],
            }
            for c in self._clusters.values()
        ]

    # ---- internal helpers ----

    @staticmethod
    def _generate_nodes(cluster_name: str, count: int, machine_type: str) -> list:
        return [
            {
                "name": f"{cluster_name}-node-{i}",
                "status": "READY",
                "machine_type": machine_type,
                "zone": "a",
            }
            for i in range(count)
        ]
