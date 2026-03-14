"""Tests for GCP Kubernetes Cluster Manager."""

import pytest
from src.cluster_manager import ClusterManager


@pytest.fixture
def manager():
    return ClusterManager()


def test_create_cluster_success(manager):
    cluster = manager.create_cluster(
        name="test-cluster",
        region="us-central1",
        node_count=3,
        machine_type="e2-standard-4",
    )
    assert cluster["name"] == "test-cluster"
    assert cluster["region"] == "us-central1"
    assert cluster["node_count"] == 3
    assert cluster["status"] == "RUNNING"
    assert len(cluster["nodes"]) == 3


def test_create_cluster_duplicate_raises(manager):
    manager.create_cluster("dup", region="us-central1")
    with pytest.raises(ValueError, match="already exists"):
        manager.create_cluster("dup", region="us-central1")


def test_create_cluster_invalid_region(manager):
    with pytest.raises(ValueError, match="Invalid region"):
        manager.create_cluster("bad-region", region="mars-west1")


def test_create_cluster_invalid_machine_type(manager):
    with pytest.raises(ValueError, match="Invalid machine type"):
        manager.create_cluster(
            "bad-machine", region="us-central1", machine_type="z9-mega-128"
        )


def test_scale_cluster(manager):
    manager.create_cluster("scale-me", region="us-east1", node_count=2)
    updated = manager.scale_cluster("scale-me", target_node_count=5)
    assert updated["node_count"] == 5
    assert len(updated["nodes"]) == 5


def test_scale_cluster_not_found(manager):
    with pytest.raises(KeyError, match="not found"):
        manager.scale_cluster("ghost", target_node_count=3)


def test_health_check(manager):
    manager.create_cluster("healthy", region="europe-west1", node_count=3)
    health = manager.health_check("healthy")
    assert health["overall_healthy"] is True
    assert health["node_count"] == 3
    assert all(n["healthy"] for n in health["nodes"])


def test_list_nodes(manager):
    manager.create_cluster("nodes", region="us-west1", node_count=4)
    nodes = manager.list_nodes("nodes")
    assert len(nodes) == 4
    assert nodes[0]["name"] == "nodes-node-0"


def test_delete_cluster(manager):
    manager.create_cluster("doomed", region="us-central1")
    result = manager.delete_cluster("doomed")
    assert result["deleted"] == "doomed"
    assert manager.list_clusters() == []


def test_list_clusters(manager):
    manager.create_cluster("c1", region="us-central1")
    manager.create_cluster("c2", region="us-east1")
    clusters = manager.list_clusters()
    assert len(clusters) == 2
    names = {c["name"] for c in clusters}
    assert names == {"c1", "c2"}
