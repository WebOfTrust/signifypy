from typing import assert_type, cast

from signify.core.api import Operation as CompatOperation
from signify.keria_types import (
    ChallengeOperation,
    CompletedChallengeOperation,
    CompletedCredentialOperation,
    CompletedOperation,
    CompletedRegistryOperation,
    CredentialOperation,
    DelegationOperation,
    DoneOperation,
    FailedOperation,
    GroupOperation,
    JsonDict,
    Operation,
    OperationStatus,
    PendingOperation,
    RegistryOperation,
    WitnessOperation,
)


def check_operation_narrowing(op: Operation, compat: CompatOperation) -> None:
    assert_type(op, Operation)
    assert_type(compat, Operation)

    if op["done"]:
        assert_type(op, CompletedOperation | FailedOperation)
        if "error" in op:
            failed = cast(FailedOperation, op)
            assert_type(failed["error"], OperationStatus)
            assert_type(failed["error"]["code"], int)
            assert_type(failed["error"]["message"], str)
        else:
            assert_type(op, CompletedOperation)
    else:
        assert_type(op, PendingOperation)


def check_registry_contract(op: RegistryOperation) -> None:
    assert_type(op["metadata"]["pre"], str)
    depends = op["metadata"]["depends"]
    assert_type(depends, GroupOperation | WitnessOperation | DoneOperation | DelegationOperation)

    if op["done"] and "response" in op:
        completed = cast(CompletedRegistryOperation, op)
        assert_type(completed["response"]["anchor"], JsonDict)


def check_credential_contract(op: CredentialOperation) -> None:
    assert_type(op["metadata"]["ced"], JsonDict)

    if "depends" in op["metadata"]:
        assert_type(op["metadata"]["depends"], JsonDict | None)

    if op["done"] and "response" in op:
        completed = cast(CompletedCredentialOperation, op)
        assert_type(completed["response"]["ced"], JsonDict)


def check_challenge_contract(op: ChallengeOperation) -> None:
    assert_type(op["metadata"]["words"], list[str])

    if op["done"] and "response" in op:
        completed = cast(CompletedChallengeOperation, op)
        assert_type(completed["response"]["exn"], JsonDict)
