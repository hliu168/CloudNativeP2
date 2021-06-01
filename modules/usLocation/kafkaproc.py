from app.udaconnect.services import KafkaService
from app import create_app
import os

app = create_app(os.getenv("FLASK_ENV") or "test")
with app.app_context():
    KafkaService.recvLocations()