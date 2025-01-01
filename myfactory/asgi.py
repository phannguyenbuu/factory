import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path  # Thêm import này
from appfactory.consumers import ProductConsumer  # Import consumer
from django.urls import re_path  # Thay vì path, bạn có thể sử dụng re_path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myfactory.settings')
print("Using settings:", os.getenv('DJANGO_SETTINGS_MODULE'))

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            # Định nghĩa URL với product_id
            re_path(r'ws/update/(?P<product_id>\d+)/$', ProductConsumer.as_asgi()),  # Đây là nơi lấy product_id từ URL
        ])
    ),
})
