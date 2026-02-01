from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import django_rq
from rq.job import Job

from django.http import HttpRequest, JsonResponse

from arbitrage_agent.core.logic import ask_agent

class StartAnalysisView(APIView):
    def post(self, request: HttpRequest) -> Response:
        user_query = request.data.get("query")
        if not user_query:
            return JsonResponse({"error": "Query is required"}, status=status.HTTP_400_BAD_REQUEST)

        job = ask_agent.delay(user_query)
        return JsonResponse({
            "task_id": job.id,
            "status": "queued",
            "message": "Analysis started."
        })

class TaskStatusView(APIView):
    def get(self, request: HttpRequest, task_id: str) -> Response:
        redis_conn = django_rq.get_connection('default')

        try:
            job = Job.fetch(task_id, connection=redis_conn)
        except Exception:
            return JsonResponse({"status": "error", "message": "Job not found"}, status=404)

        if job.is_finished:
            return JsonResponse({
                "status": "completed",
                "data": job.result
            })
        elif job.is_failed:
            return JsonResponse({
                "status": "failed",
                "error": str(job.exc_info)
            })
        else:
            return JsonResponse({
                "status": job.get_status(),
            })
