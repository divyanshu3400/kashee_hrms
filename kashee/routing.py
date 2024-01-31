from hrms.consumers import NotificationConsumer
from django.urls import path
import os
from django.core.asgi import get_asgi_application
from django.conf import settings
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kashee.settings')
django_asgi_app = get_asgi_application()
route_application = ProtocolTypeRouter({ 
    "http": django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                [
                    path("ws/notifications/", NotificationConsumer.as_asgi()),
                ]
            )
        ),
    ),
})
