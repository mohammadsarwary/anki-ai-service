from django.core.paginator import Paginator
from rest_framework.response import Response


def paginated_response(queryset, serializer_class, request, per_page=15):
    paginator = Paginator(queryset, per_page)
    page = paginator.get_page(request.query_params.get("page") or 1)
    data = serializer_class(page.object_list, many=True).data
    return Response(
        {
            "success": True,
            "data": data,
            "meta": {
                "current_page": page.number,
                "total": paginator.count,
                "per_page": per_page,
                "last_page": paginator.num_pages,
            },
        }
    )
