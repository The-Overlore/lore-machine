# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import world_pb2 as world__pb2


class WorldStub:
    """The World service provides information about the world."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.WorldMetadata = channel.unary_unary(
            "/world.World/WorldMetadata",
            request_serializer=world__pb2.MetadataRequest.SerializeToString,
            response_deserializer=world__pb2.MetadataResponse.FromString,
        )
        self.SubscribeEntities = channel.unary_stream(
            "/world.World/SubscribeEntities",
            request_serializer=world__pb2.SubscribeEntitiesRequest.SerializeToString,
            response_deserializer=world__pb2.SubscribeEntitiesResponse.FromString,
        )
        self.RetrieveEntities = channel.unary_unary(
            "/world.World/RetrieveEntities",
            request_serializer=world__pb2.RetrieveEntitiesRequest.SerializeToString,
            response_deserializer=world__pb2.RetrieveEntitiesResponse.FromString,
        )


class WorldServicer:
    """The World service provides information about the world."""

    def WorldMetadata(self, request, context):
        """Retrieves metadata about the World including all the registered components and systems."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SubscribeEntities(self, request, context):
        """Subscribes to entities updates."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def RetrieveEntities(self, request, context):
        """Retrieve entity"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_WorldServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "WorldMetadata": grpc.unary_unary_rpc_method_handler(
            servicer.WorldMetadata,
            request_deserializer=world__pb2.MetadataRequest.FromString,
            response_serializer=world__pb2.MetadataResponse.SerializeToString,
        ),
        "SubscribeEntities": grpc.unary_stream_rpc_method_handler(
            servicer.SubscribeEntities,
            request_deserializer=world__pb2.SubscribeEntitiesRequest.FromString,
            response_serializer=world__pb2.SubscribeEntitiesResponse.SerializeToString,
        ),
        "RetrieveEntities": grpc.unary_unary_rpc_method_handler(
            servicer.RetrieveEntities,
            request_deserializer=world__pb2.RetrieveEntitiesRequest.FromString,
            response_serializer=world__pb2.RetrieveEntitiesResponse.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler("world.World", rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class World:
    """The World service provides information about the world."""

    @staticmethod
    def WorldMetadata(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/world.World/WorldMetadata",
            world__pb2.MetadataRequest.SerializeToString,
            world__pb2.MetadataResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def SubscribeEntities(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_stream(
            request,
            target,
            "/world.World/SubscribeEntities",
            world__pb2.SubscribeEntitiesRequest.SerializeToString,
            world__pb2.SubscribeEntitiesResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def RetrieveEntities(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/world.World/RetrieveEntities",
            world__pb2.RetrieveEntitiesRequest.SerializeToString,
            world__pb2.RetrieveEntitiesResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )
