import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
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


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboards/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["widgets"] = sorted(list_widgets().values(), key=lambda x: x["name"])
        return context


@login_required
def load_dashboard(request):
    dashboard = Dashboard.objects.filter(
        organization=request.current_organization, user=request.user, is_default=True
    ).first()

    if not dashboard:
        dashboard = Dashboard.objects.create(
            organization=request.current_organization,
            user=request.user,
            name="Mon Dashboard",
            is_default=True,
            config=Dashboard.get_default_config(),
        )

    return JsonResponse({"data": dashboard.config})


@login_required
def load_widget_data(request, widget_id):
    dashboard = Dashboard.objects.get(organization=request.current_organization)
    widget_config = next((w for w in dashboard.config if w["id"] == widget_id), None)
    widget_class = list_widgets().get(widget_config["type"])["class"]

    html = ""
    if widget_class:
        html = widget_class(request, widget_config).index()

    return JsonResponse({"html": html})


@login_required
def render_widget_data(request, widget_type):
    widget_class = list_widgets().get(widget_type)["class"]

    html = ""
    if widget_class:
        widget_config = {
            "id": None,
            "type": widget_type,
            "config": json.loads(request.POST.get("config", "{}")),
        }
        html = widget_class(request, widget_config).index()

    return JsonResponse({"html": html})


class LoadWidgetConfigView(LoginRequiredMixin, View):
    def post(self, request, widget_type):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)

        widget_class = list_widgets().get(widget_type)["class"]
        if not widget_class:
            return JsonResponse({"error": "Invalid widget type"}, status=400)

        widget_config = {
            "id": None,
            "type": widget_type,
            "config": {"title": data.get("title"), **data.get("config", {})},
        }

        html = widget_class(request, widget_config).config()
        return JsonResponse({"html": html})


@login_required
def load_widget_config(request, widget_type):
    widget_class = list_widgets().get(widget_type)["class"]

    html = ""
    if widget_class:
        widget_config = {
            "id": None,
            "type": widget_type,
            "config": {},
        }
        html = widget_class(request, widget_config).config()

    return JsonResponse({"html": html})


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
