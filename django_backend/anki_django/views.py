from __future__ import annotations

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.views import View


class ApiTesterView(View):
    def get(self, request):
        if not settings.DEBUG and not request.user.is_staff:
            raise Http404()
        return render(request, "api_tester.html")
