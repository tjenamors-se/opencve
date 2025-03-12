from django.db import models
from django.template.loader import render_to_string

from changes.models import Report
from cves.search import Search
from views.models import View


class Widget:
    def __init__(self, type, config, request):
        self.type = type
        self.config = config
        self.request = request

    def render(self, **kwargs):
        raise NotImplementedError

    def render_template(self, **kwargs):
        return render_to_string(f"dashboards/widgets/{self.type}.html", kwargs)


class ViewsWidget(Widget):
    id = "views"
    name = "List of Views"
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
    name = "List of CVEs per view"
    description = "Display the CVEs related to a view."

    def render(self):
        view = View.objects.filter(id=self.config["view_id"]).first()
        cves = Search(view.query, self.request.user).query.all()[:20]
        return self.render_template(query=view.query, cves=cves)


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
