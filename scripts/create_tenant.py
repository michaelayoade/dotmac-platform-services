#!/usr/bin/env python
"""Create default tenant and assign to admin user."""

import requests

# Login
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login", json={"username": "admin", "password": "Admin123!@#"}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Create tenant
tenant_data = {
    "name": "Default Organization",
    "slug": "default-org",
    "settings": {"theme": "blue", "features": ["analytics", "reporting"]},
}

tenant_response = requests.post(
    "http://localhost:8000/api/v1/tenants", headers=headers, json=tenant_data
)

if tenant_response.status_code in [200, 201]:
    tenant = tenant_response.json()
    print(f"✅ Created tenant: {tenant['id']} - {tenant['name']}")
    print(f"   Slug: {tenant['slug']}")
elif tenant_response.status_code == 409:
    print("✅ Tenant already exists")
else:
    print(f"❌ Failed to create tenant: {tenant_response.status_code}")
    print(tenant_response.text)
