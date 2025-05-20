# Import packages
from dataclasses import dataclass
from typing import Final
from solders.pubkey import Pubkey

# Define 'LAMPORTS_PER_SOL'
LAMPORTS_PER_SOL: Final[int] = 1_000_000_000

# Define 'TOKEN_DECIMALS'
TOKEN_DECIMALS: Final[int] = 6


# Class 'SystemAddresses'
@dataclass
class SystemAddresses:
    """
    This dataclass defines the core system-level program addresses used across the Solana blockchain
    for native and token-based operations. These include the system program, SPL token program,
    associated token program, and rent sysvar, which are fundamental to account creation, token
    transfers, and resource allocation. These constants are immutable and are referenced in multiple
    modules to ensure consistency across all Solana interactions.

    Parameters:
    - PROGRAM (Pubkey): The standard system program address used for basic account operations.
    - TOKEN_PROGRAM (Pubkey): Address of the SPL Token Program for managing token minting and transfers.
    - ASSOCIATED_TOKEN_PROGRAM (Pubkey): Address used to derive associated token accounts for users.
    - RENT (Pubkey): Sysvar account that provides rent information for Solana accounts.
    - SOL (Pubkey): Wrapped SOL token program address used for SOL-to-token conversions.

    Returns:
    - None
    """

    PROGRAM: Final[Pubkey] = Pubkey.from_string("11111111111111111111111111111111")
    TOKEN_PROGRAM: Final[Pubkey] = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
    ASSOCIATED_TOKEN_PROGRAM: Final[Pubkey] = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
    RENT: Final[Pubkey] = Pubkey.from_string("SysvarRent111111111111111111111111111111111")
    SOL: Final[Pubkey] = Pubkey.from_string("So11111111111111111111111111111111111111112")


# Class 'PumpAddresses'
@dataclass
class PumpAddresses:
    """
    This dataclass contains all known on-chain program and system addresses used specifically
    by the Pump.fun ecosystem on the Solana blockchain. It includes program identifiers for global
    settings, fee processing, liquidity migration, and authority validation. These constants serve
    as trusted entry points for any operations performed with Pump contracts and are essential
    for transaction construction, event parsing, and cross-program interaction.

    Parameters:
    - PROGRAM (Pubkey): Main Pump.fun program address managing token creation and swaps.
    - GLOBAL (Pubkey): Global state account holding platform-wide configuration.
    - EVENT_AUTHORITY (Pubkey): Account responsible for authorizing program-generated events.
    - FEE (Pubkey): Account where Pump.fun collects protocol fees from swaps.
    - LIQUIDITY_MIGRATOR (Pubkey): Account managing migration of liquidity between older/newer pools.

    Returns:
    - None
    """

    PROGRAM: Final[Pubkey] = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
    GLOBAL: Final[Pubkey] = Pubkey.from_string("4wTV1YmiEkRvAtNtsSGPtUrqRYQMe5SKy2uB4Jjaxnjf")
    EVENT_AUTHORITY: Final[Pubkey] = Pubkey.from_string("Ce6TQqeHC9p8KetsN6JsjHK7UTZk7nasjjnr7XxXp9F1")
    FEE: Final[Pubkey] = Pubkey.from_string("CebN5WGQ4jvEPvsVU4EoHEpgzq1VV7AbicfhtW4xC9iM")
    LIQUIDITY_MIGRATOR: Final[Pubkey] = Pubkey.from_string("39azUYFWPz3VHgKCf3VChUwbpURdCHRxjWVowf5jUJjg")