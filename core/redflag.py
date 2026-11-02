"""Rule-based red-flag interface: scan_text(*texts) scans free patient text and check_alerts(record) scans a PatientRecord; both return list[Alert] with no network call, per docs/data_contract.md; no logic is implemented yet."""

from core.schema import Alert, PatientRecord


def scan_text(*texts: str) -> list[Alert]:
    raise NotImplementedError("scan_text is not implemented yet")


def check_alerts(record: PatientRecord) -> list[Alert]:
    raise NotImplementedError("check_alerts is not implemented yet")
