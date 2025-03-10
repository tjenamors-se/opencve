import json
import random

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import TemplateView


from dashboards.models import DashboardConfig
from dashboards.widgets import FooWidget, BarWidget, ViewWidget


WIDGET_CLASSES = {"foo": FooWidget, "bar": BarWidget, "view": ViewWidget}


class DashboardView(TemplateView):
    template_name = "dashboards/index.html"


@login_required
def save_dashboard(request):
    if request.method == "POST":
        user = request.user

        dashboard_config, _ = DashboardConfig.objects.get_or_create(user=user)
        dashboard_config.config = json.loads(request.body)
        dashboard_config.save()

        return JsonResponse({"message": "dashboard saved"}, status=200)

    return JsonResponse({"error": "method not allowed"}, status=405)


@login_required
def load_dashboard(request):
    dashboard = DashboardConfig.objects.get(user=request.user)

    widgets = []
    for widget in dashboard.config:
        config = widget["config"]

        widget_class = WIDGET_CLASSES.get(widget["type"])
        if widget_class:
            html = widget_class(widget["id"], config, request.user).render()
            widgets.append({**widget, "content": html})

    return JsonResponse({"dashboard": widgets})


@login_required
def load_widget_data(request, widget_id):
    dashboard = DashboardConfig.objects.get(user=request.user)
    widget = next((w for w in dashboard.config if w["id"] == widget_id), None)
    print("ici")
    print(widget)
    print("la")
    import time

    time.sleep(random.randint(0, 3))
    widget_class = WIDGET_CLASSES.get(widget["type"])
    html = ""
    if widget_class:
        html = widget_class(widget["id"], widget["config"], request.user).render()

    return JsonResponse({"html": html})
