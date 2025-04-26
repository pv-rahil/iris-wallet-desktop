"""Module containing PeerRepository."""
from __future__ import annotations

from src.model.peers_model import ConnectPeerRequestModel
from src.model.peers_model import ConnectPeerResponseModel
from src.model.peers_model import DisconnectPeerRequestModel
from src.model.peers_model import DisconnectResponseModel
from src.model.peers_model import ListPeersResponseModel
from src.utils.custom_context import repository_custom_context
from src.utils.decorators.unlock_required import unlock_required
from src.utils.endpoints import CONNECT_PEER_ENDPOINT
from src.utils.endpoints import DISCONNECT_PEER_ENDPOINT
from src.utils.endpoints import LIST_PEERS_ENDPOINT
from src.utils.request import Request


class PeerRepository:
    """Repository for handling peer connections."""

    @staticmethod
    @unlock_required
    def connect_peer(connect_peer_detail: ConnectPeerRequestModel) -> ConnectPeerResponseModel:
        """Connect to a peer."""
        payload = connect_peer_detail.dict()
        with repository_custom_context():
            response = Request.post(CONNECT_PEER_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            return ConnectPeerResponseModel(status=True)

    @staticmethod
    @unlock_required
    def disconnect_peer(peer_detail: DisconnectPeerRequestModel) -> DisconnectResponseModel:
        """Disconnect from a peer."""
        payload = peer_detail.dict()
        with repository_custom_context():
            response = Request.post(DISCONNECT_PEER_ENDPOINT, payload)
            response.raise_for_status()  # Raises an exception for HTTP errors
            return DisconnectResponseModel(status=True)

    @staticmethod
    @unlock_required
    def list_peer() -> ListPeersResponseModel:
        """List connected peers."""
        with repository_custom_context():
            response = Request.get(LIST_PEERS_ENDPOINT)
            response.raise_for_status()  # Raises an exception for HTTP errors
            data = response.json()
            return ListPeersResponseModel(**data)
