# appfactory/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Product  # Giả sử bạn có model Product

class ProductConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Lấy product_id từ URL
        self.product_id = self.scope['url_route']['kwargs']['product_id']

        print("Client connected to WebSocket")
        print(f"Product Code: {self.product_code}")

        self.room_group_name = f"product_{self.product_id}"

        # Tạo một group cho WebSocket
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept kết nối
        await self.accept()

    async def disconnect(self, close_code):
        # Hủy kết nối WebSocket
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Nhận dữ liệu từ WebSocket
    async def receive(self, text_data):
        print(f"Received data: {text_data}")
        
        # Trong trường hợp này bạn có thể gửi thông tin sản phẩm đến client
        product = Product.objects.get(id=self.product_id)
        product_data = {
            'name': product.name,
            'details': product.details
        }

        # Gửi dữ liệu tới WebSocket
        await self.send(text_data=json.dumps({
            'product': product_data
        }))
