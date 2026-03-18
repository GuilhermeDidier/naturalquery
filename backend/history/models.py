from django.db import models
from django.contrib.auth.models import User


class QueryHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="queries")
    question = models.TextField()
    sql_generated = models.TextField()
    explanation = models.TextField()
    results = models.JSONField()          # {"columns": [...], "rows": [...]}
    chart_config = models.JSONField(null=True, blank=True)
    row_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
