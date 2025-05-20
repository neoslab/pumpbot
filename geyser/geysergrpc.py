# Import libraries
import grpc

# Import local libraries
import geyser.geyserpb2 as geyser__pb2

# Define 'GRPC_GENERATED_VERSION'
GRPC_GENERATED_VERSION = '1.71.0'

# Define 'GRPC_VERSION'
GRPC_VERSION = grpc.__version__

# Define '_version_not_supported'
_version_not_supported = False

# Conditional import
try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError
    (
        f'The grpc package installed is at version {GRPC_VERSION},'
        + ' but the generated code in geyser_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


# Class 'GeyserStub'
class GeyserStub:
    """
    This class defines the gRPC client stub for communicating with the Geyser plugin service.
    It provides typed access to all RPC methods exposed by the service, including real-time
    streaming (Subscribe) and unary operations (Ping, GetSlot, etc.). Each method is bound
    to a specific gRPC endpoint path and uses protobuf serializers for request/response marshalling.

    Parameters:
    - channel: A gRPC channel (synchronous or asynchronous) used to issue remote procedure calls.

    Returns:
    - None
    """

    # Class initialization
    def __init__(self, channel):
        """
        Initializes the gRPC stub by binding each method to its corresponding RPC endpoint.
        It maps every service method (e.g., Subscribe, Ping) to the appropriate gRPC handler,
        enabling strongly-typed interactions with the Geyser server. Uses protocol buffers for
        serialization and deserialization of request and response data.

        Parameters:
        - channel: A gRPC channel object to use for sending remote requests.

        Returns:
        - None
        """
        self.Subscribe = channel.stream_stream(
            '/geyser.Geyser/Subscribe', 
            request_serializer = geyser__pb2.SubscribeRequest.SerializeToString, 
            response_deserializer = geyser__pb2.SubscribeUpdate.FromString, 
            _registered_method = True)
        self.Ping = channel.unary_unary(
            '/geyser.Geyser/Ping', 
            request_serializer = geyser__pb2.PingRequest.SerializeToString, 
            response_deserializer = geyser__pb2.PongResponse.FromString, 
            _registered_method = True)
        self.GetLatestBlockhash = channel.unary_unary(
            '/geyser.Geyser/GetLatestBlockhash', 
            request_serializer = geyser__pb2.GetLatestBlockhashRequest.SerializeToString, 
            response_deserializer = geyser__pb2.GetLatestBlockhashResponse.FromString, 
            _registered_method = True)
        self.GetBlockHeight = channel.unary_unary(
            '/geyser.Geyser/GetBlockHeight', 
            request_serializer = geyser__pb2.GetBlockHeightRequest.SerializeToString, 
            response_deserializer = geyser__pb2.GetBlockHeightResponse.FromString, 
            _registered_method = True)
        self.GetSlot = channel.unary_unary(
            '/geyser.Geyser/GetSlot', 
            request_serializer = geyser__pb2.GetSlotRequest.SerializeToString, 
            response_deserializer = geyser__pb2.GetSlotResponse.FromString, 
            _registered_method = True)
        self.IsBlockhashValid = channel.unary_unary(
            '/geyser.Geyser/IsBlockhashValid', 
            request_serializer = geyser__pb2.IsBlockhashValidRequest.SerializeToString, 
            response_deserializer = geyser__pb2.IsBlockhashValidResponse.FromString, 
            _registered_method = True)
        self.GetVersion = channel.unary_unary(
            '/geyser.Geyser/GetVersion', 
            request_serializer = geyser__pb2.GetVersionRequest.SerializeToString, 
            response_deserializer = geyser__pb2.GetVersionResponse.FromString, 
            _registered_method = True)


# Class 'GeyserServicer'
class GeyserServicer:
    """
    This class serves as the base implementation for the Geyser plugin gRPC server.
    It defines the full set of service methods that a custom backend must implement.
    By default, all methods raise NotImplementedError. To use this class, override each
    method with actual application logic for processing requests and sending responses.

    Parameters:
    - None

    Returns:
    - None
    """

    # Function 'Subscribe'
    def Subscribe(self, request_iterator, context):
        """
         Handles the `Subscribe` method, which establishes a bidirectional stream between the
         client and the server to send real-time transaction updates. This method is meant to be
         implemented by services that support continuous data feeds such as live block or log events.

         Parameters:
         - request_iterator: A stream of `SubscribeRequest` protobuf messages sent by the client.
         - context: The gRPC `ServicerContext` object for managing request metadata, status, and cancellation.

         Returns:
         - Generator of `SubscribeUpdate` messages, or raises NotImplementedError by default.
         """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    # Function 'Ping'
    def Ping(self, request, context):
        """
        Handles the `Ping` method, which is typically used by clients to verify the availability
        and responsiveness of the server. When implemented, it should return a `PongResponse`
        indicating the server is alive and optionally include server status or version info.

        Parameters:
        - request: A `PingRequest` protobuf message sent by the client.
        - context: The gRPC `ServicerContext` for handling metadata, status, and lifecycle.

        Returns:
        - PongResponse or raises NotImplementedError if not implemented.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    # Function 'GetLatestBlockhash'
    def GetLatestBlockhash(self, request, context):
        """
        Handles the `GetLatestBlockhash` method, which allows clients to query the most recent
        valid blockhash from the Solana cluster. This is essential for transaction signing and
        expiration validation. Typically returns a `GetLatestBlockhashResponse` containing
        the current blockhash and related context.

        Parameters:
        - request: A `GetLatestBlockhashRequest` protobuf message.
        - context: The gRPC context object for managing call state and errors.

        Returns:
        - GetLatestBlockhashResponse or raises NotImplementedError if not implemented.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    # Function 'GetBlockHeight'
    def GetBlockHeight(self, request, context):
        """
        Handles the `GetBlockHeight` RPC, which responds with the latest known block height
        in the Solana ledger. This can help clients track blockchain progress or determine
        synchronization status with the cluster.

        Parameters:
        - request: A `GetBlockHeightRequest` protobuf object.
        - context: The gRPC context for managing connection and metadata.

        Returns:
        - GetBlockHeightResponse or raises NotImplementedError if not implemented.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    # Function 'GetSlot'
    def GetSlot(self, request, context):
        """
         Handles the `GetSlot` method, used to retrieve the most recent confirmed or processed
         slot number. This information is valuable for measuring cluster lag or tracking the
         progress of ledger commitment.

         Parameters:
         - request: A `GetSlotRequest` protobuf object.
         - context: The gRPC `ServicerContext` for managing the request lifecycle.

         Returns:
         - GetSlotResponse or raises NotImplementedError if not implemented.
         """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    # Function 'IsBlockhashValid'
    def IsBlockhashValid(self, request, context):
        """
        Handles the `IsBlockhashValid` method to verify whether a provided blockhash is
        still valid for submitting transactions. This helps clients avoid signing or sending
        expired transactions that would be rejected by the network.

        Parameters:
        - request: An `IsBlockhashValidRequest` protobuf object containing the blockhash.
        - context: The gRPC context for managing metadata and response status.

        Returns:
        - IsBlockhashValidResponse or raises NotImplementedError if not implemented.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    # Function 'GetVersion'
    def GetVersion(self, request, context):
        """
        Handles the `GetVersion` RPC to return the current version of the Geyser plugin service.
        Useful for compatibility checks between clients and servers. This method should return
        a `GetVersionResponse` with semantic versioning details and possibly build metadata.

        Parameters:
        - request: A `GetVersionRequest` protobuf message.
        - context: The gRPC context instance for handling call flow and status.

        Returns:
        - GetVersionResponse or raises NotImplementedError if not implemented.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


# Function 'add_GeyserServicer_to_server'
def add_GeyserServicer_to_server(servicer, server):
    """
    Registers a GeyserServicer implementation to a running gRPC server instance.
    This function maps all RPC methods to the provided servicer and adds a generic
    handler to the server, allowing the gRPC runtime to dispatch incoming calls
    to the correct method implementations.

    Parameters:
    - servicer: An instance of a class that inherits from `GeyserServicer` and implements all required methods.
    - server: The gRPC server instance to which the service should be registered.

    Returns:
    - None
    """
    rpc_method_handlers = {
        'Subscribe': grpc.stream_stream_rpc_method_handler(
            servicer.Subscribe,
            request_deserializer = geyser__pb2.SubscribeRequest.FromString,
            response_serializer = geyser__pb2.SubscribeUpdate.SerializeToString
        ),
        'Ping': grpc.unary_unary_rpc_method_handler(
            servicer.Ping,
            request_deserializer = geyser__pb2.PingRequest.FromString,
            response_serializer = geyser__pb2.PongResponse.SerializeToString
        ),
        'GetLatestBlockhash': grpc.unary_unary_rpc_method_handler(
            servicer.GetLatestBlockhash,
            request_deserializer = geyser__pb2.GetLatestBlockhashRequest.FromString,
            response_serializer = geyser__pb2.GetLatestBlockhashResponse.SerializeToString
        ),
        'GetBlockHeight': grpc.unary_unary_rpc_method_handler(
            servicer.GetBlockHeight,
            request_deserializer = geyser__pb2.GetBlockHeightRequest.FromString,
            response_serializer = geyser__pb2.GetBlockHeightResponse.SerializeToString
        ),
        'GetSlot': grpc.unary_unary_rpc_method_handler(
            servicer.GetSlot,
            request_deserializer = geyser__pb2.GetSlotRequest.FromString,
            response_serializer = geyser__pb2.GetSlotResponse.SerializeToString
        ),
        'IsBlockhashValid': grpc.unary_unary_rpc_method_handler(
            servicer.IsBlockhashValid,
            request_deserializer = geyser__pb2.IsBlockhashValidRequest.FromString,
            response_serializer = geyser__pb2.IsBlockhashValidResponse.SerializeToString
        ),
        'GetVersion': grpc.unary_unary_rpc_method_handler(
            servicer.GetVersion,
            request_deserializer = geyser__pb2.GetVersionRequest.FromString,
            response_serializer = geyser__pb2.GetVersionResponse.SerializeToString
        )
    }
    generic_handler = grpc.method_handlers_generic_handler('geyser.Geyser', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('geyser.Geyser', rpc_method_handlers)


# Class 'Geyser'
class Geyser:
    """
    This static class provides experimental direct access to Geyser service RPC calls
    without using the generated stub. It enables flexible gRPC method invocations
    using raw parameters. This is useful for advanced users who need full control
    over client construction or wish to bypass the normal stub abstraction layer.

    Parameters:
    - None (all methods are static)

    Returns:
    - None
    """

    # Function 'Subscribe'
    @staticmethod
    def Subscribe(request_iterator, target, options = (), channel_credentials = None, call_credentials = None,
            insecure = False, compression = None, wait_for_ready = None, timeout = None, metadata = None):
        """
        Performs a bidirectional stream RPC call to the `Subscribe` endpoint of the Geyser service.
        This allows the client to send a continuous stream of `SubscribeRequest` messages and receive
        a stream of `SubscribeUpdate` messages in return. This is primarily used to receive live updates
        about blockchain state such as account changes or program events in near real time.

        Parameters:
        - request_iterator: An iterator or async generator of `SubscribeRequest` messages to send.
        - target (str): The gRPC server address (e.g., "localhost:50051").
        - options (tuple): Optional gRPC options for the call.
        - channel_credentials: SSL credentials for a secure connection (optional).
        - call_credentials: Per-call credentials (e.g., access token) (optional).
        - insecure (bool): Whether to use an insecure (non-TLS) connection.
        - compression: Compression type (e.g., "gzip") (optional).
        - wait_for_ready (bool): If True, the call waits for the server to be ready.
        - timeout (float): Timeout in seconds before the call fails.
        - metadata (list): Optional metadata headers (e.g., authentication tokens).

        Returns:
        - An iterable stream of `SubscribeUpdate` messages from the server.
        """
        return grpc.experimental.stream_stream(
            request_iterator, target, '/geyser.Geyser/Subscribe',
            geyser__pb2.SubscribeRequest.SerializeToString,
            geyser__pb2.SubscribeUpdate.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method = True)

    # Function 'Ping'
    @staticmethod
    def Ping(request, target, options = (), channel_credentials = None, call_credentials = None,
             insecure = False, compression = None, wait_for_ready = None, timeout = None, metadata = None):
        """
        Sends a unary `Ping` request to the Geyser service to verify its responsiveness.
        This endpoint is useful for health checks or liveness probes. The server is expected
        to return a `PongResponse` confirming it is operational and optionally providing
        server metadata or timing diagnostics.

        Parameters:
        - request: A `PingRequest` protobuf message.
        - target (str): The gRPC server address.
        - options (tuple): Additional gRPC options.
        - channel_credentials: TLS credentials for the channel.
        - call_credentials: Authentication token or other call-level credentials.
        - insecure (bool): If True, disables TLS.
        - compression: Optional compression algorithm.
        - wait_for_ready (bool): Waits for the server to become ready before starting.
        - timeout (float): Maximum time allowed for the request.
        - metadata (list): Optional metadata headers.

        Returns:
        - A `PongResponse` object returned by the server.
        """
        return grpc.experimental.unary_unary(
            request,
            target,
            '/geyser.Geyser/Ping',
            geyser__pb2.PingRequest.SerializeToString,
            geyser__pb2.PongResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method = True)

    # Function 'GetLatestBlockhash'
    @staticmethod
    def GetLatestBlockhash(request, target, options = (), channel_credentials = None, call_credentials = None,
            insecure = False, compression = None, wait_for_ready = None, timeout = None, metadata = None):
        """
        Sends a request to retrieve the latest valid blockhash from the Solana blockchain.
        This blockhash can then be used to sign and submit new transactions. The response includes
        the hash itself along with context information such as the slot it was generated at.

        Parameters:
        - request: A `GetLatestBlockhashRequest` protobuf object.
        - target (str): gRPC target address of the Geyser service.
        - options (tuple): Custom options for fine-tuning the gRPC call.
        - channel_credentials: SSL/TLS credentials for secure communication.
        - call_credentials: Optional call-scoped credentials like API tokens.
        - insecure (bool): Use unencrypted HTTP/2 instead of TLS.
        - compression: Compression strategy (e.g., "gzip") to use (optional).
        - wait_for_ready (bool): Wait for connection readiness before executing the call.
        - timeout (float): Time limit for the request in seconds.
        - metadata (list): Key-value pairs sent as call headers.

        Returns:
        - A `GetLatestBlockhashResponse` message containing the current blockhash.
        """
        return grpc.experimental.unary_unary(
            request,
            target,
            '/geyser.Geyser/GetLatestBlockhash',
            geyser__pb2.GetLatestBlockhashRequest.SerializeToString,
            geyser__pb2.GetLatestBlockhashResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method = True)

    # Function 'GetBlockHeight'
    @staticmethod
    def GetBlockHeight(request, target, options = (), channel_credentials = None, call_credentials = None,
            insecure = False, compression = None, wait_for_ready = None, timeout = None, metadata = None):
        """
        Requests the current block height from the Geyser service. This value represents the total number
        of confirmed blocks in the ledger and is useful for tracking progress or comparing synchronization
        across nodes. The response includes the latest height and metadata regarding cluster state.

        Parameters:
        - request: A `GetBlockHeightRequest` protobuf message.
        - target (str): The gRPC endpoint of the target service.
        - options (tuple): Additional gRPC call options.
        - channel_credentials: Secure channel credentials (TLS).
        - call_credentials: Optional access token or per-call credentials.
        - insecure (bool): If True, the call is made over an insecure connection.
        - compression: Type of compression to apply to the call.
        - wait_for_ready (bool): If True, delays call until the channel is ready.
        - timeout (float): Max duration to wait for a response.
        - metadata (list): Metadata key-value pairs for the call.

        Returns:
        - A `GetBlockHeightResponse` object containing the current ledger height.
        """
        return grpc.experimental.unary_unary(
            request,
            target,
            '/geyser.Geyser/GetBlockHeight',
            geyser__pb2.GetBlockHeightRequest.SerializeToString,
            geyser__pb2.GetBlockHeightResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method = True)

    # Function 'GetSlot'
    @staticmethod
    def GetSlot(request, target, options = (), channel_credentials = None, call_credentials = None,
            insecure = False, compression = None, wait_for_ready = None, timeout = None, metadata = None):
        """
        Sends a request to retrieve the latest known slot number in the Solana cluster.
        Slots are used to track ledger time and state transitions. The returned slot number
        can be used for client-side syncing, historical queries, or performance monitoring.

        Parameters:
        - request: A `GetSlotRequest` protobuf message.
        - target (str): Address of the gRPC server.
        - options (tuple): Tuple of gRPC options.
        - channel_credentials: TLS credentials for the channel (optional).
        - call_credentials: Optional per-call authentication credentials.
        - insecure (bool): Whether to disable TLS encryption.
        - compression: Compression strategy to apply (optional).
        - wait_for_ready (bool): If True, wait until the channel is ready.
        - timeout (float): Timeout for the call in seconds.
        - metadata (list): Optional list of metadata headers.

        Returns:
        - A `GetSlotResponse` object containing the current slot.
        """
        return grpc.experimental.unary_unary(
            request,
            target,
            '/geyser.Geyser/GetSlot',
            geyser__pb2.GetSlotRequest.SerializeToString,
            geyser__pb2.GetSlotResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method = True)

    # Function 'IsBlockhashValid'
    @staticmethod
    def IsBlockhashValid(request, target, options = (), channel_credentials = None, call_credentials = None,
            insecure = False, compression = None, wait_for_ready = None, timeout = None, metadata = None):
        """
        Queries the Geyser service to check whether a given blockhash is still valid.
        This helps clients determine if it's safe to sign and send a transaction using
        that blockhash, which must not have expired or been replaced.

        Parameters:
        - request: An `IsBlockhashValidRequest` protobuf message containing the hash to validate.
        - target (str): The gRPC address of the Geyser service.
        - options (tuple): Optional parameters for the gRPC call.
        - channel_credentials: SSL/TLS credentials for secure transport.
        - call_credentials: Authentication credentials (optional).
        - insecure (bool): Indicates whether to use insecure connection.
        - compression: Compression algorithm for the gRPC stream.
        - wait_for_ready (bool): If True, delays the call until the server is ready.
        - timeout (float): Timeout in seconds.
        - metadata (list): Metadata headers as key-value pairs.

        Returns:
        - An `IsBlockhashValidResponse` with a boolean validity field.
        """
        return grpc.experimental.unary_unary(
            request,
            target,
            '/geyser.Geyser/IsBlockhashValid',
            geyser__pb2.IsBlockhashValidRequest.SerializeToString,
            geyser__pb2.IsBlockhashValidResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method = True)

    # Function 'GetVersion'
    @staticmethod
    def GetVersion(request, target, options = (), channel_credentials = None, call_credentials = None,
            insecure = False, compression = None, wait_for_ready = None, timeout = None, metadata = None):
        """
        Retrieves the current version of the Geyser plugin running on the server.
        This endpoint allows clients to verify compatibility or perform runtime checks.
        The returned response typically includes a version string, build number, and
        possibly supported features.

        Parameters:
        - request: A `GetVersionRequest` protobuf message.
        - target (str): The gRPC server URL.
        - options (tuple): Optional gRPC configuration options.
        - channel_credentials: Channel-level security credentials.
        - call_credentials: Additional call-level credentials (e.g., bearer tokens).
        - insecure (bool): If True, disables SSL encryption.
        - compression: Optional compression type.
        - wait_for_ready (bool): If True, blocks until the channel is ready.
        - timeout (float): Maximum wait time for a response.
        - metadata (list): Optional metadata headers.

        Returns:
        - A `GetVersionResponse` object containing version information.
        """
        return grpc.experimental.unary_unary(
            request,
            target,
            '/geyser.Geyser/GetVersion',
            geyser__pb2.GetVersionRequest.SerializeToString,
            geyser__pb2.GetVersionResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method = True)