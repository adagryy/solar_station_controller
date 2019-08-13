from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^df/$', views.index, name='index'),
    url(r'^login/$', views.login_user, name='loginuser'),
    url(r'^logout/$', views.logout_user, name='logoutuser'),
]
