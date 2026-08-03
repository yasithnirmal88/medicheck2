from __future__ import annotations

from datetime import datetime

from app.domain.entities.user import User


class TestUserEntity:
    def test_create_user(self) -> None:
        user = User.create(
            firebase_uid="firebase-123",
            email="test@example.com",
            full_name="John Doe",
        )

        assert user.firebase_uid == "firebase-123"
        assert user.email == "test@example.com"
        assert user.full_name == "John Doe"
        assert user.is_active is True
        assert user.email_verified is False
        assert user.avatar_url is None
        assert user.last_login_at is None
        assert user.deleted_at is None
        assert user.is_deleted is False
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_create_user_with_avatar(self) -> None:
        user = User.create(
            firebase_uid="firebase-456",
            email="jane@example.com",
            full_name="Jane Doe",
            avatar_url="https://example.com/avatar.jpg",
        )

        assert user.avatar_url == "https://example.com/avatar.jpg"

    def test_deactivate_user(self) -> None:
        user = User.create(
            firebase_uid="firebase-789",
            email="test@example.com",
            full_name="Test User",
        )

        assert user.is_active is True
        user.deactivate()
        assert user.is_active is False

    def test_activate_user(self) -> None:
        user = User.create(
            firebase_uid="firebase-101",
            email="test@example.com",
            full_name="Test User",
        )

        user.deactivate()
        assert user.is_active is False

        user.activate()
        assert user.is_active is True

    def test_mark_login(self) -> None:
        user = User.create(
            firebase_uid="firebase-111",
            email="test@example.com",
            full_name="Test User",
        )

        assert user.last_login_at is None
        user.mark_login()
        assert user.last_login_at is not None

    def test_update_profile_full_name(self) -> None:
        user = User.create(
            firebase_uid="firebase-222",
            email="test@example.com",
            full_name="Old Name",
        )

        user.update_profile(full_name="New Name")
        assert user.full_name == "New Name"

    def test_update_profile_avatar(self) -> None:
        user = User.create(
            firebase_uid="firebase-333",
            email="test@example.com",
            full_name="Test User",
        )

        user.update_profile(avatar_url="https://example.com/new-avatar.jpg")
        assert user.avatar_url == "https://example.com/new-avatar.jpg"

    def test_update_profile_both(self) -> None:
        user = User.create(
            firebase_uid="firebase-444",
            email="test@example.com",
            full_name="Original",
            avatar_url="https://example.com/old.jpg",
        )

        user.update_profile(
            full_name="Updated",
            avatar_url="https://example.com/new.jpg",
        )
        assert user.full_name == "Updated"
        assert user.avatar_url == "https://example.com/new.jpg"

    def test_soft_delete(self) -> None:
        user = User.create(
            firebase_uid="firebase-555",
            email="test@example.com",
            full_name="Test User",
        )

        user.soft_delete()
        assert user.is_deleted is True
        assert user.deleted_at is not None
        assert user.is_active is False

    def test_to_dict(self) -> None:
        user = User.create(
            firebase_uid="firebase-666",
            email="test@example.com",
            full_name="Test User",
        )

        data = user.to_dict()
        assert data["firebase_uid"] == "firebase-666"
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert data["is_active"] is True
        assert data["deleted_at"] is None

    def test_email_normalization(self) -> None:
        user = User.create(
            firebase_uid="firebase-777",
            email="  TEST@Example.COM  ",
            full_name="Test User",
        )

        assert user.email == "test@example.com"

    def test_full_name_strip(self) -> None:
        user = User.create(
            firebase_uid="firebase-888",
            email="test@example.com",
            full_name="  Spaced Name  ",
        )

        assert user.full_name == "Spaced Name"
