"""Copied KERIA long-running operation contracts for SignifyPy consumers.

This module mirrors the strong operation typing exposed by modern KERIA. It is
deliberately isolated from both SignifyPy app code and KERIA runtime imports so
the implementation can later be swapped to a shared contract package without
changing public SignifyPy imports.
"""

from __future__ import annotations

from typing import Literal, NotRequired, TypeAlias, TypedDict

from .common import JsonDict

OperationKind: TypeAlias = Literal[
    "oobi",
    "query",
    "endrole",
    "witness",
    "delegation",
    "registry",
    "locscheme",
    "challenge",
    "exchange",
    "submit",
    "done",
    "credential",
    "group",
    "delegator",
]

OPERATION_FAMILY_NAMES = (
    "OOBIOperation",
    "QueryOperation",
    "EndRoleOperation",
    "WitnessOperation",
    "DelegationOperation",
    "RegistryOperation",
    "LocSchemeOperation",
    "ChallengeOperation",
    "ExchangeOperation",
    "SubmitOperation",
    "DoneOperation",
    "CredentialOperation",
    "GroupOperation",
    "DelegatorOperation",
)


class OperationStatus(TypedDict):
    """Failure status returned for completed error operations."""

    code: int
    message: str
    details: NotRequired[JsonDict | None]


class BaseOperation(TypedDict):
    """Minimal shared operation envelope."""

    name: str


class OOBIMetadata(TypedDict):
    oobi: str


class QueryMetadata(TypedDict):
    pre: str
    sn: int
    anchor: NotRequired[JsonDict]


class WitnessMetadata(TypedDict):
    pre: str
    sn: int


class DelegationMetadata(TypedDict):
    pre: str
    sn: int


class DoneOperationMetadata(TypedDict):
    response: JsonDict
    pre: NotRequired[str | None]


class GroupOperationMetadata(TypedDict):
    pre: str
    sn: int


class SubmitOperationMetadata(TypedDict):
    pre: str
    sn: int


class EndRoleMetadata(TypedDict):
    cid: str
    role: str
    eid: str


class LocSchemeMetadata(TypedDict):
    eid: str
    scheme: str
    url: str


class ChallengeOperationMetadata(TypedDict):
    words: list[str]


class ChallengeOperationResponse(TypedDict):
    exn: JsonDict


class ExchangeOperationMetadata(TypedDict):
    said: str


class RegistryOperationResponse(TypedDict):
    anchor: JsonDict


class CredentialOperationResponse(TypedDict):
    ced: JsonDict


class PendingOOBIOperation(BaseOperation):
    metadata: OOBIMetadata
    done: Literal[False]


class CompletedOOBIOperation(BaseOperation):
    metadata: OOBIMetadata
    response: JsonDict
    done: Literal[True]


class FailedOOBIOperation(BaseOperation):
    metadata: OOBIMetadata
    error: OperationStatus
    done: Literal[True]


OOBIOperation: TypeAlias = (
    PendingOOBIOperation | CompletedOOBIOperation | FailedOOBIOperation
)


class PendingQueryOperation(BaseOperation):
    metadata: QueryMetadata
    done: Literal[False]


class CompletedQueryOperation(BaseOperation):
    metadata: QueryMetadata
    response: JsonDict
    done: Literal[True]


class FailedQueryOperation(BaseOperation):
    metadata: QueryMetadata
    error: OperationStatus
    done: Literal[True]


QueryOperation: TypeAlias = (
    PendingQueryOperation | CompletedQueryOperation | FailedQueryOperation
)


class PendingWitnessOperation(BaseOperation):
    metadata: WitnessMetadata
    done: Literal[False]


class CompletedWitnessOperation(BaseOperation):
    metadata: WitnessMetadata
    response: JsonDict
    done: Literal[True]


class FailedWitnessOperation(BaseOperation):
    metadata: WitnessMetadata
    error: OperationStatus
    done: Literal[True]


WitnessOperation: TypeAlias = (
    PendingWitnessOperation | CompletedWitnessOperation | FailedWitnessOperation
)


class PendingDelegationOperation(BaseOperation):
    metadata: DelegationMetadata
    done: Literal[False]


class CompletedDelegationOperation(BaseOperation):
    metadata: DelegationMetadata
    response: JsonDict
    done: Literal[True]


class FailedDelegationOperation(BaseOperation):
    metadata: DelegationMetadata
    error: OperationStatus
    done: Literal[True]


DelegationOperation: TypeAlias = (
    PendingDelegationOperation
    | CompletedDelegationOperation
    | FailedDelegationOperation
)


class PendingDoneOperation(BaseOperation):
    metadata: DoneOperationMetadata
    done: Literal[False]


class CompletedDoneOperation(BaseOperation):
    metadata: DoneOperationMetadata
    response: JsonDict
    done: Literal[True]


class FailedDoneOperation(BaseOperation):
    metadata: DoneOperationMetadata
    error: OperationStatus
    done: Literal[True]


DoneOperation: TypeAlias = (
    PendingDoneOperation | CompletedDoneOperation | FailedDoneOperation
)


class PendingGroupOperation(BaseOperation):
    metadata: GroupOperationMetadata
    done: Literal[False]


class CompletedGroupOperation(BaseOperation):
    metadata: GroupOperationMetadata
    response: JsonDict
    done: Literal[True]


class FailedGroupOperation(BaseOperation):
    metadata: GroupOperationMetadata
    error: OperationStatus
    done: Literal[True]


GroupOperation: TypeAlias = (
    PendingGroupOperation | CompletedGroupOperation | FailedGroupOperation
)

DependencyOperation: TypeAlias = (
    GroupOperation | WitnessOperation | DoneOperation | DelegationOperation
)


class DelegatorOperationMetadata(TypedDict):
    pre: str
    teepre: str
    anchor: NotRequired[JsonDict]
    depends: NotRequired[GroupOperation | WitnessOperation | DoneOperation]


class PendingDelegatorOperation(BaseOperation):
    metadata: DelegatorOperationMetadata
    done: Literal[False]


class CompletedDelegatorOperation(BaseOperation):
    metadata: DelegatorOperationMetadata
    response: str
    done: Literal[True]


class FailedDelegatorOperation(BaseOperation):
    metadata: DelegatorOperationMetadata
    error: OperationStatus
    done: Literal[True]


DelegatorOperation: TypeAlias = (
    PendingDelegatorOperation
    | CompletedDelegatorOperation
    | FailedDelegatorOperation
)


class PendingSubmitOperation(BaseOperation):
    metadata: SubmitOperationMetadata
    done: Literal[False]


class CompletedSubmitOperation(BaseOperation):
    metadata: SubmitOperationMetadata
    response: JsonDict
    done: Literal[True]


class FailedSubmitOperation(BaseOperation):
    metadata: SubmitOperationMetadata
    error: OperationStatus
    done: Literal[True]


SubmitOperation: TypeAlias = (
    PendingSubmitOperation | CompletedSubmitOperation | FailedSubmitOperation
)


class PendingEndRoleOperation(BaseOperation):
    metadata: EndRoleMetadata
    done: Literal[False]


class CompletedEndRoleOperation(BaseOperation):
    metadata: EndRoleMetadata
    response: JsonDict
    done: Literal[True]


class FailedEndRoleOperation(BaseOperation):
    metadata: EndRoleMetadata
    error: OperationStatus
    done: Literal[True]


EndRoleOperation: TypeAlias = (
    PendingEndRoleOperation | CompletedEndRoleOperation | FailedEndRoleOperation
)


class PendingLocSchemeOperation(BaseOperation):
    metadata: LocSchemeMetadata
    done: Literal[False]


class CompletedLocSchemeOperation(BaseOperation):
    metadata: LocSchemeMetadata
    response: LocSchemeMetadata
    done: Literal[True]


class FailedLocSchemeOperation(BaseOperation):
    metadata: LocSchemeMetadata
    error: OperationStatus
    done: Literal[True]


LocSchemeOperation: TypeAlias = (
    PendingLocSchemeOperation
    | CompletedLocSchemeOperation
    | FailedLocSchemeOperation
)


class PendingChallengeOperation(BaseOperation):
    metadata: ChallengeOperationMetadata
    done: Literal[False]


class CompletedChallengeOperation(BaseOperation):
    metadata: ChallengeOperationMetadata
    response: ChallengeOperationResponse
    done: Literal[True]


class FailedChallengeOperation(BaseOperation):
    metadata: ChallengeOperationMetadata
    error: OperationStatus
    done: Literal[True]


ChallengeOperation: TypeAlias = (
    PendingChallengeOperation
    | CompletedChallengeOperation
    | FailedChallengeOperation
)


class RegistryOperationMetadata(TypedDict):
    pre: str
    depends: DependencyOperation
    anchor: JsonDict


class PendingRegistryOperation(BaseOperation):
    metadata: RegistryOperationMetadata
    done: Literal[False]


class CompletedRegistryOperation(BaseOperation):
    metadata: RegistryOperationMetadata
    response: RegistryOperationResponse
    done: Literal[True]


class FailedRegistryOperation(BaseOperation):
    metadata: RegistryOperationMetadata
    error: OperationStatus
    done: Literal[True]


RegistryOperation: TypeAlias = (
    PendingRegistryOperation
    | CompletedRegistryOperation
    | FailedRegistryOperation
)


class CredentialOperationMetadata(TypedDict):
    ced: JsonDict
    depends: NotRequired[JsonDict | None]


class PendingCredentialOperation(BaseOperation):
    metadata: CredentialOperationMetadata
    done: Literal[False]


class CompletedCredentialOperation(BaseOperation):
    metadata: CredentialOperationMetadata
    response: CredentialOperationResponse
    done: Literal[True]


class FailedCredentialOperation(BaseOperation):
    metadata: CredentialOperationMetadata
    error: OperationStatus
    done: Literal[True]


CredentialOperation: TypeAlias = (
    PendingCredentialOperation
    | CompletedCredentialOperation
    | FailedCredentialOperation
)


class PendingExchangeOperation(BaseOperation):
    metadata: ExchangeOperationMetadata
    done: Literal[False]


class CompletedExchangeOperation(BaseOperation):
    metadata: ExchangeOperationMetadata
    response: ExchangeOperationMetadata
    done: Literal[True]


class FailedExchangeOperation(BaseOperation):
    metadata: ExchangeOperationMetadata
    error: OperationStatus
    done: Literal[True]


ExchangeOperation: TypeAlias = (
    PendingExchangeOperation
    | CompletedExchangeOperation
    | FailedExchangeOperation
)


PendingOperation: TypeAlias = (
    PendingOOBIOperation
    | PendingQueryOperation
    | PendingEndRoleOperation
    | PendingWitnessOperation
    | PendingDelegationOperation
    | PendingRegistryOperation
    | PendingLocSchemeOperation
    | PendingChallengeOperation
    | PendingExchangeOperation
    | PendingSubmitOperation
    | PendingDoneOperation
    | PendingCredentialOperation
    | PendingGroupOperation
    | PendingDelegatorOperation
)

CompletedOperation: TypeAlias = (
    CompletedOOBIOperation
    | CompletedQueryOperation
    | CompletedEndRoleOperation
    | CompletedWitnessOperation
    | CompletedDelegationOperation
    | CompletedRegistryOperation
    | CompletedLocSchemeOperation
    | CompletedChallengeOperation
    | CompletedExchangeOperation
    | CompletedSubmitOperation
    | CompletedDoneOperation
    | CompletedCredentialOperation
    | CompletedGroupOperation
    | CompletedDelegatorOperation
)

FailedOperation: TypeAlias = (
    FailedOOBIOperation
    | FailedQueryOperation
    | FailedEndRoleOperation
    | FailedWitnessOperation
    | FailedDelegationOperation
    | FailedRegistryOperation
    | FailedLocSchemeOperation
    | FailedChallengeOperation
    | FailedExchangeOperation
    | FailedSubmitOperation
    | FailedDoneOperation
    | FailedCredentialOperation
    | FailedGroupOperation
    | FailedDelegatorOperation
)

Operation: TypeAlias = PendingOperation | CompletedOperation | FailedOperation
