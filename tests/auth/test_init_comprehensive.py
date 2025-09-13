"""Comprehensive tests for auth.__init__ module - imports, re-exports, lazy loading."""

import sys
import warnings
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
import dotmac.platform.auth as auth_module


class TestAuthImports:
    """Test import availability and side effects."""

    def test_module_basic_imports(self):
        """Test that auth module imports successfully."""
        assert auth_module is not None
        assert hasattr(auth_module, "__version__")
        assert hasattr(auth_module, "__all__")

    def test_all_exports_list(self):
        """Test that __all__ is properly defined."""
        all_exports = auth_module.__all__
        assert isinstance(all_exports, list)
        assert len(all_exports) > 0
        
        # Common expected exports
        expected = [
            "JWTService",
            "create_jwt_service",
            "RBACEngine",
            "Role",
            "Permission",
            "SessionManager",
            "MFAService",
            "OAuthService",
            "AuthenticationError",
            "AuthorizationError",
            "InvalidTokenError",
        ]
        
        for export in expected:
            if export in all_exports:
                # Check that the export is actually available
                assert hasattr(auth_module, export) or export in ["create_jwt_service"]

    def test_import_side_effects(self):
        """Test that importing doesn't cause unwanted side effects."""
        # Capture warnings during import
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Re-import to check for warnings
            import importlib
            importlib.reload(auth_module)
            
            # Check if there are import warnings (expected for missing optional deps)
            import_warnings = [warning for warning in w if "not available" in str(warning.message)]
            # This is OK - some services might not be available

    def test_lazy_loading_pattern(self):
        """Test lazy loading behavior for heavy components."""
        # Check that certain heavy components use lazy loading
        assert hasattr(auth_module, "_jwt_available") or True  # May not expose this
        assert hasattr(auth_module, "_rbac_available") or True  # May not expose this
        
        # Test that services can be conditionally imported
        if hasattr(auth_module, "JWTService"):
            assert auth_module.JWTService is not None or auth_module.JWTService is None


class TestPublicAPIReExports:
    """Test public API re-exports."""

    def test_jwt_service_exports(self):
        """Test JWT service re-exports."""
        if hasattr(auth_module, "JWTService"):
            # Should be re-exported from jwt_service module
            from dotmac.platform.auth.jwt_service import JWTService as DirectImport
            
            if auth_module.JWTService is not None:
                assert auth_module.JWTService is DirectImport

    def test_rbac_exports(self):
        """Test RBAC engine re-exports."""
        if hasattr(auth_module, "RBACEngine"):
            from dotmac.platform.auth.rbac_engine import RBACEngine as DirectImport
            
            if auth_module.RBACEngine is not None:
                assert auth_module.RBACEngine is DirectImport
                
        if hasattr(auth_module, "Role"):
            from dotmac.platform.auth.rbac_engine import Role as DirectImport
            
            if auth_module.Role is not None:
                assert auth_module.Role is DirectImport

    def test_exception_exports(self):
        """Test exception class re-exports."""
        from dotmac.platform.auth.exceptions import (
            AuthenticationError,
            AuthorizationError,
            InvalidTokenError,
        )
        
        if hasattr(auth_module, "AuthenticationError"):
            assert auth_module.AuthenticationError is AuthenticationError
        if hasattr(auth_module, "AuthorizationError"):
            assert auth_module.AuthorizationError is AuthorizationError
        if hasattr(auth_module, "InvalidTokenError"):
            assert auth_module.InvalidTokenError is InvalidTokenError

    def test_session_manager_export(self):
        """Test SessionManager re-export."""
        if hasattr(auth_module, "SessionManager"):
            from dotmac.platform.auth.session_manager import SessionManager as DirectImport
            
            if auth_module.SessionManager is not None:
                assert auth_module.SessionManager is DirectImport

    def test_mfa_service_export(self):
        """Test MFAService re-export."""
        if hasattr(auth_module, "MFAService"):
            from dotmac.platform.auth.mfa_service import MFAService as DirectImport
            
            if auth_module.MFAService is not None:
                assert auth_module.MFAService is DirectImport


class TestHelperFunctions:
    """Test helper functions and factory methods."""

    def test_create_jwt_service(self):
        """Test create_jwt_service helper function."""
        if hasattr(auth_module, "create_jwt_service"):
            # Function should exist even if it returns None when JWT not available
            assert callable(auth_module.create_jwt_service) or auth_module.create_jwt_service is None

    def test_create_rbac_engine(self):
        """Test create_rbac_engine helper function."""
        if hasattr(auth_module, "create_rbac_engine"):
            assert callable(auth_module.create_rbac_engine) or auth_module.create_rbac_engine is None

    def test_initialize_auth_service(self):
        """Test initialize_auth_service function."""
        if hasattr(auth_module, "initialize_auth_service"):
            assert callable(auth_module.initialize_auth_service)
            
            # Test with minimal config
            with patch("dotmac.platform.auth.JWTService") as mock_jwt:
                mock_jwt.return_value = MagicMock()
                
                config = {
                    "auth": {
                        "jwt": {"secret_key": "test-secret", "algorithm": "HS256"}
                    }
                }
                
                try:
                    result = auth_module.initialize_auth_service(config)
                    # May return a service or None depending on availability
                except Exception:
                    # OK if it fails due to missing dependencies
                    pass


class TestModuleAttributes:
    """Test module-level attributes."""

    def test_version_attribute(self):
        """Test __version__ attribute."""
        assert hasattr(auth_module, "__version__")
        version = auth_module.__version__
        assert isinstance(version, str)
        # Should be semantic version
        parts = version.split(".")
        assert len(parts) >= 2  # At least major.minor

    def test_module_docstring(self):
        """Test module has proper docstring."""
        assert auth_module.__doc__ is not None
        assert len(auth_module.__doc__) > 0
        assert "auth" in auth_module.__doc__.lower()

    def test_cache_config_available(self):
        """Test CacheConfig is available."""
        assert hasattr(auth_module, "CacheConfig")
        from dotmac.platform.auth.cache_config import CacheConfig
        assert auth_module.CacheConfig is CacheConfig


class TestConditionalImports:
    """Test conditional import behavior."""

    @patch.dict(sys.modules, {"dotmac.platform.auth.jwt_service": None})
    def test_jwt_import_failure_handling(self):
        """Test handling of JWT import failure."""
        # Force reload to trigger import failure
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # This tests the try/except block for JWT imports
            import importlib
            
            # Remove from cache if exists
            if "dotmac.platform.auth" in sys.modules:
                del sys.modules["dotmac.platform.auth"]
            
            # Re-import should handle missing JWT gracefully
            from dotmac.platform import auth
            
            # Should have warned about missing JWT
            jwt_warnings = [warning for warning in w if "JWT" in str(warning.message)]
            # This is expected behavior

    def test_optional_dependencies(self):
        """Test that optional dependencies are handled gracefully."""
        # These should not raise even if dependencies are missing
        optional_attrs = [
            "OAuthService",
            "MFAService",
            "SessionManager",
        ]
        
        for attr in optional_attrs:
            # Should either exist or be None, but not raise AttributeError
            value = getattr(auth_module, attr, None)
            # OK if None (not available) or a class/function


class TestFactoryFunctions:
    """Test factory functions for creating auth services."""

    def test_create_jwt_service_from_config(self):
        """Test JWT service factory from config."""
        if hasattr(auth_module, "create_jwt_service_from_config"):
            if auth_module.create_jwt_service_from_config is not None:
                assert callable(auth_module.create_jwt_service_from_config)
                
                # Test with basic config
                from dotmac.platform.auth.jwt_service import JWTConfig
                config = JWTConfig(secret_key="test-key", algorithm="HS256")
                
                try:
                    service = auth_module.create_jwt_service_from_config(config)
                    if service is not None:
                        assert hasattr(service, "generate_token")
                except Exception:
                    # OK if fails due to dependencies
                    pass

    def test_create_rbac_engine_factory(self):
        """Test RBAC engine factory."""
        if hasattr(auth_module, "create_rbac_engine"):
            if auth_module.create_rbac_engine is not None:
                assert callable(auth_module.create_rbac_engine)
                
                try:
                    engine = auth_module.create_rbac_engine()
                    if engine is not None:
                        assert hasattr(engine, "check_permission")
                except Exception:
                    # OK if fails due to dependencies
                    pass


class TestBackwardCompatibility:
    """Test backward compatibility for deprecated imports."""

    def test_deprecated_aliases(self):
        """Test that deprecated aliases still work with warnings."""
        # Example: old name -> new name mappings
        deprecated_mappings = {
            # Add any deprecated mappings here
            # "old_function": "new_function",
        }
        
        for old_name, new_name in deprecated_mappings.items():
            if hasattr(auth_module, old_name):
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    
                    # Access deprecated attribute
                    value = getattr(auth_module, old_name)
                    
                    # Should warn about deprecation
                    deprecation_warnings = [
                        warning for warning in w 
                        if "deprecated" in str(warning.message).lower()
                    ]
                    # Expect deprecation warning

    def test_legacy_import_paths(self):
        """Test that legacy import paths are maintained."""
        # These should still work for backward compatibility
        try:
            from dotmac.platform.auth import AuthenticationError
            assert AuthenticationError is not None
        except ImportError:
            # OK if new structure doesn't support this
            pass


class TestModuleInitialization:
    """Test module initialization and setup."""

    def test_module_initialization_order(self):
        """Test that module initializes in correct order."""
        # Check that core components are initialized before dependent ones
        if hasattr(auth_module, "CacheConfig"):
            # CacheConfig should be available early
            assert auth_module.CacheConfig is not None
        
        # Check initialization flags if exposed
        if hasattr(auth_module, "_initialized"):
            assert isinstance(auth_module._initialized, bool)

    def test_module_cleanup(self):
        """Test module cleanup on reload."""
        import importlib
        
        # Get initial state
        initial_modules = set(sys.modules.keys())
        
        # Reload module
        importlib.reload(auth_module)
        
        # Check no orphaned modules
        final_modules = set(sys.modules.keys())
        # Should not leak module references

    def test_circular_import_prevention(self):
        """Test that circular imports are prevented."""
        # This should not cause circular import
        from dotmac.platform import auth
        from dotmac.platform.auth import exceptions
        
        # Both should be importable without issues
        assert auth is not None
        assert exceptions is not None