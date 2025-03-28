import json
from django.urls import reverse
from bs4 import BeautifulSoup
from unittest.mock import patch

from dashboards.models import Dashboard


def test_dashboard_view(create_organization, create_user, auth_client):
    user = create_user()
    create_organization(name="org", user=user)
    client = auth_client(user)

    response = client.get(reverse("home"))
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, features="html.parser")
    assert soup.find("h1", {"class": "navbar-title"}).text == "Dashboard"


def test_load_dashboard(
    create_organization, create_user, create_dashboard, auth_client
):
    user = create_user()
    org = create_organization(name="org", user=user)
    client = auth_client(user)

    dashboard_config = [
        {
            "h": 4,
            "w": 4,
            "x": 0,
            "y": 0,
            "id": "fe149a36-28ad-482d-aacb-11345de5f972",
            "type": "tags",
            "title": "Last tags",
            "config": {"foo": "bar"},
        }
    ]
    create_dashboard(organization=org, config=dashboard_config)

    response = client.get(reverse("load_dashboard"))
    assert response.status_code == 200
    assert response.json() == {"data": dashboard_config}


@patch("dashboards.widgets.TagsWidget.render")
def test_load_widget_data(
    mock_render, create_organization, create_user, create_dashboard, auth_client
):
    mock_render.return_value = "<div>Mocked HTML</div>"

    user = create_user()
    org = create_organization(name="org", user=user)
    client = auth_client(user)

    dashboard_config = [
        {
            "h": 4,
            "w": 4,
            "x": 0,
            "y": 0,
            "id": "fe149a36-28ad-482d-aacb-11345de5f972",
            "type": "tags",
            "title": "Last tags",
            "config": {"foo": "bar"},
        }
    ]
    create_dashboard(organization=org, config=dashboard_config)

    response = client.get(
        reverse(
            "load_widget_data",
            kwargs={"widget_id": "fe149a36-28ad-482d-aacb-11345de5f972"},
        )
    )
    assert response.status_code == 200
    assert response.json() == {"html": "<div>Mocked HTML</div>"}
    mock_render.assert_called_once()


@patch("dashboards.widgets.TagsWidget.render")
def test_render_widget_data(mock_render, create_organization, create_user, auth_client):
    mock_render.return_value = "<div>Mocked HTML</div>"

    user = create_user()
    create_organization(name="org", user=user)
    client = auth_client(user)

    config = {"key": "value"}
    response = client.post(
        reverse(
            "render_widget_data",
            kwargs={"widget_type": "tags"},
        ),
        data={"config": json.dumps(config)},
    )
    assert response.status_code == 200
    assert response.json() == {"html": "<div>Mocked HTML</div>"}


@patch("dashboards.widgets.TagsWidget.configure")
def test_load_widget_config(
    mock_configure, create_organization, create_user, auth_client
):
    mock_configure.return_value = "<div>Mocked Config HTML</div>"

    user = create_user()
    create_organization(name="org", user=user)
    client = auth_client(user)

    response = client.get(
        reverse(
            "load_widget_config",
            kwargs={"widget_type": "tags"},
        )
    )
    assert response.status_code == 200
    assert response.json() == {"html": "<div>Mocked Config HTML</div>"}
    mock_configure.assert_called_once()


def test_save_dashboard(create_organization, create_user, auth_client):
    user = create_user()
    org = create_organization(name="org", user=user)
    client = auth_client(user)

    dashboard_config = [
        {
            "h": 4,
            "w": 4,
            "x": 0,
            "y": 0,
            "id": "fe149a36-28ad-482d-aacb-11345de5f972",
            "type": "tags",
            "title": "Last tags",
            "config": {"foo": "bar"},
        }
    ]

    response = client.post(
        reverse("save_dashboard"),
        data=json.dumps(dashboard_config),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json() == {"message": "dashboard saved"}

    # Verify the dashboard was saved
    dashboard = Dashboard.objects.get(organization=org)
    assert dashboard.config == dashboard_config


def test_save_dashboard_invalid_method(create_organization, create_user, auth_client):
    user = create_user()
    create_organization(name="org", user=user)
    client = auth_client(user)

    response = client.get(reverse("save_dashboard"))
    assert response.status_code == 405
    assert response.json() == {"error": "method not allowed"}


def test_login_required(client):
    # Test dashboard view
    response = client.get(reverse("home"))
    assert response.status_code == 302
    assert response.url.startswith("/login/")

    # Test load dashboard
    response = client.get(reverse("load_dashboard"))
    assert response.status_code == 302
    assert response.url.startswith("/login/")

    # Test load widget data
    response = client.get(
        reverse(
            "load_widget_data",
            kwargs={"widget_id": "fe149a36-28ad-482d-aacb-11345de5f972"},
        )
    )
    assert response.status_code == 302
    assert response.url.startswith("/login/")

    # Test render widget data
    response = client.post(
        reverse(
            "render_widget_data",
            kwargs={"widget_type": "tags"},
        ),
        data={"config": json.dumps({"key": "value"})},
    )
    assert response.status_code == 302
    assert response.url.startswith("/login/")

    # Test load widget config
    response = client.get(
        reverse(
            "load_widget_config",
            kwargs={"widget_type": "tags"},
        )
    )
    assert response.status_code == 302
    assert response.url.startswith("/login/")

    # Test save dashboard
    response = client.post(
        reverse("save_dashboard"),
        data=json.dumps({"widgets": []}),
        content_type="application/json",
    )
    assert response.status_code == 302
    assert response.url.startswith("/login/")
