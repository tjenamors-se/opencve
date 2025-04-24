import pytest
from bs4 import BeautifulSoup
from django.test import override_settings
from django.urls import reverse
from unittest.mock import patch
import uuid

from dashboards.widgets import list_widgets
from dashboards.models import Dashboard
from dashboards.views import SaveDashboardView  # Import SaveDashboardView


@override_settings(ENABLE_ONBOARDING=False)
@pytest.mark.django_db
def test_dashboard_view_context(client, auth_client, create_user):
    """
    Test that DashboardView correctly passes the sorted list of widgets to the template context.
    """
    # Test unauthenticated access
    response = client.get(reverse("home"))
    assert response.status_code == 302
    assert reverse("account_login") in response.url

    user = create_user()
    client = auth_client(user)
    response = client.get(reverse("home"))

    # Assertions
    assert response.status_code == 200
    assert response.template_name == ["dashboards/index.html"]
    assert "widgets" in response.context

    expected_widgets = sorted(list_widgets().values(), key=lambda x: x["name"])
    assert response.context["widgets"] == expected_widgets

    soup = BeautifulSoup(response.content, features="html.parser")
    assert [
        n.text.split("\n")[0]
        for n in soup.find("div", {"id": "modal-add-widget"}).find_all(
            "strong", {"class": "product-title"}
        )
    ] == [w["name"] for w in expected_widgets]


@override_settings(ENABLE_ONBOARDING=False)
@pytest.mark.django_db
@patch("dashboards.models.uuid.uuid4")
def test_load_dashboard_view(
    mock_uuid4, client, auth_client, create_user, create_organization
):
    """
    Test that LoadDashboardView returns the correct dashboard config.
    """
    mock_uuid4.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")

    # Check unauthenticated access
    load_url = reverse("load_dashboard")
    login_url = reverse("account_login")
    response = client.get(load_url)
    assert response.status_code == 302
    assert login_url in response.url

    user = create_user()
    organization = create_organization(name="Test Org", user=user)
    client = auth_client(user)

    # Check default dashboard
    response = client.get(reverse("load_dashboard"))
    dashboard = Dashboard.objects.get(
        organization=organization, user=user, is_default=True
    )
    expected_config = Dashboard.get_default_config(client.request().wsgi_request)

    assert response.status_code == 200
    assert response.json() == expected_config
    assert dashboard.config == expected_config

    # Check existing dashboard
    custom_config = {"widgets": [{"id": "custom-widget", "type": "test"}]}
    dashboard.config = custom_config
    dashboard.save()

    response = client.get(reverse("load_dashboard"))
    assert response.status_code == 200
    assert response.json() == custom_config
    assert (
        Dashboard.objects.filter(
            organization=organization, user=user, is_default=True
        ).count()
        == 1
    )


@override_settings(ENABLE_ONBOARDING=False)
@pytest.mark.django_db
def test_save_dashboard_validate_widgets_config(
    auth_client, create_user, create_organization
):
    """
    Test the static method validate_widgets_config in SaveDashboardView.
    """
    user = create_user()
    client = auth_client(user)
    organization = create_organization(name="Test Org", user=user)

    request = client.request().wsgi_request
    request.current_organization = organization
    request.user = user

    valid_uuid = str(uuid.uuid4())

    # Valid configuration
    valid_widgets = [
        {"id": valid_uuid, "type": "tags", "title": "My Tags", "config": {}},
        {
            "id": str(uuid.uuid4()),
            "type": "activity",
            "title": "Activity",
            "config": {"activities_view": "all"},
        },
    ]
    is_clean, result = SaveDashboardView.validate_widgets_config(request, valid_widgets)
    assert is_clean is True
    assert len(result) == 2
    assert result[0]["id"] == valid_uuid
    assert result[0]["type"] == "tags"
    assert result[0]["config"] == {}  # TagsWidget cleans config
    assert result[1]["type"] == "activity"
    assert result[1]["config"] == {"activities_view": "all"}

    # Invalid Widget ID
    invalid_id_widgets = [
        {"id": "not-a-uuid", "type": "tags", "title": "Invalid Tags", "config": {}},
    ]
    is_clean, result = SaveDashboardView.validate_widgets_config(
        request, invalid_id_widgets
    )
    assert is_clean is False
    assert result == "Incorrect configuration"

    # Invalid Widget Type
    invalid_type_widgets = [
        {
            "id": str(uuid.uuid4()),
            "type": "invalid_type",
            "title": "Invalid Type",
            "config": {},
        },
    ]
    is_clean, result = SaveDashboardView.validate_widgets_config(
        request, invalid_type_widgets
    )
    assert is_clean is False
    assert result == "Invalid widget type"

    # Invalid Widget Config (ActivityWidget)
    invalid_config_widgets = [
        {
            "id": str(uuid.uuid4()),
            "type": "activity",
            "title": "Invalid Activity Config",
            "config": {"activities_view": "invalid_value"},
        },
    ]
    is_clean, result = SaveDashboardView.validate_widgets_config(
        request, invalid_config_widgets
    )
    assert is_clean is False
    assert result == "Incorrect configuration"
