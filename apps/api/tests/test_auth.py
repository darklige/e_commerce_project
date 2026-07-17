from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.domains.identity.constants import AccountType, Role
from app.domains.identity.models import AuditLog, UserRole
from app.domains.identity.service import InvalidRoleAssignmentError, create_user


def register_customer(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "buyer@example.com",
            "password": "StrongerPass123!",
            "display_name": "Buyer",
        },
    )
    assert response.status_code == 201
    return response.json()


def login(client: TestClient, email: str, password: str, account_type: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password, "account_type": account_type},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_customer_register_login_and_read_me(client: TestClient) -> None:
    registered = register_customer(client)

    assert registered["email"] == "buyer@example.com"
    assert registered["roles"] == ["customer"]
    assert "user:profile:read" in registered["permissions"]

    token = login(client, "buyer@example.com", "StrongerPass123!", "customer")
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "buyer@example.com"


def test_role_specific_registration_and_console_access(
    client: TestClient,
    session: Session,
) -> None:
    customer_response = client.post(
        "/api/v1/auth/register/customer",
        json={
            "email": "buyer-v2@example.com",
            "password": "StrongerPass123!",
            "display_name": "Buyer V2",
        },
    )
    assert customer_response.status_code == 201
    assert customer_response.json()["console"] == "customer"
    assert customer_response.json()["user"]["account_type"] == "customer"

    merchant_response = client.post(
        "/api/v1/auth/register/merchant",
        json={
            "email": "merchant-signup@example.com",
            "password": "StrongerPass123!",
            "display_name": "Merchant Signup",
            "shop_name": "Northstar 演示店",
        },
    )
    assert merchant_response.status_code == 201
    assert merchant_response.json()["console"] == "merchant"
    assert merchant_response.json()["user"]["account_type"] == "merchant"
    assert merchant_response.json()["merchant_ids"]
    merchant_token = login(
        client,
        "merchant-signup@example.com",
        "StrongerPass123!",
        "merchant",
    )
    assert (
        client.get(
            "/api/v1/auth/merchant/me",
            headers={"Authorization": f"Bearer {merchant_token}"},
        ).status_code
        == 200
    )
    assert (
        client.get(
            "/api/v1/auth/admin/me",
            headers={"Authorization": f"Bearer {merchant_token}"},
        ).status_code
        == 403
    )

    forbidden_admin = client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "admin-signup@example.com",
            "password": "StrongerPass123!",
            "display_name": "Admin Signup",
            "invite_code": "wrong-code",
            "role": "admin_customer_service",
        },
    )
    assert forbidden_admin.status_code == 403

    admin_response = client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "admin-signup@example.com",
            "password": "StrongerPass123!",
            "display_name": "Admin Signup",
            "invite_code": "local-admin-invite-code",
            "role": "admin_customer_service",
        },
    )
    assert admin_response.status_code == 201
    assert admin_response.json()["console"] == "admin"
    admin_token = login(client, "admin-signup@example.com", "StrongerPass123!", "admin")
    assert (
        client.get(
            "/api/v1/auth/admin/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        ).status_code
        == 200
    )
    assert (
        client.get(
            "/api/v1/auth/merchant/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        ).status_code
        == 403
    )

    audit_logs = session.exec(select(AuditLog).where(AuditLog.action == "auth.register")).all()
    assert any(
        log.resource_type == "merchant_user" and log.outcome == "success"
        for log in audit_logs
    )
    assert any(log.resource_type == "admin_user" and log.outcome == "success" for log in audit_logs)


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    register_customer(client)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "buyer@example.com",
            "password": "StrongerPass123!",
            "display_name": "Buyer Again",
        },
    )

    assert response.status_code == 409


def test_register_rejects_extra_account_type(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin-self-service@example.com",
            "password": "StrongerPass123!",
            "display_name": "Sneaky",
            "account_type": "admin",
        },
    )

    assert response.status_code == 422


def test_password_reset_is_account_type_scoped_and_single_use(
    client: TestClient,
    session: Session,
) -> None:
    register_customer(client)

    wrong_type = client.post(
        "/api/v1/auth/password/forgot",
        json={"email": "buyer@example.com", "account_type": "merchant"},
    )
    assert wrong_type.status_code == 200
    assert wrong_type.json()["reset_token"] is None

    forgot_response = client.post(
        "/api/v1/auth/password/forgot",
        json={"email": "buyer@example.com", "account_type": "customer"},
    )
    assert forgot_response.status_code == 200
    reset_token = forgot_response.json()["reset_token"]
    assert reset_token

    invalid_reset = client.post(
        "/api/v1/auth/password/reset",
        json={
            "email": "buyer@example.com",
            "account_type": "merchant",
            "reset_token": reset_token,
            "new_password": "NewStrongerPass123!",
        },
    )
    assert invalid_reset.status_code == 400

    reset_response = client.post(
        "/api/v1/auth/password/reset",
        json={
            "email": "buyer@example.com",
            "account_type": "customer",
            "reset_token": reset_token,
            "new_password": "NewStrongerPass123!",
        },
    )
    assert reset_response.status_code == 200

    old_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "buyer@example.com",
            "password": "StrongerPass123!",
            "account_type": "customer",
        },
    )
    assert old_login.status_code == 401
    assert login(client, "buyer@example.com", "NewStrongerPass123!", "customer")

    reused_reset = client.post(
        "/api/v1/auth/password/reset",
        json={
            "email": "buyer@example.com",
            "account_type": "customer",
            "reset_token": reset_token,
            "new_password": "AnotherStrongerPass123!",
        },
    )
    assert reused_reset.status_code == 400

    audit_logs = session.exec(select(AuditLog)).all()
    assert any(log.action == "auth.password_reset_request" for log in audit_logs)
    assert any(
        log.action == "auth.password_reset" and log.outcome == "success"
        for log in audit_logs
    )


def test_invalid_login_writes_audit_log(client: TestClient, session: Session) -> None:
    register_customer(client)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "buyer@example.com",
            "password": "wrong-password",
            "account_type": "customer",
        },
    )

    assert response.status_code == 401
    audit_logs = session.exec(select(AuditLog).where(AuditLog.action == "auth.login")).all()
    assert any(log.outcome == "failure" for log in audit_logs)


def test_customer_cannot_access_admin_or_merchant_console(client: TestClient) -> None:
    register_customer(client)
    token = login(client, "buyer@example.com", "StrongerPass123!", "customer")
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/v1/auth/admin/me", headers=headers).status_code == 403
    assert client.get("/api/v1/auth/merchant/me", headers=headers).status_code == 403


def test_permission_denial_writes_audit_log(client: TestClient, session: Session) -> None:
    register_customer(client)
    token = login(client, "buyer@example.com", "StrongerPass123!", "customer")

    response = client.get(
        "/api/v1/auth/admin/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    audit_logs = session.exec(
        select(AuditLog).where(AuditLog.action == "auth.permission_denied")
    ).all()
    assert any(log.actor_user_id is not None for log in audit_logs)


def test_admin_can_access_admin_console(client: TestClient, session: Session) -> None:
    create_user(
        session,
        email="admin@example.com",
        password="StrongerPass123!",
        display_name="Admin",
        account_type=AccountType.ADMIN,
        roles=[Role.ADMIN_SUPER],
    )
    token = login(client, "admin@example.com", "StrongerPass123!", "admin")

    response = client.get("/api/v1/auth/admin/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["console"] == "admin"


def test_merchant_owner_can_access_merchant_console(client: TestClient, session: Session) -> None:
    merchant_id = uuid4()
    create_user(
        session,
        email="merchant@example.com",
        password="StrongerPass123!",
        display_name="Merchant",
        account_type=AccountType.MERCHANT,
        roles=[Role.MERCHANT_OWNER],
        merchant_id=merchant_id,
    )
    token = login(client, "merchant@example.com", "StrongerPass123!", "merchant")

    response = client.get("/api/v1/auth/merchant/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["console"] == "merchant"
    assert response.json()["merchant_ids"] == [str(merchant_id)]


def test_login_rejects_wrong_account_type(client: TestClient, session: Session) -> None:
    create_user(
        session,
        email="admin@example.com",
        password="StrongerPass123!",
        display_name="Admin",
        account_type=AccountType.ADMIN,
        roles=[Role.ADMIN_SUPER],
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "StrongerPass123!",
            "account_type": "customer",
        },
    )

    assert response.status_code == 401


def test_create_user_rejects_role_from_wrong_account_namespace(session: Session) -> None:
    with pytest.raises(InvalidRoleAssignmentError):
        create_user(
            session,
            email="not-admin@example.com",
            password="StrongerPass123!",
            display_name="Not Admin",
            account_type=AccountType.CUSTOMER,
            roles=[Role.ADMIN_SUPER],
        )


def test_admin_role_misassigned_to_customer_still_cannot_access_admin_console(
    client: TestClient,
    session: Session,
) -> None:
    user = create_user(
        session,
        email="misassigned@example.com",
        password="StrongerPass123!",
        display_name="Misassigned",
        account_type=AccountType.CUSTOMER,
    )
    session.add(UserRole(user_id=user.id, role=Role.ADMIN_SUPER))
    session.commit()
    token = login(client, "misassigned@example.com", "StrongerPass123!", "customer")

    response = client.get(
        "/api/v1/auth/admin/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_audit_log_truncates_user_controlled_fields(client: TestClient, session: Session) -> None:
    long_email = (
        f"{'a' * 63}@"
        f"{'b' * 50}."
        f"{'c' * 50}."
        f"{'d' * 10}.com"
    )
    user_agent = "M1-check/" + ("x" * 800)
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": long_email,
            "password": "wrong-password",
            "account_type": "customer",
        },
        headers={"user-agent": user_agent},
    )

    assert response.status_code == 401
    audit_log = session.exec(
        select(AuditLog).where(AuditLog.action == "auth.login")
    ).one()
    assert audit_log.resource_id == long_email.lower()
    assert len(audit_log.resource_id or "") <= 320
    assert len(audit_log.user_agent or "") <= 512
