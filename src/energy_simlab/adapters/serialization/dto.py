"""Pydantic edge DTOs generated from the frozen domain contract surface.

The DTO classes exist only in this adapter.  Every validated DTO is mapped to
a fresh standard-library dataclass before it can enter the application/domain.
"""

from __future__ import annotations

from dataclasses import MISSING, fields
from typing import Any, ClassVar, get_type_hints

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, create_model, model_validator

from energy_simlab.contracts.records import V1_DOMAIN_TYPES, VersionedV1


class ContractDTO(BaseModel):
    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        validate_default=True,
    )

    __domain_type__: ClassVar[type[VersionedV1]]

    @model_validator(mode="after")
    def validate_domain_semantics(self) -> ContractDTO:
        TypeAdapter(self.__domain_type__).validate_python(self.model_dump(mode="python"))
        return self


def _dto_for(domain_type: type[VersionedV1]) -> type[ContractDTO]:
    hints = get_type_hints(domain_type)
    definitions: dict[str, tuple[Any, Any]] = {}
    for field in fields(domain_type):
        if field.default is not MISSING:
            default: Any = field.default
        elif field.default_factory is not MISSING:
            default = Field(default_factory=field.default_factory)
        else:
            default = ...
        definitions[field.name] = (hints[field.name], default)

    dto_type = create_model(
        f"{domain_type.__name__}DTO",
        __base__=ContractDTO,
        __module__=__name__,
        **definitions,
    )
    dto_type.__domain_type__ = domain_type
    return dto_type


DTO_BY_DOMAIN: dict[type[VersionedV1], type[ContractDTO]] = {
    domain_type: _dto_for(domain_type) for domain_type in V1_DOMAIN_TYPES
}
DOMAIN_BY_DTO: dict[type[ContractDTO], type[VersionedV1]] = {
    dto_type: domain_type for domain_type, dto_type in DTO_BY_DOMAIN.items()
}

# Export stable class names such as CommandV1DTO for OpenAPI and adapter use.
globals().update({dto_type.__name__: dto_type for dto_type in DTO_BY_DOMAIN.values()})


def dto_type_for(domain_type: type[VersionedV1]) -> type[ContractDTO]:
    try:
        return DTO_BY_DOMAIN[domain_type]
    except KeyError as error:
        raise TypeError(f"unregistered V1 domain contract: {domain_type!r}") from error


def to_dto(record: VersionedV1) -> ContractDTO:
    dto_type = dto_type_for(type(record))
    return dto_type.model_validate(record, from_attributes=True)


def to_domain(dto: ContractDTO) -> VersionedV1:
    try:
        domain_type = DOMAIN_BY_DTO[type(dto)]
    except KeyError as error:
        raise TypeError(f"unregistered edge DTO: {type(dto)!r}") from error
    return TypeAdapter(domain_type).validate_python(dto.model_dump(mode="python"))


__all__ = [
    "ContractDTO",
    "DOMAIN_BY_DTO",
    "DTO_BY_DOMAIN",
    "dto_type_for",
    "to_domain",
    "to_dto",
    *(dto_type.__name__ for dto_type in DTO_BY_DOMAIN.values()),
]

