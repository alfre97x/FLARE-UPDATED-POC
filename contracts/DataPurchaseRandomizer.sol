// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title DataPurchaseRandomizer (Flare SRNG - RandomNumberV2 beacon integration)
 * @dev Reads randomness from Flare SRNG (RandomNumberV2) via Contract Registry on Coston2
 *      and stores it per userProvidedId for deterministic use in pricing.
 *
 * Key points:
 * - SRNG is a randomness beacon; there is no per-request API. We fetch the current round's
 *   random number using getRandomNumber() (view) and store it on-chain via storeRandomness().
 * - Once stored, randomness for a given userProvidedId is immutable and considered fulfilled.
 */

interface IContractRegistry {
    function getContractAddressByName(string calldata name) external view returns (address);
}

interface IRandomNumberV2 {
    function getRandomNumber()
        external
        view
        returns (uint256 _randomNumber, bool _isSecureRandom, uint256 _randomTimestamp);

    function getRandomNumberHistorical(uint256 _votingRoundId)
        external
        view
        returns (uint256 _randomNumber, bool _isSecureRandom, uint256 _randomTimestamp);
}

contract DataPurchaseRandomizer {
    // Events
    event RandomnessStored(
        bytes32 indexed userProvidedId,
        uint256 randomValue,
        bool isSecure,
        uint256 randomTimestamp
    );

    // State variables
    address public owner;
    address public registry; // Flare Contract Registry address (e.g., Coston2)

    // Mappings
    mapping(bytes32 => uint256) public userProvidedIdToRandomValue; // userProvidedId -> random value
    mapping(bytes32 => bool) public userProvidedIdFulfilled;        // userProvidedId -> fulfilled flag
    mapping(bytes32 => uint256) public userProvidedIdToTimestamp;   // optional: timestamp from SRNG
    mapping(bytes32 => bool) public userProvidedIdIsSecure;         // optional: security flag from SRNG

    // Modifiers
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    /**
     * @dev Constructor
     * @param _registry Address of the Flare Contract Registry on the target network (e.g., Coston2)
     *
     * Coston2 Registry (as of writing): 0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019
     */
    constructor(address _registry) {
        owner = msg.sender;
        registry = _registry;
    }

    /**
     * @dev Internal helper to resolve the current SRNG (RandomNumberV2) contract address from the registry
     */
    function srng() internal view returns (IRandomNumberV2) {
        address rng = IContractRegistry(registry).getContractAddressByName("RandomNumberV2");
        require(rng != address(0), "SRNG not resolved");
        return IRandomNumberV2(rng);
    }

    /**
     * @notice Fetch randomness from SRNG beacon and store it for the given userProvidedId
     * @param _userProvidedId Custom ID for tracking (bytes32)
     * @return randomValue The random number fetched
     * @return isSecure Whether SRNG marks the randomness as secure
     * @return randomTimestamp Timestamp associated with the randomness
     */
    function storeRandomness(bytes32 _userProvidedId)
        external
        returns (uint256 randomValue, bool isSecure, uint256 randomTimestamp)
    {
        require(!userProvidedIdFulfilled[_userProvidedId], "Already fulfilled");

        (randomValue, isSecure, randomTimestamp) = srng().getRandomNumber();
        require(randomValue != 0, "SRNG not ready");

        userProvidedIdToRandomValue[_userProvidedId] = randomValue;
        userProvidedIdIsSecure[_userProvidedId] = isSecure;
        userProvidedIdToTimestamp[_userProvidedId] = randomTimestamp;
        userProvidedIdFulfilled[_userProvidedId] = true;

        emit RandomnessStored(_userProvidedId, randomValue, isSecure, randomTimestamp);
    }

    /**
     * @notice Get the random value for a user-provided ID
     * @param _userProvidedId The user-provided ID
     * @return randomValue The random value
     * @return fulfilled Whether the randomness has been stored
     */
    function getRandomValue(bytes32 _userProvidedId) external view returns (uint256 randomValue, bool fulfilled) {
        return (userProvidedIdToRandomValue[_userProvidedId], userProvidedIdFulfilled[_userProvidedId]);
    }

    /**
     * @notice Get the randomness metadata (isSecure flag and timestamp) for a user-provided ID
     * @param _userProvidedId The user-provided ID
     * @return isSecure Whether SRNG marked the randomness as secure
     * @return randomTimestamp The timestamp associated with the randomness
     * @return fulfilled Whether the randomness has been stored
     */
    function getRandomnessMeta(bytes32 _userProvidedId)
        external
        view
        returns (bool isSecure, uint256 randomTimestamp, bool fulfilled)
    {
        if (!userProvidedIdFulfilled[_userProvidedId]) {
            return (false, 0, false);
        }
        return (userProvidedIdIsSecure[_userProvidedId], userProvidedIdToTimestamp[_userProvidedId], true);
    }

    /**
     * @notice Get a normalized random value between 0 and 999 (for 3 decimal places)
     * @param _userProvidedId The user-provided ID
     * @return normalizedValue The normalized random value (0-999)
     * @return fulfilled Whether the randomness has been stored
     */
    function getNormalizedRandomValue(bytes32 _userProvidedId)
        external
        view
        returns (uint256 normalizedValue, bool fulfilled)
    {
        if (!userProvidedIdFulfilled[_userProvidedId]) {
            return (0, false);
        }

        uint256 randomValue = userProvidedIdToRandomValue[_userProvidedId];
        normalizedValue = (randomValue % 1000);

        return (normalizedValue, true);
    }

    /**
     * @notice Get a random price variation factor and final price
     * @param _userProvidedId The user-provided ID
     * @param _basePrice The base price to apply variation to (wei)
     * @param _variationPercent The maximum variation percentage (e.g., 10 for ±10%)
     * @return finalPrice The price with random variation applied
     * @return variationFactor The variation factor applied (e.g., -5 for -5%)
     * @return fulfilled Whether the randomness has been stored
     */
    function getRandomPriceVariation(
        bytes32 _userProvidedId,
        uint256 _basePrice,
        uint256 _variationPercent
    ) external view returns (uint256 finalPrice, int256 variationFactor, bool fulfilled) {
        if (!userProvidedIdFulfilled[_userProvidedId]) {
            return (_basePrice, 0, false);
        }

        uint256 randomValue = userProvidedIdToRandomValue[_userProvidedId];

        // Calculate variation factor between -_variationPercent and +_variationPercent
        variationFactor = int256(randomValue % (2 * _variationPercent + 1)) - int256(_variationPercent);

        // Apply variation to base price
        if (variationFactor >= 0) {
            finalPrice = _basePrice + (_basePrice * uint256(variationFactor) / 100);
        } else {
            finalPrice = _basePrice - (_basePrice * uint256(-variationFactor) / 100);
        }

        return (finalPrice, variationFactor, true);
    }

    /**
     * @notice Allows owner to update the Registry address (should rarely be needed)
     * @param _registry New Contract Registry address
     */
    function updateRegistry(address _registry) external onlyOwner {
        registry = _registry;
    }

    /**
     * @notice Allows owner to withdraw ETH from the contract
     */
    function withdraw() external onlyOwner {
        payable(owner).transfer(address(this).balance);
    }

    /**
     * @notice Fallback function to receive ETH
     */
    receive() external payable {}
}
