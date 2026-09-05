"""
Security and edge case tests for Modified Duke Endocarditis Criteria.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import os
import tempfile
from agents.base import PHIGuard, AuditTrail, SecurityException
from duke_endocarditis import calculate_metrics, process_batch, _safe_resolve_path


class TestPathTraversalProtection:
    """Tests for path traversal prevention."""

    def test_safe_resolve_rejects_traversal(self):
        with pytest.raises(ValueError, match="Access denied"):
            _safe_resolve_path("../../../etc/passwd")

    def test_safe_resolve_accepts_cwd_file(self, tmp_path):
        test_file = tmp_path / "test.csv"
        test_file.write_text("data")
        result = _safe_resolve_path(str(test_file))
        assert result == test_file.resolve()

    def test_safe_resolve_accepts_relative_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        test_file = tmp_path / "test.csv"
        test_file.write_text("data")
        result = _safe_resolve_path("test.csv")
        assert result == test_file.resolve()

    def test_process_batch_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            process_batch(str(tmp_path / "nonexistent.csv"), str(tmp_path / "out.csv"))

    def test_process_batch_directory_input(self, tmp_path):
        with pytest.raises(ValueError, match="not a file"):
            process_batch(str(tmp_path), str(tmp_path / "out.csv"))


class TestAuditSecurity:
    """Tests for audit trail security requirements."""

    def test_audit_trail_requires_secret_key(self, monkeypatch):
        monkeypatch.delenv("AUDIT_SECRET_KEY", raising=False)
        with pytest.raises(SecurityException, match="AUDIT_SECRET_KEY environment variable must be set"):
            AuditTrail()

    def test_audit_trail_rejects_short_key(self, monkeypatch):
        monkeypatch.setenv("AUDIT_SECRET_KEY", "short")
        with pytest.raises(SecurityException, match="at least 16 characters"):
            AuditTrail()

    def test_audit_trail_accepts_valid_key(self, monkeypatch):
        monkeypatch.setenv("AUDIT_SECRET_KEY", "a" * 32)
        trail = AuditTrail()
        assert trail.secret_key == b"a" * 32

    def test_audit_trail_accepts_explicit_key(self):
        trail = AuditTrail(secret_key="my-secret-key-1234567890")
        assert trail.secret_key == b"my-secret-key-1234567890"


class TestPHIGuard:
    """Tests for PHI detection and redaction."""

    def test_detects_mrn(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-12345678")

    def test_detects_ssn(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_detects_phone(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call 555-123-4567")

    def test_detects_email(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@example.com")

    def test_redacts_phi(self):
        text = "Patient John Doe MRN-12345 called 555-123-4567"
        redacted = PHIGuard.redact_phi(text)
        assert "REDACTED_IDENTIFIER" in redacted
        assert "MRN" not in redacted or "12345" not in redacted

    def test_allows_clean_text(self):
        PHIGuard.assert_no_phi("Analytical specimen KEY-001 optimal")

    def test_empty_text_passes(self):
        PHIGuard.assert_no_phi("")


class TestCalculateMetricsEdgeCases:
    """Tests for calculate_metrics edge cases."""

    def test_empty_input(self):
        result = calculate_metrics()
        assert result["score"] == 1.0  # default when no numeric values
        assert result["classification"] == "Low / Standard"

    def test_single_value(self):
        result = calculate_metrics(v1=15.0)
        assert result["score"] == 15.0

    def test_mixed_types(self):
        result = calculate_metrics(v1=10.0, name="test", v2=5.0)
        # Algorithm: score = v1 + v2 * (1/2) = 10 + 2.5 = 12.5
        assert result["score"] == 12.5
        assert result["inputs_evaluated"] == 3  # all params counted

    def test_none_values_ignored(self):
        result = calculate_metrics(v1=10.0, v2=None)
        assert result["score"] == 10.0

    def test_string_values_handled(self):
        result = calculate_metrics(v1="invalid", v2=5.0)
        assert result["score"] == 5.0  # only v2 is numeric

    def test_negative_values(self):
        result = calculate_metrics(v1=-10.0)
        assert result["score"] == -10.0
        assert result["classification"] == "Low / Standard"

    def test_zero_values(self):
        result = calculate_metrics(v1=0.0)
        assert result["score"] == 0.0
