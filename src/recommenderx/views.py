from django.http import HttpResponse

def home_page_view(request, *args, **kwargs):

    return HttpResponse("Hello, world. You're at the RecommenderX home page.")