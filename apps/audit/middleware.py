# from threading import local

# _request_local = local()

# class AuditMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         _request_local.request = request
#         response = self.get_response(request)
#         return response

# def get_current_request():
#     return getattr(_request_local, 'request', None)