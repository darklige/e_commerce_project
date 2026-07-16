from enum import StrEnum


class AccountType(StrEnum):
    CUSTOMER = "customer"
    MERCHANT = "merchant"
    ADMIN = "admin"


class Role(StrEnum):
    CUSTOMER = "customer"
    MEMBER_CUSTOMER = "member_customer"
    ENTERPRISE_CUSTOMER = "enterprise_customer"
    MERCHANT_OWNER = "merchant_owner"
    MERCHANT_PRODUCT_OPERATOR = "merchant_product_operator"
    MERCHANT_ORDER_SUPPORT = "merchant_order_support"
    MERCHANT_WAREHOUSE = "merchant_warehouse"
    MERCHANT_FINANCE = "merchant_finance"
    ADMIN_SUPER = "admin_super"
    ADMIN_OPERATOR = "admin_operator"
    ADMIN_CUSTOMER_SERVICE = "admin_customer_service"
    ADMIN_CUSTOMER_SERVICE_LEAD = "admin_customer_service_lead"
    ADMIN_RISK = "admin_risk"
    ADMIN_FINANCE = "admin_finance"
    ADMIN_TECH = "admin_tech"
    AUDIT_READONLY = "audit_readonly"


class Permission(StrEnum):
    USER_PROFILE_READ = "user:profile:read"
    ADMIN_CONSOLE_ACCESS = "admin:console:access"
    MERCHANT_CONSOLE_ACCESS = "merchant:console:access"
    AUDIT_READ = "audit:read"
    RBAC_MANAGE = "rbac:manage"


ROLE_ACCOUNT_TYPES: dict[Role, set[AccountType]] = {
    Role.CUSTOMER: {AccountType.CUSTOMER},
    Role.MEMBER_CUSTOMER: {AccountType.CUSTOMER},
    Role.ENTERPRISE_CUSTOMER: {AccountType.CUSTOMER},
    Role.MERCHANT_OWNER: {AccountType.MERCHANT},
    Role.MERCHANT_PRODUCT_OPERATOR: {AccountType.MERCHANT},
    Role.MERCHANT_ORDER_SUPPORT: {AccountType.MERCHANT},
    Role.MERCHANT_WAREHOUSE: {AccountType.MERCHANT},
    Role.MERCHANT_FINANCE: {AccountType.MERCHANT},
    Role.ADMIN_SUPER: {AccountType.ADMIN},
    Role.ADMIN_OPERATOR: {AccountType.ADMIN},
    Role.ADMIN_CUSTOMER_SERVICE: {AccountType.ADMIN},
    Role.ADMIN_CUSTOMER_SERVICE_LEAD: {AccountType.ADMIN},
    Role.ADMIN_RISK: {AccountType.ADMIN},
    Role.ADMIN_FINANCE: {AccountType.ADMIN},
    Role.ADMIN_TECH: {AccountType.ADMIN},
    Role.AUDIT_READONLY: {AccountType.ADMIN},
}


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.CUSTOMER: {Permission.USER_PROFILE_READ},
    Role.MEMBER_CUSTOMER: {Permission.USER_PROFILE_READ},
    Role.ENTERPRISE_CUSTOMER: {Permission.USER_PROFILE_READ},
    Role.MERCHANT_OWNER: {
        Permission.USER_PROFILE_READ,
        Permission.MERCHANT_CONSOLE_ACCESS,
        Permission.RBAC_MANAGE,
    },
    Role.MERCHANT_PRODUCT_OPERATOR: {
        Permission.USER_PROFILE_READ,
        Permission.MERCHANT_CONSOLE_ACCESS,
    },
    Role.MERCHANT_ORDER_SUPPORT: {
        Permission.USER_PROFILE_READ,
        Permission.MERCHANT_CONSOLE_ACCESS,
    },
    Role.MERCHANT_WAREHOUSE: {
        Permission.USER_PROFILE_READ,
        Permission.MERCHANT_CONSOLE_ACCESS,
    },
    Role.MERCHANT_FINANCE: {
        Permission.USER_PROFILE_READ,
        Permission.MERCHANT_CONSOLE_ACCESS,
    },
    Role.ADMIN_SUPER: {
        Permission.USER_PROFILE_READ,
        Permission.ADMIN_CONSOLE_ACCESS,
        Permission.AUDIT_READ,
        Permission.RBAC_MANAGE,
    },
    Role.ADMIN_OPERATOR: {Permission.USER_PROFILE_READ, Permission.ADMIN_CONSOLE_ACCESS},
    Role.ADMIN_CUSTOMER_SERVICE: {
        Permission.USER_PROFILE_READ,
        Permission.ADMIN_CONSOLE_ACCESS,
    },
    Role.ADMIN_CUSTOMER_SERVICE_LEAD: {
        Permission.USER_PROFILE_READ,
        Permission.ADMIN_CONSOLE_ACCESS,
        Permission.AUDIT_READ,
    },
    Role.ADMIN_RISK: {Permission.USER_PROFILE_READ, Permission.ADMIN_CONSOLE_ACCESS},
    Role.ADMIN_FINANCE: {Permission.USER_PROFILE_READ, Permission.ADMIN_CONSOLE_ACCESS},
    Role.ADMIN_TECH: {
        Permission.USER_PROFILE_READ,
        Permission.ADMIN_CONSOLE_ACCESS,
        Permission.AUDIT_READ,
    },
    Role.AUDIT_READONLY: {Permission.USER_PROFILE_READ, Permission.AUDIT_READ},
}


ACCOUNT_DEFAULT_ROLE: dict[AccountType, Role] = {
    AccountType.CUSTOMER: Role.CUSTOMER,
    AccountType.MERCHANT: Role.MERCHANT_OWNER,
    AccountType.ADMIN: Role.ADMIN_SUPER,
}
