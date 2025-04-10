from django.db import models
from django.template.loader import render_to_string

from changes.models import Change, Report
from cves.search import Search
from views.models import View


class Widget:
    def __init__(self, request, data):
        self.id = data["id"]
        self.type = data["type"]
        self.request = request
        self.configuration = data["config"]

    def index(self):
        return self.render_index()

    def config(self):
        return self.render_config()

    def render_index(self, **kwargs):
        return render_to_string(
            f"dashboards/widgets/{self.type}/index.html",
            {
                "widget_id": self.id,
                "widget_type": self.type,
                "request": self.request,
                **kwargs,
            },
        )

    def render_config(self, **kwargs):
        return render_to_string(
            f"dashboards/widgets/{self.type}/config.html",
            {
                "widget_id": self.id,
                "widget_type": self.type,
                "config": self.configuration,
                "request": self.request,
                **kwargs,
            },
        )


class ActivityWidget(Widget):
    id = "activity"
    name = "CVE Activity"
    description = "Displays the most recent CVE changes across all projects."

    def index(self):
        # Get the queryset similar to ChangeListView
        query = Change.objects.select_related("cve")

        # Filter on user subscriptions if needed
        activities_view = self.configuration.get("activities_view", "all")
        if activities_view == "subscriptions":
            vendors = self.request.current_organization.get_projects_vendors()
            if vendors:
                query = query.filter(cve__vendors__has_any_keys=vendors)

        # Get the last 10 changes
        changes = query.order_by("-created_at")[:10]

        return self.render_index(changes=changes)


class ViewsWidget(Widget):
    id = "views"
    name = "Saved Views"
    description = (
        "Shows the list of your private views and your organization’s public views."
    )

    def index(self):
        views = View.objects.filter(
            models.Q(privacy="public", organization=self.request.current_organization)
            | models.Q(
                privacy="private",
                user=self.request.user,
                organization=self.request.current_organization,
            )
        ).order_by("privacy")
        return self.render_index(views=views)


class ViewCvesWidget(Widget):
    id = "view_cves"
    name = "CVEs by View"
    description = "Displays CVEs associated with a selected saved view."

    def config(self):
        # TODO: Move this query to a shared function since it’s used in multiple places
        views = View.objects.filter(
            models.Q(privacy="public", organization=self.request.current_organization)
            | models.Q(
                privacy="private",
                user=self.request.user,
                organization=self.request.current_organization,
            )
        )
        return self.render_config(views=views)

    def index(self):
        view = View.objects.filter(id=self.configuration["view_id"]).first()
        cves = Search(view.query, self.request.user).query.all()[:20]
        return self.render_index(view=view, cves=cves)


class TagsWidget(Widget):
    id = "tags"
    name = "User Tags"
    description = "Shows the list of tags you created to categorize CVEs."

    def index(self):
        tags = self.request.user.tags.all()
        return self.render_index(tags=tags)


class ProjectsWidget(Widget):
    id = "projects"
    name = "Projects"
    description = "Displays the list of projects within your organization."

    def index(self):
        organization = self.request.current_organization
        projects = organization.projects.all()
        return self.render_index(
            organization=organization, projects=projects.order_by("name")
        )


class LastReportsWidget(Widget):
    id = "last_reports"
    name = "Recent Reports"
    description = (
        "Displays the latest CVE reports generated for your organization’s projects."
    )

    def index(self):
        organization = self.request.current_organization
        projects = organization.projects.all()

        reports = (
            Report.objects.filter(project__in=projects)
            .prefetch_related("changes")
            .select_related("project")
            .order_by("-day")[:10]
        )
        return self.render_index(organization=organization, reports=reports)
