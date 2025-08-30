// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IFdcVerification {
    function verifyAttestation(
        bytes32 requestId,
        bytes32 attestationResponse,
        bytes calldata proof
    ) external view returns (bool);
}

contract DataPurchase {
    event DataRequested(address buyer, bytes32 requestId);
    event DataDelivered(bytes32 requestId, bytes32 dataHash);

    struct Request {
        address buyer;
        bool delivered;
    }

    mapping(bytes32 => Request) public requests;

    address public fdcVerifier;
    address public owner;

    constructor(address _fdcVerifier) {
        fdcVerifier = _fdcVerifier;
        owner = msg.sender;
    }

    function purchase(bytes32 requestId) external payable {
        require(msg.value > 0, "Payment required");
        requests[requestId] = Request(msg.sender, false);
        emit DataRequested(msg.sender, requestId);
    }

    function deliverData(
        bytes32 requestId,
        bytes32 attestationResponse,
        bytes calldata proof
    ) external {
        require(!requests[requestId].delivered, "Already fulfilled");
        require(requests[requestId].buyer != address(0), "Invalid request");

        bool valid = IFdcVerification(fdcVerifier).verifyAttestation(
            requestId,
            attestationResponse,
            proof
        );
        require(valid, "Invalid attestation proof");

        requests[requestId].delivered = true;
        emit DataDelivered(requestId, attestationResponse);
    }
}
