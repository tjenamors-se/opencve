from django.template.loader import render_to_string

from cves.search import Search
from views.models import View


class Widget:
    def __init__(self, widget_id, config, user):
        self.id = widget_id
        self.config = config
        self.user = user

    def render(self):
        raise NotImplementedError


class ViewWidget(Widget):
    def render(self):
        view = View.objects.filter(id=self.config["view_id"]).first()
        cves = Search(view.query, self.user).query.all()[:20]
        return render_to_string(
            "dashboards/widgets/view.html", {"query": view.query, "cves": cves}
        )


class FooWidget(Widget):
    def render(self):
        return render_to_string(
            "dashboards/widgets/foo.html", {"foo_objects": ["a", "b"]}
        )


class BarWidget(Widget):
    def render(self):
        return render_to_string(
            "dashboards/widgets/bar.html", {"bar_objects": ["c", "d"]}
        )
