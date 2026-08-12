from decimal import Decimal

from backend.core.exceptions import AppError
from backend.modules.d7_evidence.categories import is_smartphone_type
from backend.modules.d7_evidence.geospatial import has_valid_coordinates


def normalize_imei(imei: str | None) -> str | None:
    if imei is None:
        return None
    cleaned = "".join(ch for ch in imei.strip() if ch.isdigit())
    return cleaned or None


def is_valid_imei(imei: str) -> bool:
    if len(imei) != 15 or not imei.isdigit():
        return False
    total = 0
    for index, digit_char in enumerate(imei):
        digit = int(digit_char)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def validate_imei(imei: str | None, *, required: bool = False, field_name: str = "IMEI") -> str | None:
    normalized = normalize_imei(imei)
    if normalized is None:
        if required:
            raise AppError("invalid_imei", f"{field_name} is required", status_code=422)
        return None
    if not is_valid_imei(normalized):
        raise AppError(
            "invalid_imei",
            f"{field_name} must be 15 digits with a valid check digit",
            status_code=422,
        )
    return normalized


def validate_coordinates(
    latitude: Decimal | None,
    longitude: Decimal | None,
) -> None:
    if latitude is None and longitude is None:
        return
    if latitude is None or longitude is None:
        raise AppError(
            "invalid_coordinates",
            "Both latitude and longitude must be provided together",
            status_code=422,
        )
    if not has_valid_coordinates(latitude, longitude):
        raise AppError(
            "invalid_coordinates",
            "Coordinates must be within valid latitude (-90 to 90) and longitude (-180 to 180) ranges",
            status_code=422,
        )


def validate_evidence_fields(
    *,
    evidence_type: str,
    brand: str | None,
    imei_slot1: str | None,
    imei_slot2: str | None,
    serial_number: str | None,
    location_latitude: Decimal | None,
    location_longitude: Decimal | None,
) -> tuple[str | None, str | None]:
    smartphone = is_smartphone_type(evidence_type)
    normalized_slot1 = validate_imei(
        imei_slot1,
        required=smartphone,
        field_name="IMEI slot 1",
    )
    normalized_slot2 = validate_imei(
        imei_slot2,
        required=False,
        field_name="IMEI slot 2",
    )

    if smartphone:
        if not (brand and brand.strip()):
            raise AppError("invalid_brand", "Brand is required for smartphone evidence", status_code=422)
        if not (serial_number and serial_number.strip()):
            raise AppError(
                "invalid_serial_number",
                "Serial number is required for smartphone evidence",
                status_code=422,
            )
    else:
        if normalized_slot1 is not None:
            validate_imei(normalized_slot1, required=True, field_name="IMEI slot 1")
        if normalized_slot2 is not None:
            validate_imei(normalized_slot2, required=True, field_name="IMEI slot 2")

    if (
        normalized_slot1
        and normalized_slot2
        and normalized_slot1 == normalized_slot2
    ):
        raise AppError(
            "invalid_imei",
            "IMEI slot 1 and slot 2 must be different when both are provided",
            status_code=422,
        )

    validate_coordinates(location_latitude, location_longitude)
    return normalized_slot1, normalized_slot2
