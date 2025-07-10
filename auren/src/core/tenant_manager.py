import hashlib
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class TenantContext:
    tenant_id: str
    redis_namespace: str
    vector_index: str


class TenantManager:
    """Manages multi-tenant isolation for AUREN instances"""

    def __init__(self):
        self.tenant_map: Dict[str, str] = {}
        self.active_tenants: Dict[str, TenantContext] = {}

    def get_tenant_context(self, phone_number: str) -> TenantContext:
        """Get or create tenant context for a phone number"""
        tenant_id = hashlib.sha256(phone_number.encode()).hexdigest()[:12]

        if tenant_id not in self.active_tenants:
            self.active_tenants[tenant_id] = TenantContext(
                tenant_id=tenant_id,
                redis_namespace=f"auren:{tenant_id}",
                vector_index=f"conversations_{tenant_id}",
            )

        return self.active_tenants[tenant_id]
