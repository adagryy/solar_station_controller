from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
import redis
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
class ParametersConsumer(WebsocketConsumer):    
    def connect(self):
        # self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'workingParams_preview'
        self.user = self.scope["user"]
        # At the beginning check if user is authenticated
        if self.user.is_authenticated:
            # Next acquire reference to data store
            self.redisDbReference = redis.Redis(host='localhost', port=6379, db=0)

            # Join room group
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )
        
            self.accept()
            logger.error('Zaakceptowano WebSocket ' + str(self.user.is_authenticated))
        else:
            self.close()
            logger.error('Odrzucono WebSocket '  + str(self.user.is_authenticated))

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'right_sensor_temperature': str(self.redisDbReference.get('right_sensor_temperature'), 'utf-8'),
                'middle_sensor_temperature': str(self.redisDbReference.get('middle_sensor_temperature'), 'utf-8'),
                'left_sensor_temperature': str(self.redisDbReference.get('left_sensor_temperature'), 'utf-8'),
                'tank_sensor_temperature': str(self.redisDbReference.get('tank_sensor_temperature'), 'utf-8')
            }
        )

    # Receive message from room group
    def chat_message(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps(event))