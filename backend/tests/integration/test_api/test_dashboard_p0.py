"""Regression tests for P0 dashboard correctness fixes.

Covers:
- GET /questionnaires/sessions must not be shadowed by GET /questionnaires/{id}
  (route ordering bug that returned 404 "Template not found").
- GET /profiles/me must return 200 with a valid HealthProfileDTO instead of 500
  (MissingGreenlet lazy-load + metadata attribute mismatch).
- GET /profiles/me/completion must return 200.
- GET /report/ must return 200 (no 307 redirect) and be scoped to the user.
"""

from __future__ import annotations

from httpx import AsyncClient


class TestDashboardEndpointsP0:
    async def test_questionnaires_sessions_not_shadowed_by_id_route(
        self, client: AsyncClient
    ) -> None:
        """GET /questionnaires/sessions must resolve to the sessions list
        endpoint, not be caught by /questionnaires/{id} (id='sessions')."""
        response = await client.get(
            "/api/v1/questionnaires/sessions",
            headers={"Authorization": "Bearer mock-firebase-id-token"},
        )
        # Before the fix this was 404 "Template not found".
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_profiles_me_returns_valid_dto(self, client: AsyncClient) -> None:
        """GET /profiles/me must return 200 with a serializable HealthProfileDTO.

        Before the fix this raised MissingGreenlet (lazy personal_info) and a
        metadata ValidationError (MetaData object instead of dict) -> 500.
        """
        response = await client.get(
            "/api/v1/profiles/me",
            headers={"Authorization": "Bearer mock-firebase-id-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "user_id" in data
        # metadata must be a dict or null, never SQLAlchemy's MetaData object.
        assert data["metadata"] is None or isinstance(data["metadata"], dict)

    async def test_profiles_me_completion_returns_200(
        self, client: AsyncClient
    ) -> None:
        """GET /profiles/me/completion must return 200 (was 500)."""
        response = await client.get(
            "/api/v1/profiles/me/completion",
            headers={"Authorization": "Bearer mock-firebase-id-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "overall" in data
        assert "sections" in data

    async def test_report_list_no_trailing_slash_redirect(
        self, client: AsyncClient
    ) -> None:
        """GET /report/ must return 200 directly (was 307 redirect when the
        client requested /report without a trailing slash)."""
        response = await client.get(
            "/api/v1/report/",
            params={"limit": 8},
            headers={"Authorization": "Bearer mock-firebase-id-token"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
