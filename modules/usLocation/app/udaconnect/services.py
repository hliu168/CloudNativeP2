import logging
from datetime import datetime, timedelta
from typing import Dict, List

from app import db
from app.udaconnect.models import Location
from app.udaconnect.schemas import LocationSchema
from geoalchemy2.functions import ST_AsText, ST_Point
from sqlalchemy.sql import text

from kafka import KafkaProducer, KafkaConsumer

import json

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("udaconnect-api")

class LocationService:

    @staticmethod
    def retrieve_all() -> List[Location]:
        return db.session.query(Location).all()

    @staticmethod
    def retrieve(location_id) -> Location:
        location, coord_text = (
            db.session.query(Location, Location.coordinate.ST_AsText())
            .filter(Location.id == location_id)
            .one()
        )

        # Rely on database to return text form of point to reduce overhead of conversion in app code
        location.wkt_shape = coord_text
        return location

    @staticmethod
    def create(location: Dict) -> Location:
        validation_results: Dict = LocationSchema().validate(location)
        if validation_results:
            logger.warning(f"Unexpected data format in payload: {validation_results}")
            raise Exception(f"Invalid payload: {validation_results}")

        new_location = Location()
        new_location.person_id = location["person_id"]
        if location.get("creation_time") is not None:
            new_location.creation_time = location["creation_time"]
        else:
            new_location.creation_time = None
        new_location.coordinate = ST_Point(location["latitude"], location["longitude"])
        db.session.add(new_location)
        db.session.commit()

        return new_location

class KafkaService:

    TOPIC_NAME = 'locations'
    KAFKA_SERVER = 'kafka-service:9092'

    @staticmethod
    def sendLocation(location_data):
        KAFKA_PRODUCER = KafkaProducer(bootstrap_servers=KafkaService.KAFKA_SERVER)
        kafka_data = json.dumps(location_data).encode()
        KAFKA_PRODUCER.send(KafkaService.TOPIC_NAME, kafka_data)
        KAFKA_PRODUCER.flush()
        return location_data

    @staticmethod
    def recvLocations(): 
        KAFKA_CONSUMER = KafkaConsumer(KafkaService.TOPIC_NAME, bootstrap_servers=KafkaService.KAFKA_SERVER)
        for location in KAFKA_CONSUMER:
            locationJson = json.loads(location.value.decode('utf-8'))
            print(locationJson)
            new_location = Location()
            new_location.person_id = locationJson["person_id"]
            new_location.coordinate = ST_Point(locationJson["latitude"], locationJson["longitude"])
            db.session.add(new_location)
            db.session.commit()
