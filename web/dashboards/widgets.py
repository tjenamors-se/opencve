from datetime import timedelta

from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone

from changes.models import Change, Report
from cves.search import Search
from views.models import View


class Widget:
    def __init__(self, request, data):
        self.id = data["id"]
        self.type = data["type"]
        self.request = request
        self.config = data["config"]

    def render(self, **kwargs):
        raise NotImplementedError

    def configure(self):
        raise NotImplementedError

    def render_template(self, **kwargs):
        return render_to_string(
            f"dashboards/widgets/{self.type}.html",
            {"widget_id": self.id, "widget_type": self.type, **kwargs},
        )


class ActivityWidget(Widget):
    id = "activity"
    name = "Activity Feed"
    description = "Display the feed of CVEs changes"

    def configure(self):
        return render_to_string(
            "dashboards/widgets/activity_config.html", {"config": self.config}
        )

    def render(self):
        # Get the queryset similar to ChangeListView
        query = Change.objects.select_related("cve")

        # Filter on user subscriptions if needed
        activities_view = self.config.get("activities_view", "all")
        if activities_view == "subscriptions":
            vendors = self.request.current_organization.get_projects_vendors()
            if vendors:
                query = query.filter(cve__vendors__has_any_keys=vendors)

        # Get changes from the last 7 days
        seven_days_ago = timezone.now() - timedelta(days=7)
        changes = query.order_by("-created_at")[:10]
        print(changes)

        return render_to_string(
            "dashboards/widgets/activity.html",
            {
                "changes": changes,
                "user": self.request.user,
            },
        )


class ViewsWidget(Widget):
    id = "views"
    name = "List of views"
    description = "Display a list of public and private views."

    def render(self):
        views = View.objects.filter(
            models.Q(privacy="public", organization=self.request.current_organization)
            | models.Q(
                privacy="private",
                user=self.request.user,
                organization=self.request.current_organization,
            )
        ).order_by("privacy")
        return self.render_template(views=views)


class ViewCvesWidget(Widget):
    id = "view_cves"
    name = "View CVEs"
    description = "Display the CVEs related to a view."

    def configure(self):
        # TODO: factoriser cette requete utilisée à 3 endroits
        views = View.objects.filter(
            models.Q(privacy="public", organization=self.request.current_organization)
            | models.Q(
                privacy="private",
                user=self.request.user,
                organization=self.request.current_organization,
            )
        )
        return render_to_string(
            "dashboards/widgets/view_cves_config.html", {"views": views}
        )

    def render(self):
        view = View.objects.filter(id=self.config["view_id"]).first()
        cves = Search(view.query, self.request.user).query.all()[:20]
        return self.render_template(view=view, cves=cves)


class TagsWidget(Widget):
    id = "tags"
    name = "List of tags"
    description = "Display list of Tags"

    def render(self):
        tags = self.request.user.tags.all()
        return self.render_template(tags=tags)


class ProjectsWidget(Widget):
    id = "projects"
    name = "List of projects"
    description = "Display list of Projects"

    def render(self):
        organization = self.request.current_organization
        projects = organization.projects.all()
        return self.render_template(
            organization=organization, projects=projects.order_by("name")
        )


class LastReportsWidget(Widget):
    id = "last_reports"
    name = "Last Reports"
    description = "Display the last reports of all projects"

    def render(self):
        organization = self.request.current_organization
        projects = organization.projects.all()

        reports = (
            Report.objects.filter(project__in=projects)
            .prefetch_related("changes")
            .select_related("project")
            .order_by("-day")[:10]
        )
        return self.render_template(organization=organization, reports=reports)
