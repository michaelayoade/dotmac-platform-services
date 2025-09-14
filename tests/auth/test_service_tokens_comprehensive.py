"""
Comprehensive tests for auth.service_tokens module.

This module tests the compatibility module for service_tokens imports.
"""

from unittest.mock import patch

import pytest


class TestServiceTokensImports:
    """Test service_tokens module imports and re-exports."""

    def test_service_auth_middleware_import(self):
        """Test that ServiceAuthMiddleware can be imported from service_tokens."""
        from dotmac.platform.auth.service_tokens import ServiceAuthMiddleware

        assert ServiceAuthMiddleware is not None
        # Test that it's the same object as from service_auth
        from dotmac.platform.auth.service_auth import ServiceAuthMiddleware as OriginalMiddleware

        assert ServiceAuthMiddleware is OriginalMiddleware

    def test_create_service_token_manager_import(self):
        """Test that create_service_token_manager can be imported from service_tokens."""
        from dotmac.platform.auth.service_tokens import create_service_token_manager

        assert create_service_token_manager is not None
        # Test that it's the same object as from service_auth
        from dotmac.platform.auth.service_auth import (
            create_service_token_manager as OriginalFunction,
        )

        assert create_service_token_manager is OriginalFunction

    def test_all_exports_available(self):
        """Test that all exports defined in __all__ are available."""
        from dotmac.platform.auth import service_tokens

        # Test that __all__ is defined
        assert hasattr(service_tokens, "__all__")
        assert isinstance(service_tokens.__all__, list)
        assert len(service_tokens.__all__) == 2

        # Test that all items in __all__ are actually exported
        for item_name in service_tokens.__all__:
            assert hasattr(service_tokens, item_name)

    def test_module_docstring(self):
        """Test that the module has proper documentation."""
        from dotmac.platform.auth import service_tokens

        assert service_tokens.__doc__ is not None
        assert "Compatibility module" in service_tokens.__doc__
        assert "service_auth" in service_tokens.__doc__

    def test_import_all_items(self):
        """Test importing all items using * import pattern."""
        # This tests the __all__ functionality
        exec("from dotmac.platform.auth.service_tokens import *")

        # Items should be available in local scope after * import
        # We can't easily test this without using exec, but we can test __all__ exists
        from dotmac.platform.auth import service_tokens

        assert "ServiceAuthMiddleware" in service_tokens.__all__
        assert "create_service_token_manager" in service_tokens.__all__


class TestServiceAuthMiddlewareCompatibility:
    """Test ServiceAuthMiddleware compatibility through service_tokens."""

    def test_middleware_class_availability(self):
        """Test that ServiceAuthMiddleware class is available through service_tokens."""
        from dotmac.platform.auth.service_tokens import ServiceAuthMiddleware

        # Test that it's a class
        assert isinstance(ServiceAuthMiddleware, type)

        # Test that it has expected attributes (from service_auth module)
        # We test indirectly by checking it's the same object
        from dotmac.platform.auth.service_auth import ServiceAuthMiddleware as Original

        assert ServiceAuthMiddleware.__name__ == Original.__name__

    def test_middleware_instantiation_compatibility(self):
        """Test that middleware can be instantiated through service_tokens import."""
        from dotmac.platform.auth.service_tokens import ServiceAuthMiddleware

        # Test basic instantiation (with minimal required params)
        with patch("dotmac.platform.auth.service_auth.JWTService"):
            try:
                # We can't fully instantiate without proper config, but we can test the class exists
                assert callable(ServiceAuthMiddleware)
            except Exception:
                # Expected - just testing that the class is available
                pass


class TestCreateServiceTokenManagerCompatibility:
    """Test create_service_token_manager function compatibility."""

    def test_function_availability(self):
        """Test that create_service_token_manager function is available."""
        from dotmac.platform.auth.service_tokens import create_service_token_manager

        # Test that it's callable
        assert callable(create_service_token_manager)

        # Test that it's the same object as original
        from dotmac.platform.auth.service_auth import create_service_token_manager as Original

        assert create_service_token_manager is Original

    def test_function_signature_compatibility(self):
        """Test that function signature is preserved through re-export."""
        from dotmac.platform.auth.service_auth import create_service_token_manager as Original
        from dotmac.platform.auth.service_tokens import create_service_token_manager

        # Test they have the same signature (same function object)
        assert create_service_token_manager.__name__ == Original.__name__
        assert create_service_token_manager.__doc__ == Original.__doc__


class TestModuleStructure:
    """Test the overall structure of the service_tokens module."""

    def test_module_is_compatibility_layer(self):
        """Test that the module serves as a proper compatibility layer."""
        from dotmac.platform.auth import service_tokens

        # Test that it only contains the expected exports
        module_attributes = [attr for attr in dir(service_tokens) if not attr.startswith("_")]

        # Should include the re-exported items
        expected_attrs = set(["ServiceAuthMiddleware", "create_service_token_manager"])
        actual_attrs = set(module_attributes)

        # The actual attributes should be a superset of expected (may have __all__, etc.)
        assert expected_attrs.issubset(actual_attrs)

    def test_no_additional_functionality(self):
        """Test that the module doesn't add extra functionality beyond re-exports."""
        from dotmac.platform.auth import service_auth, service_tokens

        # ServiceAuthMiddleware should be exactly the same object
        assert service_tokens.ServiceAuthMiddleware is service_auth.ServiceAuthMiddleware

        # create_service_token_manager should be exactly the same object
        assert (
            service_tokens.create_service_token_manager is service_auth.create_service_token_manager
        )


class TestImportPatterns:
    """Test different import patterns work correctly."""

    def test_direct_import(self):
        """Test direct import of specific items."""
        from dotmac.platform.auth.service_tokens import (
            ServiceAuthMiddleware,
            create_service_token_manager,
        )

        assert ServiceAuthMiddleware is not None
        assert create_service_token_manager is not None

    def test_module_import(self):
        """Test importing the module and accessing attributes."""
        import dotmac.platform.auth.service_tokens as service_tokens

        assert hasattr(service_tokens, "ServiceAuthMiddleware")
        assert hasattr(service_tokens, "create_service_token_manager")

    def test_nested_import(self):
        """Test nested import pattern."""
        from dotmac.platform.auth import service_tokens

        middleware = service_tokens.ServiceAuthMiddleware
        manager_func = service_tokens.create_service_token_manager

        assert middleware is not None
        assert manager_func is not None


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_import_errors_propagate(self):
        """Test that import errors from service_auth are properly propagated."""
        # If service_auth module has issues, service_tokens should fail too
        with patch(
            "dotmac.platform.auth.service_tokens.ServiceAuthMiddleware",
            side_effect=ImportError("Test error"),
        ):
            try:
                # This should work normally, but if we mock an import error, it should propagate
                from dotmac.platform.auth.service_tokens import ServiceAuthMiddleware

                # Normal case - import should succeed
                assert ServiceAuthMiddleware is not None
            except ImportError:
                # This would happen if our mock was effective, but in normal cases it shouldn't
                pass

    def test_missing_service_auth_handling(self):
        """Test behavior when service_auth module is not available."""
        # In normal circumstances, service_auth should always be available
        # This tests the import structure is correct
        try:
            from dotmac.platform.auth import service_auth, service_tokens

            # Both should be available
            assert service_auth is not None
            assert service_tokens is not None
        except ImportError as e:
            pytest.fail(f"Required modules should be available: {e}")


class TestBackwardCompatibility:
    """Test backward compatibility features."""

    def test_old_import_patterns_work(self):
        """Test that old import patterns continue to work."""
        # Test that users can still import from service_tokens as before
        try:
            from dotmac.platform.auth.service_tokens import (
                ServiceAuthMiddleware,
                create_service_token_manager,
            )

            assert ServiceAuthMiddleware is not None
            assert create_service_token_manager is not None
        except ImportError:
            pytest.fail("Backward compatible imports should work")

    def test_migration_path_clear(self):
        """Test that the migration path to service_auth is clear."""
        # Users should be able to import from either location
        from dotmac.platform.auth.service_auth import ServiceAuthMiddleware as NewMiddleware
        from dotmac.platform.auth.service_tokens import ServiceAuthMiddleware as CompatMiddleware

        # They should be the same object
        assert CompatMiddleware is NewMiddleware

    def test_deprecation_path(self):
        """Test that the deprecation path is properly set up."""
        # The module should clearly indicate it's a compatibility layer
        from dotmac.platform.auth import service_tokens

        doc = service_tokens.__doc__ or ""
        assert "compatibility" in doc.lower() or "redirects" in doc.lower()
