"""Tests for Terraform Configuration Validator."""

import pytest
from src.terraform_validator import TerraformValidator


@pytest.fixture
def validator():
    return TerraformValidator()


def _make_config(resources):
    return {"resources": resources}


def test_valid_config(validator):
    config = _make_config([
        {
            "name": "my-instance",
            "type": "google_compute_instance",
            "config": {"name": "vm-1", "machine_type": "e2-standard-2", "zone": "us-central1-a"},
        }
    ])
    result = validator.validate_config(config)
    assert result["valid"] is True
    assert result["errors"] == []


def test_missing_resources_key(validator):
    result = validator.validate_config({})
    assert result["valid"] is False
    assert "Missing top-level 'resources' key" in result["errors"]


def test_invalid_resource_type(validator):
    config = _make_config([
        {"name": "bad", "type": "aws_ec2_instance", "config": {}}
    ])
    result = validator.validate_config(config)
    assert result["valid"] is False
    assert any("invalid type" in e for e in result["errors"])


def test_missing_required_fields(validator):
    config = _make_config([
        {
            "name": "incomplete",
            "type": "google_compute_instance",
            "config": {"name": "vm-1"},  # missing machine_type and zone
        }
    ])
    result = validator.validate_config(config)
    assert result["valid"] is False
    assert any("machine_type" in e for e in result["errors"])
    assert any("zone" in e for e in result["errors"])


def test_circular_dependency_detected(validator):
    config = _make_config([
        {"name": "a", "type": "google_storage_bucket", "config": {"name": "a", "location": "US"}, "depends_on": ["b"]},
        {"name": "b", "type": "google_storage_bucket", "config": {"name": "b", "location": "US"}, "depends_on": ["a"]},
    ])
    result = validator.validate_config(config)
    assert result["valid"] is False
    assert any("Circular dependency" in e for e in result["errors"])


def test_no_circular_dependency(validator):
    config = _make_config([
        {"name": "a", "type": "google_storage_bucket", "config": {"name": "a", "location": "US"}, "depends_on": ["b"]},
        {"name": "b", "type": "google_storage_bucket", "config": {"name": "b", "location": "US"}},
    ])
    result = validator.validate_config(config)
    assert result["valid"] is True


def test_validate_resource_type_valid(validator):
    assert validator.validate_resource_type("google_container_cluster") is True


def test_validate_resource_type_invalid(validator):
    assert validator.validate_resource_type("aws_lambda_function") is False


def test_missing_type_field(validator):
    config = _make_config([{"name": "no-type", "config": {}}])
    result = validator.validate_config(config)
    assert result["valid"] is False
    assert any("missing 'type'" in e for e in result["errors"])
