"""Tests for admin-configurable surveillance base image feature.

Covers:
- Allowlist construction (defaults + env-var extras)
- TheiaContainerManager.is_image_allowed / get_allowed_images / get_default_surveillance_image
- _resolve_image_to_use fallback chain with an admin-configured image
- Validation logic in the PUT /admin/settings endpoint (simulated via helper)
"""

from __future__ import annotations

import os
import sys
import types
import pytest

# ---------------------------------------------------------------------------
# Minimal stubs so we can import theia_service without real dependencies
# ---------------------------------------------------------------------------

BACKEND_DIR = os.path.dirname(__file__)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Stub out modules that theia_service doesn't strictly need for our tests
for mod_name in ("pymysql", "dotenv", "fastapi"):
    if mod_name not in sys.modules:
        stub = types.ModuleType(mod_name)
        if mod_name == "dotenv":
            stub.load_dotenv = lambda *a, **kw: None
        if mod_name == "fastapi":
            class _HTTPException(Exception):
                def __init__(self, status_code=500, detail=""):
                    self.status_code = status_code
                    self.detail = detail
            stub.HTTPException = _HTTPException
        sys.modules[mod_name] = stub

from services.theia_service import TheiaContainerManager, _build_allowed_images, _DEFAULT_ALLOWED_IMAGES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manager(env_overrides: dict | None = None, monkeypatch=None) -> TheiaContainerManager:
    """Create a TheiaContainerManager with mocked filesystem/db."""
    if env_overrides and monkeypatch:
        for key, value in env_overrides.items():
            monkeypatch.setenv(key, value)

    manager = TheiaContainerManager.__new__(TheiaContainerManager)
    # Populate only the attributes exercised by the methods under test
    manager.db_manager = None
    manager.theia_image = os.getenv("THEIA_IMAGE", "elswork/theia")
    manager.default_theia_image = os.getenv("DEFAULT_THEIA_IMAGE", None)
    manager.theia_booking_image = os.getenv("THEIA_BOOKING_IMAGE", None)
    manager.allowed_images = _build_allowed_images()
    return manager


# ---------------------------------------------------------------------------
# _build_allowed_images
# ---------------------------------------------------------------------------

class TestBuildAllowedImages:
    def test_defaults_always_present(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_SURVEILLANCE_IMAGES", raising=False)
        images = _build_allowed_images()
        for img in _DEFAULT_ALLOWED_IMAGES:
            assert img in images

    def test_extra_images_from_env(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_SURVEILLANCE_IMAGES", "my-custom/image:latest,another/image")
        images = _build_allowed_images()
        assert "my-custom/image:latest" in images
        assert "another/image" in images

    def test_no_duplicates(self, monkeypatch):
        # Re-adding a default image via env should not produce duplicates
        monkeypatch.setenv("ALLOWED_SURVEILLANCE_IMAGES", _DEFAULT_ALLOWED_IMAGES[0])
        images = _build_allowed_images()
        assert images.count(_DEFAULT_ALLOWED_IMAGES[0]) == 1

    def test_order_defaults_first(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_SURVEILLANCE_IMAGES", "extra/image:v1")
        images = _build_allowed_images()
        assert images[0] == _DEFAULT_ALLOWED_IMAGES[0]

    def test_empty_env_var_ignored(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_SURVEILLANCE_IMAGES", "  ,  ,  ")
        images = _build_allowed_images()
        assert images == _DEFAULT_ALLOWED_IMAGES


# ---------------------------------------------------------------------------
# TheiaContainerManager allowlist helpers
# ---------------------------------------------------------------------------

class TestAllowlistHelpers:
    def test_get_allowed_images_returns_list(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_SURVEILLANCE_IMAGES", raising=False)
        m = _make_manager()
        assert isinstance(m.get_allowed_images(), list)
        assert len(m.get_allowed_images()) >= len(_DEFAULT_ALLOWED_IMAGES)

    def test_is_image_allowed_true_for_default(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_SURVEILLANCE_IMAGES", raising=False)
        m = _make_manager()
        for img in _DEFAULT_ALLOWED_IMAGES:
            assert m.is_image_allowed(img) is True

    def test_is_image_allowed_false_for_arbitrary(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_SURVEILLANCE_IMAGES", raising=False)
        m = _make_manager()
        assert m.is_image_allowed("attacker/malicious:latest") is False

    def test_is_image_allowed_strips_whitespace(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_SURVEILLANCE_IMAGES", raising=False)
        m = _make_manager()
        assert m.is_image_allowed(f"  {_DEFAULT_ALLOWED_IMAGES[0]}  ") is True

    def test_get_default_surveillance_image(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_SURVEILLANCE_IMAGES", raising=False)
        m = _make_manager()
        assert m.get_default_surveillance_image() == _DEFAULT_ALLOWED_IMAGES[0]


# ---------------------------------------------------------------------------
# _resolve_image_to_use with admin-configured image
# ---------------------------------------------------------------------------

class TestResolveImageToUse:
    def test_robot_override_takes_priority(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_SURVEILLANCE_IMAGES", raising=False)
        m = _make_manager()
        m.default_theia_image = "admin/configured:v1"
        result = m._resolve_image_to_use("robot/specific:v2")
        assert result == "robot/specific:v2"

    def test_admin_configured_used_when_no_robot_override(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_SURVEILLANCE_IMAGES", raising=False)
        m = _make_manager()
        m.default_theia_image = "muneeb/theia-ros-humble:v2"
        result = m._resolve_image_to_use(None)
        assert result == "muneeb/theia-ros-humble:v2"

    def test_fallback_to_booking_image(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_SURVEILLANCE_IMAGES", raising=False)
        m = _make_manager()
        m.default_theia_image = None
        m.theia_booking_image = "muneeb/theia-ros-humble:v2"
        result = m._resolve_image_to_use(None)
        assert result == "muneeb/theia-ros-humble:v2"

    def test_fallback_to_theia_image(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_SURVEILLANCE_IMAGES", raising=False)
        m = _make_manager()
        m.default_theia_image = None
        m.theia_booking_image = None
        m.theia_image = "elswork/theia"
        result = m._resolve_image_to_use(None)
        assert result == "elswork/theia"

    def test_empty_string_override_treated_as_none(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_SURVEILLANCE_IMAGES", raising=False)
        m = _make_manager()
        m.default_theia_image = "muneeb/theia-ros-humble:v2"
        result = m._resolve_image_to_use("   ")
        assert result == "muneeb/theia-ros-humble:v2"


# ---------------------------------------------------------------------------
# Validation logic (simulating PUT /admin/settings behaviour)
# ---------------------------------------------------------------------------

class TestSettingsValidation:
    """Simulate the image validation that the PUT /admin/settings endpoint performs."""

    def _validate(self, manager: TheiaContainerManager, image: str):
        """Returns (is_valid, error_detail)"""
        if not manager.is_image_allowed(image):
            return False, f"Image '{image}' is not in the allowlist."
        return True, None

    def test_valid_image_passes(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_SURVEILLANCE_IMAGES", raising=False)
        m = _make_manager()
        ok, err = self._validate(m, _DEFAULT_ALLOWED_IMAGES[0])
        assert ok is True
        assert err is None

    def test_invalid_image_rejected(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_SURVEILLANCE_IMAGES", raising=False)
        m = _make_manager()
        ok, err = self._validate(m, "evil/image:latest")
        assert ok is False
        assert "allowlist" in err

    def test_extra_env_image_accepted(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_SURVEILLANCE_IMAGES", "custom/ros:humble")
        m = _make_manager()
        ok, err = self._validate(m, "custom/ros:humble")
        assert ok is True

    def test_default_fallback_is_valid(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_SURVEILLANCE_IMAGES", raising=False)
        m = _make_manager()
        fallback = m.get_default_surveillance_image()
        ok, _ = self._validate(m, fallback)
        assert ok is True
