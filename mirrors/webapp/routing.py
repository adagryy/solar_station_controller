# chat/routing.py
from django.conf.urls import url

from .webSocketConsumers import parametersPreviewConsumer

websocket_urlpatterns = [
    url(r'^parametersPreview/$', parametersPreviewConsumer.ParametersConsumer),
]