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


class LocationInfoService:

    @staticmethod
    def findLocations(person_id, start_date, end_date):
        locations: List = db.session.query(Location).filter(
            Location.person_id == person_id
        ).filter(Location.creation_time < end_date).filter(
            Location.creation_time >= start_date
        ).all()
        return locations

    @staticmethod
    def findLocation(person_id, start_date, end_date, meters, latitude, longitude):
        data = {
                    "person_id": person_id,
                    "longitude": longitude,
                    "latitude": latitude,
                    "meters": meters,
                    "start_date": datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%d"),
                    "end_date": (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
                }
        query = text(
            """
        SELECT  person_id, id, ST_X(coordinate), ST_Y(coordinate), creation_time
        FROM    location
        WHERE   ST_DWithin(coordinate::geography,ST_SetSRID(ST_MakePoint(:latitude,:longitude),4326)::geography, :meters)
        AND     person_id != :person_id
        AND     TO_DATE(:start_date, 'YYYY-MM-DD') <= creation_time
        AND     TO_DATE(:end_date, 'YYYY-MM-DD') > creation_time;
        """
        )
        locations : List[Location] = []
        for (
                exposed_person_id,
                location_id,
                exposed_lat,
                exposed_long,
                exposed_time,
        ) in db.engine.execute(query, **data):
            location = Location(
                id=location_id,
                person_id=exposed_person_id,
                creation_time=exposed_time,
            )
            location.set_wkt_with_coords(exposed_lat, exposed_long)
            locations.append(location)
        return locations



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
