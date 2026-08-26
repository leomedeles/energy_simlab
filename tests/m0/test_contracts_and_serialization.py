from dataclasses import fields, is_dataclass
import json
from math import inf, nan

import pytest
from pydantic import BaseModel, ValidationError

from energy_simlab.adapters.serialization import (
    canonical_json_bytes,
    dto_type_for,
    parse_json_bytes,
    to_domain,
    to_dto,
)
from energy_simlab.contracts.enums import (
    AcknowledgementReason,
    AcknowledgementStatus,
    CommandAuthority,
    CommandKind,
    Unit,
)
from energy_simlab.contracts.records import AcknowledgementV1, CommandV1, V1_DOMAIN_TYPES

from .samples import sample_records


@pytest.mark.parametrize("record", sample_records(), ids=lambda item: type(item).__name__)
def test_every_v1_contract_round_trips_through_edge_dto_and_json(record):
    dto = to_dto(record)
    assert isinstance(dto, BaseModel)
    assert to_domain(dto) == record
    payload = canonical_json_bytes(record)
    assert parse_json_bytes(type(record), payload) == record
    assert payload == canonical_json_bytes(parse_json_bytes(type(record), payload))


def test_contract_registry_and_dto_registry_are_complete():
    assert {type(record) for record in sample_records()} == set(V1_DOMAIN_TYPES)
    assert all(dto_type_for(domain_type).__name__ == f"{domain_type.__name__}DTO" for domain_type in V1_DOMAIN_TYPES)


def test_equivalent_json_key_orders_have_identical_canonical_bytes():
    command = next(item for item in sample_records() if isinstance(item, CommandV1))
    canonical = canonical_json_bytes(command)
    values = json.loads(canonical)
    reversed_payload = json.dumps(dict(reversed(tuple(values.items())))).encode()
    reparsed = parse_json_bytes(CommandV1, reversed_payload)
    assert canonical_json_bytes(reparsed) == canonical


@pytest.mark.parametrize("bad_value", [nan, inf, -inf])
def test_non_finite_values_are_rejected_by_domain_and_edge(bad_value):
    with pytest.raises(ValueError, match="finite"):
        CommandV1(
            id="CMD-BAD",
            source_id="operator",
            logical_tick=0,
            sequence=1,
            target_id="BESS",
            kind=CommandKind.SET_ACTIVE_POWER,
            authority=CommandAuthority.OPERATOR,
            apply_tick=10,
            expiry_tick=20,
            requested_value=bad_value,
            unit=Unit.MEGAWATT,
        )

    payload = canonical_json_bytes(next(item for item in sample_records() if isinstance(item, CommandV1)))
    values = json.loads(payload)
    values["requested_value"] = bad_value
    with pytest.raises(ValidationError):
        dto_type_for(CommandV1).model_validate(values)


def test_wrong_major_version_is_rejected():
    command = next(item for item in sample_records() if isinstance(item, CommandV1))
    values = json.loads(canonical_json_bytes(command))
    values["schema_version"] = "2.0.0"
    with pytest.raises(ValidationError, match="unsupported schema version"):
        dto_type_for(CommandV1).model_validate(values)


def test_wrong_unit_is_rejected():
    command = next(item for item in sample_records() if isinstance(item, CommandV1))
    values = json.loads(canonical_json_bytes(command))
    values["unit"] = Unit.MEGAWATT_HOUR.value
    with pytest.raises(ValidationError, match="unit MW"):
        dto_type_for(CommandV1).model_validate(values)


@pytest.mark.parametrize("missing_field", ["command_id", "correlation_id"])
def test_missing_causal_fields_are_rejected(missing_field):
    acknowledgement = next(item for item in sample_records() if isinstance(item, AcknowledgementV1))
    values = json.loads(canonical_json_bytes(acknowledgement))
    del values[missing_field]
    with pytest.raises(ValidationError, match=missing_field):
        dto_type_for(AcknowledgementV1).model_validate(values)


def test_empty_causal_fields_are_rejected():
    with pytest.raises(ValueError, match="correlation_id"):
        AcknowledgementV1(
            id="ACK-BAD",
            source_id="validator",
            logical_tick=1,
            sequence=1,
            command_id="CMD-1",
            correlation_id="",
            target_id="BESS",
            status=AcknowledgementStatus.REJECTED,
            reason=AcknowledgementReason.UNKNOWN_TARGET,
            detail="unknown target",
            effective_tick=1,
            requested_value=0.1,
            accepted_value=None,
            unit=Unit.MEGAWATT,
            model_version="1.0.0",
            topology_version=0,
        )


def test_pydantic_objects_do_not_enter_nested_domain_state():
    record = max(sample_records(), key=lambda item: len(fields(item)))
    domain = to_domain(to_dto(record))

    def assert_domain_only(value):
        assert not isinstance(value, BaseModel)
        if is_dataclass(value):
            for field in fields(value):
                assert_domain_only(getattr(value, field.name))
        elif isinstance(value, (tuple, list)):
            for item in value:
                assert_domain_only(item)

    assert_domain_only(domain)

