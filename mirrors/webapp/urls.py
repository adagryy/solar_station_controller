from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^df/$', views.index, name='index'),
    url(r'^drawChart/$', views.chartData, name='chartData'),
    url(r'^parameters/$', views.parameters, name='parameters'),
    url(r'^management/$', views.mirrormanagement, name='management'),
]
