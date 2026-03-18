from rest_framework import serializers
from .models import QueryHistory


class QueryHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryHistory
        fields = ["id", "question", "sql_generated", "explanation", "results",
                  "chart_config", "row_count", "created_at"]
