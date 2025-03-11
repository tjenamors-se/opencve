from django.db import models

from opencve.models import BaseModel
from organizations.models import Organization


class Dashboard(BaseModel):
    organization = models.OneToOneField(
        Organization, on_delete=models.CASCADE, related_name="dashboard"
    )
    config = models.JSONField(default=dict)

    class Meta:
        db_table = "opencve_dashboards"
