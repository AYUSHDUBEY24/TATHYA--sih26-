"""
Blockchain service (Phase 7) — connect to the local Hardhat network and
anchor document-version hashes in the DocumentIntegrity smart contract.

The blockchain is ONLY an integrity-anchor layer. It never stores file
contents or metadata. All operations raise BlockchainError on failure
so callers can degrade gracefully (mark the anchor FAILED/PENDING).

Secrets (RPC URL, contract address, private key) come from environment
variables. The private key stays backend-only and is never exposed.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger("sih26190.blockchain")


class BlockchainError(Exception):
    """Raised when a blockchain operation fails (node down, tx reverted, etc.)."""


class BlockchainService:
    """
    Connect to the local Hardhat network and anchor document-version hashes.

    Connection is lazy: the node is only contacted when an operation is
    first attempted. Connection state is cached for the lifetime of the
    process (single-contract, single-network prototype).
    """

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._w3 = None
        self._contract = None
        self._account = None

    @staticmethod
    def _load_abi() -> list[dict]:
        """Load the DocumentIntegrity ABI from the compiled Hardhat artifact."""
        artifact = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "blockchain"
            / "artifacts"
            / "contracts"
            / "DocumentIntegrity.sol"
            / "DocumentIntegrity.json"
        )
        with open(artifact) as f:
            return json.load(f)["abi"]

    def _connect(self) -> None:
        """Establish the web3 connection, account, and contract instance."""
        from web3 import Web3

        rpc_url = self.settings.BLOCKCHAIN_RPC_URL
        private_key = self.settings.BLOCKCHAIN_PRIVATE_KEY
        contract_address = self.settings.BLOCKCHAIN_CONTRACT_ADDRESS

        if not private_key:
            raise BlockchainError("BLOCKCHAIN_PRIVATE_KEY is not configured")
        if not contract_address:
            raise BlockchainError("BLOCKCHAIN_CONTRACT_ADDRESS is not configured")

        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            raise BlockchainError(f"Cannot connect to blockchain node at {rpc_url}")

        self._account = w3.eth.account.from_key(private_key)
        self._contract = w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=self._load_abi(),
        )
        self._w3 = w3
        logger.info(
            "Blockchain connected: node=%s account=%s contract=%s",
            rpc_url, self._account.address, contract_address,
        )

    @property
    def w3(self):
        if self._w3 is None:
            self._connect()
        return self._w3

    @property
    def contract(self):
        if self._contract is None:
            self._connect()
        return self._contract

    @property
    def account(self):
        if self._account is None:
            self._connect()
        return self._account

    # ------------------------------------------------------------------
    # Public operations
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
            """Return True if the node is reachable and the contract is loaded."""
            try:
                self._connect()
                return self._w3.is_connected()
            except BlockchainError:
                return False

    @staticmethod
    def _hex_to_bytes32(hash_hex: str) -> bytes:
        """Convert a lowercase hex SHA-256 digest to a 32-byte value."""
        clean = hash_hex.lower().replace("0x", "")
        if len(clean) != 64:
            raise BlockchainError(
                f"Invalid SHA-256 hex length: {len(clean)} (expected 64)"
            )
        return bytes.fromhex(clean)

    def is_anchored(self, key: str) -> bool:
        """True if *key* already has an on-chain anchor."""
        try:
            return bool(self.contract.functions.isAnchored(key).call())
        except BlockchainError:
            raise
        except Exception as exc:
            raise BlockchainError(f"Failed to check anchor status: {exc}") from exc

    def get_anchor(self, key: str) -> dict | None:
        """
        Return {"hash": <hex>, "timestamp": <datetime>} for *key*, or
        None if the key has never been anchored.
        """
        try:
            result = self.contract.functions.getAnchor(key).call()
        except Exception as exc:
            if "key not anchored" in str(exc):
                return None
            raise BlockchainError(
                f"Failed to read anchor for key '{key}': {exc}"
            ) from exc

        hash_bytes = result[0]
        timestamp_unix = result[1]
        return {
            "hash": "0x" + hash_bytes.hex(),
            "timestamp": datetime.fromtimestamp(timestamp_unix, tz=timezone.utc),
        }

    def register_hash(self, key: str, hash_hex: str) -> dict:
        """
        Register a document-version hash on-chain.

        Returns {"tx_hash", "block_number", "timestamp"}.
        Raises BlockchainError on any failure.
        """
        if not key:
            raise BlockchainError("Empty document-version key")

        bytes32_hash = self._hex_to_bytes32(hash_hex)

        # Guard against double registration (the contract also reverts).
        try:
            if self.contract.functions.isAnchored(key).call():
                raise BlockchainError(f"Hash already registered for key '{key}'")
        except BlockchainError:
            raise
        except Exception as exc:
            raise BlockchainError(f"Failed to check anchor status: {exc}") from exc

        try:
            tx = self.contract.functions.registerDocumentHash(
                key, bytes32_hash
            ).build_transaction(
                {
                    "from": self.account.address,
                    "nonce": self.w3.eth.get_transaction_count(self.account.address),
                    "chainId": self.settings.BLOCKCHAIN_CHAIN_ID,
                }
            )
            signed = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        except BlockchainError:
            raise
        except Exception as exc:
            raise BlockchainError(f"Transaction submission failed: {exc}") from exc

        if receipt["status"] != 1:
            raise BlockchainError(f"Transaction reverted (tx={tx_hash.hex()})")

        block = self.w3.eth.get_block(receipt["blockNumber"])
        return {
            "tx_hash": tx_hash.hex(),
            "block_number": receipt["blockNumber"],
            "timestamp": datetime.fromtimestamp(block["timestamp"], tz=timezone.utc),
        }


# ------------------------------------------------------------------
# Process-wide singleton + FastAPI dependency
# ------------------------------------------------------------------

_blockchain_service: BlockchainService | None = None


def get_blockchain_service() -> BlockchainService:
    """FastAPI dependency returning the shared blockchain service."""
    global _blockchain_service
    if _blockchain_service is None:
        _blockchain_service = BlockchainService()
        return _blockchain_service
    return _blockchain_service
