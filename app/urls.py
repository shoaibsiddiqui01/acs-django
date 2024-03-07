# myapp/urls.py
from django.urls import path
from .views import auth , source ,search , test , sites , site_details


urlpatterns = [
    path('login/', auth.LoginView.as_view(), name='login'),
    path('source/', source.SourceView().as_view(), name='source'),
    path('search/', search.SearchView().as_view(), name='search'),
    path('sites-by-collections/', sites.SitesView.as_view(), name='sites-by-collections'),
    path('sites-details/', site_details.SourceDetailsView.as_view(), name='sites-details'),
    path('test/', test.TestView().as_view(), name='test'),
]
