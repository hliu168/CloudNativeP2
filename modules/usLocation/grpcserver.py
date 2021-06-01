import time
import json
from concurrent import futures

from kafka import KafkaProducer

import grpc
import location_pb2
import location_pb2_grpc


kafkaServer = "kafka-service:9092"
topicName = 'locations'

class LocationServicer(location_pb2_grpc.LocationServiceServicer):
    def Create(self, request, context):

        request_value = {
            "person_id": int(request.person_id),
            "latitude": str(request.latitude),
            "longitude": str(request.longitude)
        }
        print(request_value)

        producer = KafkaProducer(bootstrap_servers=kafkaServer)
        kafka_data = json.dumps(request_value).encode()
        producer.send(topicName, kafka_data)
        producer.flush()
        return request

# Initialize gRPC server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
location_pb2_grpc.add_LocationServiceServicer_to_server(LocationServicer(), server)


print("Server starting on port 5005...")
server.add_insecure_port("[::]:5005")
server.start()
# Keep thread alive
try:
    while True:
        time.sleep(86400)
except KeyboardInterrupt:
    server.stop(0)