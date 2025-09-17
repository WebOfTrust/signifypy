from dataclasses import dataclass
from typing import List


@dataclass
class AgentBoot:
    """Data sent to a KERIA server to request an agent and pair the agent with this Signify Controller."""
    icp: dict  # inception event for the Signify Controller, sent so the Agent can have the Signify Controller's KEL
    sig: str  # qb64 encoded signature
    stem: str  # default unique path stem for salty algo for this Signify Controller's private key seed
    pidx: int  # prefix index (key index) for this keypair sequence
    tier: str  # security tier for stretch index salty algo

@dataclass
class Operation:
    name: str  # unique name for this operation
    metadata: dict  # metadata about the operation
    done: bool  # True if operation is complete
    error: bool | None  # True if operation failed, False if succeeded, None if not completed
    response: dict | None  # response data from operation, if any

@dataclass
class ReplyMessage:
    rpy: dict  # reply message content
    sigs: List[str] # list of qb64 encoded signatures
