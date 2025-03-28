from django.urls import path

from dashboards.views import (
    DashboardView,
    save_dashboard,
    load_dashboard,
    load_widget_config,
    load_widget_data,
    render_widget_data,
)

urlpatterns = [
    path("", DashboardView.as_view(), name="home"),
    path("ajax/save_dashboard", save_dashboard, name="save_dashboard"),
    path("ajax/load_dashboard", load_dashboard, name="load_dashboard"),
    path(
        "ajax/load_widget_data/<widget_id>", load_widget_data, name="load_widget_data"
    ),
    path(
        "ajax/load_widget_config/<widget_type>",
        load_widget_config,
        name="load_widget_config",
    ),
    path(
        "ajax/render_widget_config/<widget_type>",
        render_widget_data,
        name="render_widget_data",
    ),
]
