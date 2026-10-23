"""Future authorized government-system integration contract. No external endpoint is called."""
from typing import Protocol
from dataclasses import dataclass
@dataclass(frozen=True)
class IntegrationReceipt:
    reference: str
    mode: str
    message: str
class GrievanceAdapter(Protocol):
    def submit(self, public_case_id: str, payload: dict) -> IntegrationReceipt: ...
class DemoAdapter:
    def submit(self, public_case_id: str, payload: dict) -> IntegrationReceipt:
        return IntegrationReceipt(public_case_id,"LOCAL_DEMO_ONLY","No government service was contacted")
class AuthorizedAdapterRequired:
    def submit(self, public_case_id: str, payload: dict) -> IntegrationReceipt:
        raise PermissionError("Official credentials, API specification and authorization are required")
