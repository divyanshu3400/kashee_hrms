from channels.generic.websocket import WebsocketConsumer
import json
from asgiref.sync import async_to_sync


class NotificationConsumer(WebsocketConsumer):
    
    def connect(self):
        if self.scope["user"].is_anonymous:
            self.close()
        else:
            self.group_name = str(self.scope["user"].pk)  # Setting the group name as the pk of the user primary key as it is unique to each user. The group name is used to communicate with the user.
            async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
            self.accept()

    def disconnect(self, close_code):
        self.close()

    def notify(self, event):
        rejected_by = event["rejected_by"]
        message = f"Leave Rejected by: {rejected_by.username}"
        data = event["text"]
        notification = {
            'message': message,
            'data': data
        }
        print(data)
        self.send(text_data=json.dumps(notification))