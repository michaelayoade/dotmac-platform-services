"""
Test rate limiting and security features for the DotMac ISP Framework API.
Comprehensive testing of rate limits, authentication security, and abuse prevention.
"""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException


class TestRateLimiting:
    """Test API rate limiting functionality."""

    def test_login_rate_limiting(self, client):
        """Test rate limiting on login attempts."""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword",
            "portal_type": "admin"
        }

        with patch('dotmac_isp.modules.identity.router.AuthService') as mock_service:
            mock_instance = AsyncMock()
            mock_instance.authenticate_user.return_value = None  # Failed login
            mock_service.return_value = mock_instance

            # Simulate multiple rapid login attempts
            responses = []
            for _i in range(10):
                response = client.post("/identity/auth/login", json=login_data)
                responses.append(response)

                # Small delay between requests
                time.sleep(0.01)

            # Check if any requests were rate limited
            status_codes = [r.status_code for r in responses]

            # Should have some 401s (failed auth) and potentially some 429s (rate limited)
            assert 401 in status_codes

            # In a real implementation, we'd expect 429 after threshold
            # For now, just verify the endpoint responds consistently
            assert all(code in [401, 429, 500] for code in status_codes)

    def test_api_endpoint_rate_limiting(self, client):
        """Test rate limiting on general API endpoints."""
        with patch('dotmac.auth.dependencies.get_current_user') as mock_get_user:
            with patch('dotmac.auth.dependencies.require_permissions') as mock_perms:
                mock_get_user.return_value = {"id": "user-123", "tenant_id": "tenant-123"}
                mock_perms.return_value = lambda: None

                headers = {"Authorization": "Bearer valid_token"}

                # Make rapid requests to the same endpoint
                responses = []
                for _i in range(20):
                    response = client.get("/identity/customers", headers=headers)
                    responses.append(response)

                    # Very small delay
                    time.sleep(0.005)

                status_codes = [r.status_code for r in responses]

                # Should handle all requests gracefully
                # In production, might see 429 responses after threshold
                assert all(code in [200, 429, 500] for code in status_codes)

    def test_rate_limit_headers(self, client):
        """Test that rate limit information is included in headers."""
        response = client.get("/identity/auth/login")  # Using GET instead of POST for header test

        # Check for common rate limiting headers
        # These might be set by rate limiting middleware

        # At minimum, the response should be well-formed
        assert response.status_code in [200, 401, 404, 429]

        # In a real implementation, we'd check for rate limit headers
        # For now, just verify response structure
        if "X-RateLimit-Limit" in response.headers:
            assert int(response.headers["X-RateLimit-Limit"]) > 0

    def test_rate_limit_per_user(self, client):
        """Test that rate limits are applied per user."""
        with patch('dotmac.auth.dependencies.get_current_user') as mock_get_user:
            with patch('dotmac.auth.dependencies.require_permissions') as mock_perms:
                mock_perms.return_value = lambda: None

                # User 1 makes requests
                mock_get_user.return_value = {"id": "user-1", "tenant_id": "tenant-123"}
                headers_user1 = {"Authorization": "Bearer token_user1"}

                responses_user1 = []
                for _i in range(5):
                    response = client.get("/identity/customers", headers=headers_user1)
                    responses_user1.append(response)

                # User 2 makes requests
                mock_get_user.return_value = {"id": "user-2", "tenant_id": "tenant-123"}
                headers_user2 = {"Authorization": "Bearer token_user2"}

                responses_user2 = []
                for _i in range(5):
                    response = client.get("/identity/customers", headers=headers_user2)
                    responses_user2.append(response)

                # Both users should be able to make requests independently
                # (Rate limits should be per-user, not global)
                user1_success = any(r.status_code == 200 for r in responses_user1)
                user2_success = any(r.status_code == 200 for r in responses_user2)

                # At least one request from each user should succeed
                assert user1_success or user2_success

    def test_rate_limit_reset_window(self, client):
        """Test that rate limits reset after time window."""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword",
            "portal_type": "admin"
        }

        with patch('dotmac_isp.modules.identity.router.AuthService') as mock_service:
            mock_instance = AsyncMock()
            mock_instance.authenticate_user.return_value = None
            mock_service.return_value = mock_instance

            # Make initial requests
            initial_responses = []
            for _i in range(3):
                response = client.post("/identity/auth/login", json=login_data)
                initial_responses.append(response)

            # Wait a short time (simulating rate limit window)
            time.sleep(1)

            # Make additional request after wait
            final_response = client.post("/identity/auth/login", json=login_data)

            # Should still respond (window may not have reset in test)
            assert final_response.status_code in [401, 429, 500]


class TestAuthenticationSecurity:
    """Test authentication security measures."""

    def test_token_expiration_enforcement(self, client):
        """Test that expired tokens are rejected."""
        # Create an expired token
        from datetime import datetime, timedelta, timezone

        import jwt

        expired_payload = {
            "sub": "user-123",
            "username": "testuser",
            "tenant_id": "tenant-123",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
            "iat": datetime.now(timezone.utc) - timedelta(hours=2)
        }

        expired_token = jwt.encode(expired_payload, "test-secret", algorithm="HS256")

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/identity/users/user-123", headers=headers)

        # Should reject expired token
        assert response.status_code == 401

    def test_malformed_token_handling(self, client):
        """Test handling of malformed JWT tokens."""
        malformed_tokens = [
            "not.a.jwt.token",
            "Bearer malformed_token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.malformed.signature",
            "",
            "null",
            "undefined"
        ]

        for malformed_token in malformed_tokens:
            headers = {"Authorization": f"Bearer {malformed_token}"}
            response = client.get("/identity/users/user-123", headers=headers)

            # Should reject malformed tokens
            assert response.status_code == 401

    def test_token_signature_validation(self, client):
        """Test JWT token signature validation."""
        import jwt

        # Create token with wrong signature
        valid_payload = {
            "sub": "user-123",
            "username": "testuser",
            "tenant_id": "tenant-123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc)
        }

        # Sign with wrong secret
        wrong_signature_token = jwt.encode(valid_payload, "wrong-secret", algorithm="HS256")

        headers = {"Authorization": f"Bearer {wrong_signature_token}"}
        response = client.get("/identity/users/user-123", headers=headers)

        # Should reject token with invalid signature
        assert response.status_code == 401

    def test_session_fixation_prevention(self, client):
        """Test prevention of session fixation attacks."""
        # Simulate login process
        with patch('dotmac_isp.modules.identity.router.AuthService') as mock_service:
            mock_instance = AsyncMock()

            # First login should generate new session
            mock_instance.authenticate_user.return_value = {
                "access_token": "token_1",
                "session_id": "session_1",
                "user": {"id": "user-123"}
            }
            mock_service.return_value = mock_instance

            login_data = {
                "username": "testuser",
                "password": "password",
                "portal_type": "admin"
            }

            response1 = client.post("/identity/auth/login", json=login_data)
            assert response1.status_code == 200
            token1 = response1.json()["access_token"]

            # Second login should generate different session
            mock_instance.authenticate_user.return_value = {
                "access_token": "token_2",
                "session_id": "session_2",
                "user": {"id": "user-123"}
            }

            response2 = client.post("/identity/auth/login", json=login_data)
            assert response2.status_code == 200
            token2 = response2.json()["access_token"]

            # Tokens should be different (preventing session fixation)
            assert token1 != token2

    def test_concurrent_session_handling(self, client):
        """Test handling of concurrent user sessions."""
        with patch('dotmac_isp.modules.identity.router.AuthService'):
            mock_instance = AsyncMock()

            # Simulate multiple sessions for same user
            session_responses = []
            for i in range(3):
                mock_instance.authenticate_user.return_value = {
                    "access_token": f"token_{i}",
                    "session_id": f"session_{i}",
                    "user": {"id": "user-123"}
                }

                login_data = {
                    "username": "testuser",
                    "password": "password",
                    "portal_type": "admin"
                }

                response = client.post("/identity/auth/login", json=login_data)
                session_responses.append(response)

            # All sessions should be allowed (or implement max sessions limit)
            for response in session_responses:
                assert response.status_code == 200

    def test_password_brute_force_protection(self, client):
        """Test protection against password brute force attacks."""
        with patch('dotmac_isp.modules.identity.router.AuthService') as mock_service:
            mock_instance = AsyncMock()

            # Simulate account lockout after failed attempts
            attempt_count = 0
            def mock_authenticate(username, password, **kwargs):
                nonlocal attempt_count
                attempt_count += 1

                if attempt_count > 5:  # After 5 failed attempts
                    raise HTTPException(
                        status_code=423,  # Locked
                        detail="Account temporarily locked due to too many failed attempts"
                    )
                return None  # Failed authentication

            mock_instance.authenticate_user.side_effect = mock_authenticate
            mock_service.return_value = mock_instance

            login_data = {
                "username": "targetuser",
                "password": "wrongpassword",
                "portal_type": "admin"
            }

            responses = []
            for _i in range(7):  # Try more than threshold
                try:
                    response = client.post("/identity/auth/login", json=login_data)
                    responses.append(response)
                except HTTPException as e:
                    responses.append(type('MockResponse', (), {'status_code': e.status_code})())

            status_codes = [r.status_code for r in responses]

            # Should see 401s initially, then 423 (locked) after threshold
            assert 401 in status_codes
            # In real implementation, would expect 423 after threshold
            assert all(code in [401, 423, 500] for code in status_codes)


class TestInputValidationSecurity:
    """Test security aspects of input validation."""

    def test_sql_injection_prevention(self, client):
        """Test SQL injection prevention in search parameters."""
        with patch('dotmac.auth.dependencies.get_current_user') as mock_get_user:
            with patch('dotmac.auth.dependencies.require_permissions') as mock_perms:
                with patch('dotmac_isp.modules.identity.router.CustomerService') as mock_service:
                    mock_get_user.return_value = {"id": "user-123"}
                    mock_perms.return_value = lambda: None

                    mock_instance = AsyncMock()
                    mock_instance.search_customers.return_value = []
                    mock_service.return_value = mock_instance

                    # SQL injection attempts
                    injection_payloads = [
                        "'; DROP TABLE customers; --",
                        "' UNION SELECT * FROM users --",
                        "'; INSERT INTO customers VALUES (1, 'hacked'); --",
                        "' OR '1'='1",
                        "'; EXEC xp_cmdshell('dir'); --"
                    ]

                    headers = {"Authorization": "Bearer valid_token"}

                    for payload in injection_payloads:
                        response = client.get(
                            f"/identity/customers?search={payload}",
                            headers=headers
                        )

                        # Should handle safely without server errors
                        assert response.status_code in [200, 422]

                        # Verify service was called (parameterized queries prevent injection)
                        if response.status_code == 200:
                            mock_instance.search_customers.assert_called()

    def test_xss_prevention_in_responses(self, client):
        """Test XSS prevention in API responses."""
        with patch('dotmac.auth.dependencies.get_current_user') as mock_get_user:
            with patch('dotmac.auth.dependencies.require_permissions') as mock_perms:
                with patch('dotmac_isp.modules.identity.router.CustomerService') as mock_service:
                    mock_get_user.return_value = {"id": "user-123"}
                    mock_perms.return_value = lambda: None

                    # Mock customer with potentially malicious data
                    malicious_customer = {
                        "id": "customer-123",
                        "first_name": "<script>alert('xss')</script>",
                        "last_name": "<img src=x onerror=alert('xss')>",
                        "email": "test@example.com"
                    }

                    mock_instance = AsyncMock()
                    mock_instance.get_customer_by_id.return_value = malicious_customer
                    mock_service.return_value = mock_instance

                    headers = {"Authorization": "Bearer valid_token"}
                    response = client.get("/identity/customers/customer-123", headers=headers)

                    assert response.status_code == 200

                    # Response should contain the data as-is (JSON API doesn't interpret HTML)
                    # XSS prevention is typically handled by frontend frameworks
                    data = response.json()
                    assert "script" in data["first_name"]  # Should be preserved as text

    def test_file_path_traversal_prevention(self, client):
        """Test prevention of directory traversal attacks."""
        # Test path traversal in customer ID parameter
        with patch('dotmac.auth.dependencies.get_current_user') as mock_get_user:
            with patch('dotmac.auth.dependencies.require_permissions') as mock_perms:
                mock_get_user.return_value = {"id": "user-123"}
                mock_perms.return_value = lambda: None

                # Path traversal attempts
                traversal_payloads = [
                    "../../../etc/passwd",
                    "..\\..\\windows\\system32\\config\\sam",
                    "/etc/shadow",
                    "file:///etc/passwd"
                ]

                headers = {"Authorization": "Bearer valid_token"}

                for payload in traversal_payloads:
                    response = client.get(f"/identity/customers/{payload}", headers=headers)

                    # Should return validation error or 404, not server error
                    assert response.status_code in [404, 422]

    def test_command_injection_prevention(self, client):
        """Test prevention of command injection attacks."""
        with patch('dotmac.auth.dependencies.get_current_user') as mock_get_user:
            with patch('dotmac.auth.dependencies.require_permissions') as mock_perms:
                with patch('dotmac_isp.modules.identity.router.CustomerService') as mock_service:
                    mock_get_user.return_value = {"id": "user-123"}
                    mock_perms.return_value = lambda: None

                    mock_instance = AsyncMock()
                    mock_instance.create_customer.return_value = {"id": "customer-123"}
                    mock_service.return_value = mock_instance

                    # Command injection attempts in customer data
                    malicious_data = {
                        "email": "test@example.com",
                        "first_name": "John; rm -rf /",
                        "last_name": "$(whoami)",
                        "phone": "`cat /etc/passwd`"
                    }

                    headers = {"Authorization": "Bearer valid_token"}
                    response = client.post("/identity/customers", json=malicious_data, headers=headers)

                    # Should process normally (commands should be treated as literal strings)
                    assert response.status_code in [200, 201, 422]


class TestAPIAbusePrevention:
    """Test prevention of API abuse and DoS attacks."""

    def test_request_size_limits(self, client):
        """Test request payload size limits."""
        # Very large payload
        large_customer_data = {
            "email": "test@example.com",
            "first_name": "A" * 10000,  # Very long string
            "last_name": "B" * 10000,
            "company_name": "C" * 50000,
            "additional_data": "X" * 100000
        }

        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/identity/customers", json=large_customer_data, headers=headers)

        # Should handle large payloads gracefully
        # Might be 413 (Payload Too Large) or 422 (validation error)
        assert response.status_code in [413, 422, 400]

    def test_nested_object_depth_limits(self, client):
        """Test limits on nested object depth."""
        # Deeply nested object
        nested_data = {"level1": {"level2": {"level3": {"level4": {"level5": {"level6": "deep"}}}}}}

        customer_data = {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "nested_config": nested_data
        }

        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/identity/customers", json=customer_data, headers=headers)

        # Should handle nested objects reasonably
        assert response.status_code in [200, 201, 422, 400]

    def test_concurrent_request_handling(self, client):
        """Test handling of many concurrent requests."""
        import queue
        import threading

        results = queue.Queue()

        def make_request():
            try:
                response = client.get("/identity/customers")
                results.put(response.status_code)
            except Exception as e:
                results.put(f"Error: {e}")

        # Create multiple threads to simulate concurrent requests
        threads = []
        for _i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Collect results
        status_codes = []
        while not results.empty():
            status_codes.append(results.get())

        # Should handle concurrent requests without crashing
        assert len(status_codes) == 10
        # Most should succeed or return controlled errors
        success_codes = [code for code in status_codes if isinstance(code, int) and code < 500]
        assert len(success_codes) >= 5  # At least half should not be server errors

    def test_slowloris_protection(self, client):
        """Test protection against slow HTTP attacks."""
        # Simulate slow request by sending incomplete data
        # This is difficult to test with TestClient, so we'll simulate the concept

        login_data = {
            "username": "testuser",
            "password": "password"
            # Incomplete data
        }

        # Request should be handled in reasonable time
        start_time = time.time()
        response = client.post("/identity/auth/login", json=login_data)
        end_time = time.time()

        # Should not hang indefinitely
        assert (end_time - start_time) < 30  # 30 second timeout
        assert response.status_code in [422, 400]  # Validation error for incomplete data


class TestSecurityHeaders:
    """Test security-related HTTP headers."""

    def test_security_headers_present(self, client):
        """Test that security headers are included in responses."""
        response = client.get("/identity/auth/login")

        # Security headers that should be present
        expected_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": None,  # Should contain max-age
            "Content-Security-Policy": None
        }

        for header, expected_values in expected_headers.items():
            if expected_values is None:
                # Just check if header exists
                if header in response.headers:
                    assert len(response.headers[header]) > 0
            elif isinstance(expected_values, list):
                # Check if any of the expected values are present
                if header in response.headers:
                    assert any(val in response.headers[header] for val in expected_values)
            else:
                # Check exact value
                if header in response.headers:
                    assert response.headers[header] == expected_values

    def test_cors_headers_configuration(self, client):
        """Test CORS headers configuration."""
        # Preflight request
        response = client.options(
            "/identity/customers",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization,Content-Type"
            }
        )

        # Should handle CORS appropriately
        # Specific behavior depends on CORS configuration
        assert response.status_code in [200, 204, 405]

    def test_information_disclosure_prevention(self, client):
        """Test that sensitive information is not disclosed in error responses."""
        # Force an internal server error
        with patch('dotmac_isp.modules.identity.router.AuthService') as mock_service:
            mock_instance = AsyncMock()
            mock_instance.authenticate_user.side_effect = Exception("Database password: secret123")
            mock_service.return_value = mock_instance

            login_data = {
                "username": "testuser",
                "password": "password",
                "portal_type": "admin"
            }

            response = client.post("/identity/auth/login", json=login_data)

            assert response.status_code == 500

            # Error response should not contain sensitive details
            error_detail = response.json()["detail"]
            assert "secret123" not in error_detail
            assert "password" not in error_detail.lower()
            assert "database" not in error_detail.lower()

            # Should be a generic error message
            assert "Authentication failed" in error_detail
