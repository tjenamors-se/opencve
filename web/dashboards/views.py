import json
import random

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import TemplateView


from dashboards.models import Dashboard
from dashboards.widgets import ViewsWidget, ViewCvesWidget


WIDGET_CLASSES = {"views": ViewsWidget, "view_cves": ViewCvesWidget}


class DashboardView(TemplateView):
    template_name = "dashboards/index.html"


@login_required
def save_dashboard(request):
    if request.method == "POST":
        user = request.user

        dashboard_config, _ = Dashboard.objects.get_or_create(user=user)
        dashboard_config.config = json.loads(request.body)
        dashboard_config.save()

        return JsonResponse({"message": "dashboard saved"}, status=200)

    return JsonResponse({"error": "method not allowed"}, status=405)


@login_required
def load_dashboard(request):
    dashboard = Dashboard.objects.get(organization=request.current_organization)

    widgets = []
    for widget in dashboard.config:
        config = widget["config"]

        widget_class = WIDGET_CLASSES.get(widget["type"])
        if widget_class:
            html = widget_class(widget["id"], config, request).render()
            widgets.append({**widget, "content": html})

    return JsonResponse({"dashboard": widgets})


@login_required
def load_widget_data(request, widget_id):
    dashboard = Dashboard.objects.get(organization=request.current_organization)
    widget = next((w for w in dashboard.config if w["id"] == widget_id), None)

    # To remove
    import time

    time.sleep(random.randint(0, 3))

    widget_class = WIDGET_CLASSES.get(widget["type"])
    html = ""
    if widget_class:
        html = widget_class(widget["id"], widget["config"], request).render()

    return JsonResponse({"html": html})
