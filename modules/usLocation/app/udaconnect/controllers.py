from datetime import datetime

from app.udaconnect.models import Location
from app.udaconnect.schemas import (
    LocationSchema,
)
from app.udaconnect.services import LocationService, LocationInfoService, KafkaService
from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from typing import Optional, List

DATE_FORMAT = "%Y-%m-%d"

api = Namespace("UdaConnect", description="Locations")  # noqa


# TODO: This needs better exception handling


@api.route("/locations")
class LocationsResource(Resource):
    @accepts(schema=LocationSchema)
    @responds(schema=LocationSchema)
    def post(self) -> Location:
        request.get_json()
        location: Location = KafkaService.sendLocation(request.get_json())
        return location

    @responds(schema=LocationSchema, many=True)
    def get(self) -> List[Location]:
        locations: List[Location] = LocationService.retrieve_all()
        return locations
        

@api.route("/locations/<location_id>")
@api.param("location_id", "Unique ID for a given Location", _in="query")
class LocationResource(Resource):
    @responds(schema=LocationSchema)
    def get(self, location_id) -> Location:
        location: Location = LocationService.retrieve(location_id)
        return location


@api.route("/locationsinfo/person/<person_id>")
@api.param("person_id", "Unique ID for a given Person", _in="query") 
class LocationsInfoResource(Resource):
    @responds(schema=LocationSchema, many=True)
    def get(self, person_id) -> List[Location]:
        locations: List[Location] = LocationInfoService.findLocations(person_id=person_id, start_date=request.args["start_date"], end_date=request.args["end_date"])
        return locations


@api.route("/locationinfo/person/<person_id>")
@api.param("person_id", "Unique ID for a given Person", _in="query")
class LocationInfoResource(Resource):
    @responds(schema=LocationSchema, many=True)
    def get(self, person_id) -> Location:
        locations: List[Location] = LocationInfoService.findLocation(person_id, start_date=request.args["start_date"], end_date=request.args["end_date"],
                meters=request.args["meters"], latitude=request.args["latitude"], longitude=request.args["longitude"])
        return locations