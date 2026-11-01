from enum import Enum


class Permission(str, Enum):
    USERS_READ = "users:read"
    USERS_MANAGE = "users:manage"
    EVENTS_READ = "events:read"
    EVENTS_WRITE = "events:write"
    ALERTS_READ = "alerts:read"
    ALERTS_MANAGE = "alerts:manage"
    CASES_READ = "cases:read"
    CASES_MANAGE = "cases:manage"
    DETECTIONS_READ = "detections:read"
    DETECTIONS_MANAGE = "detections:manage"
    REPORTS_READ = "reports:read"
    REPORTS_MANAGE = "reports:manage"
    AUDIT_READ = "audit:read"
    SETTINGS_MANAGE = "settings:manage"


ROLE_PERMISSIONS = {
    "ADMIN": {
        Permission.USERS_READ,
        Permission.USERS_MANAGE,
        Permission.EVENTS_READ,
        Permission.EVENTS_WRITE,
        Permission.ALERTS_READ,
        Permission.ALERTS_MANAGE,
        Permission.CASES_READ,
        Permission.CASES_MANAGE,
        Permission.DETECTIONS_READ,
        Permission.DETECTIONS_MANAGE,
        Permission.REPORTS_READ,
        Permission.REPORTS_MANAGE,
        Permission.AUDIT_READ,
        Permission.SETTINGS_MANAGE,
    },
    "SOC_ANALYST": {
        Permission.EVENTS_READ,
        Permission.EVENTS_WRITE,
        Permission.ALERTS_READ,
        Permission.ALERTS_MANAGE,
        Permission.CASES_READ,
        Permission.CASES_MANAGE,
        Permission.DETECTIONS_READ,
        Permission.REPORTS_READ,
        Permission.REPORTS_MANAGE,
    },
    "SECURITY_VIEWER": {
        Permission.EVENTS_READ,
        Permission.ALERTS_READ,
        Permission.CASES_READ,
        Permission.DETECTIONS_READ,
        Permission.REPORTS_READ,
    },
}

LEGACY_ROLE_MAP = {
    "Administrator": "ADMIN",
    "Admin": "ADMIN",
    "administrator": "ADMIN",
    "Analyst": "SOC_ANALYST",
    "analyst": "SOC_ANALYST",
    "Viewer": "SECURITY_VIEWER",
    "viewer": "SECURITY_VIEWER",
}


def normalize_role(role: str | None) -> str:
    if role in ROLE_PERMISSIONS:
        return role
    return LEGACY_ROLE_MAP.get(role or "", "SECURITY_VIEWER")


def has_permission(role: str | None, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(normalize_role(role), set())
