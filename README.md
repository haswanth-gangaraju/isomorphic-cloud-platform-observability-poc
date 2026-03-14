# Cloud Platform Observability POC

Proof-of-concept demonstrating cloud platform engineering skills for GCP Kubernetes cluster management, Terraform configuration validation, Prometheus-style metrics collection, and Grafana-style observability dashboard generation.

## Modules

- **cluster_manager** - Simulates GKE cluster operations (create, scale, health check, node listing)
- **terraform_validator** - Validates Terraform configs for required fields, resource types, and circular dependencies
- **metrics_pipeline** - Collects and processes Prometheus-style metrics with aggregation and JSON export
- **observability** - Generates Grafana-style dashboard configurations and manages alert rules

## Setup

```bash
pip install -r requirements.txt
```

## Running Tests

```bash
python -m pytest -q
```
