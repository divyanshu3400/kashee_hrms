from channels.routing import ProtocolTypeRouter
import os
from django.core.asgi import get_asgi_application
from .routing import route_application  # Correct import

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kashee.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": route_application, 
})
