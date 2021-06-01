import grpc
import location_pb2
import location_pb2_grpc

print("Sending sample payload")

channel = grpc.insecure_channel("localhost:30003")
stub = location_pb2_grpc.LocationServiceStub(channel)

location = location_pb2.LocationMessage(
	person_id = 1,
    latitude = 49.05,
    longitude = 49.05
)

response = stub.Create(location)