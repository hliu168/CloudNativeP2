import logging, requests
from datetime import datetime, timedelta
from typing import Dict, List

from app import db
from app.udaconnect.models import Connection, Location, Person
from app.udaconnect.schemas import ConnectionSchema, LocationSchema, PersonSchema
from geoalchemy2.functions import ST_AsText, ST_Point
from sqlalchemy.sql import text

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("udaconnect-api")


class ConnectionService:
    @staticmethod
    def find_contacts(person_id: int, start_date: datetime, end_date: datetime, meters=5
    ) -> List[Connection]:
        """
        Finds all Person who have been within a given distance of a given Person within a date range.

        This will run rather quickly locally, but this is an expensive method and will take a bit of time to run on
        large datasets. This is by design: what are some ways or techniques to help make this data integrate more
        smoothly for a better user experience for API consumers?
        """
        locations: List = LocationService.findLocations(person_id, start_date, end_date)
        data = []
        for location in locations:
            data.append(
                {
                    "person_id": person_id,
                    "longitude": location.longitude,
                    "latitude": location.latitude,
                    "meters": meters,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": (end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                }
            )
        # Cache all users in memory for quick lookup
        person_map: Dict[str, Person] = {person["id"]: person for person in PersonService.retrieve_all()}

        # Prepare arguments for queries

        result: List[Connection] = []
        for line in data:
            for location in LocationService.findLocation(person_id=line["person_id"], start_date=line["start_date"], end_date=line["end_date"],
                    meters=line["meters"], latitude=line["latitude"], longitude=line["longitude"]):
                result.append(
                    Connection(
                        person=person_map[location.person_id], location=location,
                    )
                )
            
        return result


class LocationService:
    @staticmethod
    def findLocations(person_id, start_date, end_date) -> List[Location]:
        location_list: List[Location] = []
        res = requests.get("http://location-api:5000/api/locationsinfo/person/{}?start_date={}&end_date={}".format(person_id, start_date, end_date))
        locations = res.json()

        for locationJson in locations:
            location = Location()
            location.id = locationJson['id']
            location.person_id = locationJson['person_id']
            location.set_wkt_with_coords(locationJson['latitude'], locationJson['longitude'])
            location.creation_time = datetime.strptime(locationJson['creation_time'], "%Y-%m-%dT%H:%M:%S")
            location_list.append(location)
        return location_list
    
    @staticmethod
    def findLocation(person_id, start_date, end_date, meters, latitude, longitude) -> List[Location]:
        res = requests.get("http://location-api:5000/api/locationinfo/person/{}?start_date={}&end_date={}&meters={}&latitude={}&longitude={}"
                .format(person_id, start_date, end_date, meters, latitude, longitude))
        location_list: List[Location] = []
        locations = res.json()
        for locationJson in locations:
            location = Location()
            location.id = locationJson['id']
            location.person_id = locationJson['person_id']
            location.set_wkt_with_coords(locationJson['latitude'], locationJson['longitude'])
            location.creation_time = datetime.strptime(locationJson['creation_time'], "%Y-%m-%dT%H:%M:%S")
            location_list.append(location)
        return location_list


class PersonService:
    @staticmethod
    def retrieve_all() -> List[Person]:
        persons_list : List[Person] = []
        res = requests.get("http://person-api:5000/api/persons")
        persons = res.json()

        for p in persons:
            person = Person()
            person.id = p['id']
            person.company_name = p['company_name']
            person.last_name = p['last_name']
            person.first_name = p['first_name']
            persons_list.append(p)

        # return db.session.query(Person).all()
        return persons_list

