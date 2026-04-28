# -*- encoding: utf-8 -*-
"""Runtime checks for the exported SignifyPy KERIA typing surface."""

from typing import get_args


def test_keria_types_exports_are_available():
    from signify import keria_types
    from signify.core import api

    assert "Operation" in keria_types.__all__
    assert "RegistryOperation" in keria_types.__all__
    assert keria_types.OPERATION_FAMILY_NAMES[0] == "OOBIOperation"
    assert len(get_args(api.Operation)) >= len(keria_types.OPERATION_FAMILY_NAMES)


def test_core_api_reexports_operation_status():
    from signify.core.api import OperationStatus

    sample: OperationStatus = {"code": 400, "message": "bad request"}

    assert sample["code"] == 400
    assert sample["message"] == "bad request"
