import json
import random

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.generic import TemplateView


from dashboards.models import Dashboard
from dashboards.widgets import Widget


def list_widgets():
    return {
        w.id: {
            "type": w.id,
            "name": w.name,
            "description": w.description,
            "class": w,
        }
        for w in Widget.__subclasses__()
    }


class DashboardView(TemplateView):
    template_name = "dashboards/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["widgets"] = list_widgets().values()
        return context


@login_required
def save_dashboard(request):
    if request.method == "POST":
        dashboard_config, _ = Dashboard.objects.get_or_create(
            organization=request.current_organization
        )
        dashboard_config.config = json.loads(request.body)
        dashboard_config.save()

        return JsonResponse({"message": "dashboard saved"}, status=200)

    return JsonResponse({"error": "method not allowed"}, status=405)


@login_required
def load_dashboard(request):
    dashboard = Dashboard.objects.get(organization=request.current_organization)
    return JsonResponse({"widgets": dashboard.config})


@login_required
def load_widget_data(request, widget_id):
    dashboard = Dashboard.objects.get(organization=request.current_organization)
    widget = next((w for w in dashboard.config if w["id"] == widget_id), None)

    # To remove
    import time

    time.sleep(random.randint(0, 3))

    widget_class = list_widgets().get(widget["type"])["class"]

    html = ""
    if widget_class:
        html = widget_class(widget["type"], widget["config"], request).render()

    return JsonResponse({"html": html})
