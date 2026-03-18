from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from ai_engine.engine import run_query, QueryEngineError
from query_runner.validator import InvalidSQLError
from query_runner.chart import detect_chart_type
from .models import QueryHistory
from .serializers import QueryHistorySerializer


class QueryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = (request.data.get("question") or "").strip()
        if not question:
            return Response({"errors": {"question": ["This field is required."]}}, status=400)

        try:
            sql_generated, results, explanation = run_query(question)
        except InvalidSQLError as e:
            return Response({"errors": {"query": [str(e)]}}, status=400)
        except QueryEngineError as e:
            return Response({"errors": {"question": [str(e)]}},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        chart_config = detect_chart_type(results["columns"], results["rows"])
        row_count = len(results["rows"])

        QueryHistory.objects.create(
            user=request.user,
            question=question,
            sql_generated=sql_generated,
            explanation=explanation,
            results=results,
            chart_config=chart_config,
            row_count=row_count,
        )

        # Keep only the latest 50 per user
        old_ids = list(
            QueryHistory.objects.filter(user=request.user)
            .values_list("id", flat=True)[50:]
        )
        if old_ids:
            QueryHistory.objects.filter(id__in=old_ids).delete()

        return Response({
            "question": question,
            "sql_generated": sql_generated,
            "explanation": explanation,
            "results": results,
            "chart_config": chart_config,
            "row_count": row_count,
        })


class HistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = QueryHistory.objects.filter(user=request.user)[:50]
        return Response({"results": QueryHistorySerializer(qs, many=True).data})
