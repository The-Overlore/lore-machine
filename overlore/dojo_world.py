from concurrent import futures

import grpc

from overlore.proto import world_pb2, world_pb2_grpc
from overlore.proto.world_pb2 import (
    MetadataRequest,
    MetadataResponse,
    RetrieveEntitiesRequest,
    RetrieveEntitiesResponse,
    SubscribeEntitiesRequest,
    SubscribeEntitiesResponse,
)


class WorldService(world_pb2_grpc.WorldServicer):
    def WorldMetadata(self, request: MetadataRequest, context: grpc.ServicerContext) -> MetadataResponse:
        # Implement the WorldMetadata logic
        # Return a MetadataResponse message
        return world_pb2.MetadataResponse()

    def SubscribeEntities(
        self, request: SubscribeEntitiesRequest, context: grpc.ServicerContext
    ) -> SubscribeEntitiesResponse:
        # Implement the SubscribeEntities logic
        # Yield SubscribeEntitiesResponse messages
        # Example: yield world_pb2.SubscribeEntitiesResponse()
        pass

    def RetrieveEntities(
        self, request: RetrieveEntitiesRequest, context: grpc.ServicerContext
    ) -> RetrieveEntitiesResponse:
        # Implement the RetrieveEntities logic
        # Return a RetrieveEntitiesResponse message
        return world_pb2.RetrieveEntitiesResponse()


def serve() -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    world_pb2_grpc.add_WorldServicer_to_server(WorldService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()
