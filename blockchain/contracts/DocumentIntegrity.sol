// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title DocumentIntegrity
 * @notice Tamper-evident hash anchor for document versions.
 *
 * Stores ONLY an opaque per-version key -> anchored SHA-256 hash (bytes32)
 * plus the registration timestamp. Never stores file contents, metadata,
 * or audit information on-chain.
 */
contract DocumentIntegrity {
    struct Anchor {
        bytes32 documentHash;
        uint256 timestamp;
        bool exists;
    }

    mapping(string => Anchor) private anchors;

    event HashRegistered(
        string indexed key,
        bytes32 documentHash,
        uint256 timestamp
    );

    /**
     * @dev Register a document-version hash.
     * Reverts on empty keys, empty hashes, and duplicate registration.
     */
    function registerDocumentHash(
        string calldata key,
        bytes32 documentHash
    ) external {
        require(bytes(key).length > 0, "empty document-version key");
        require(documentHash != bytes32(0), "empty document hash");
        require(
            !anchors[key].exists,
            "hash already registered for this key"
        );

        anchors[key] = Anchor({
            documentHash: documentHash,
            timestamp: block.timestamp,
            exists: true
        });
        emit HashRegistered(key, documentHash, block.timestamp);
    }

    /**
     * @dev Retrieve the anchored hash + timestamp. Reverts if never registered.
     */
    function getAnchor(string calldata key)
        external
        view
        returns (bytes32 documentHash, uint256 timestamp)
    {
        Anchor storage a = anchors[key];
        require(a.exists, "key not anchored");
        return (a.documentHash, a.timestamp);
    }

    /**
     * @dev True if a key already has an anchor (never reverts).
     */
    function isAnchored(string calldata key) external view returns (bool) {
        return anchors[key].exists;
    }
}