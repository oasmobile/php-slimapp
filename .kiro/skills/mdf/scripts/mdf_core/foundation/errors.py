import json
from dataclasses import dataclass
from typing import Any, Iterable


class MDFError(RuntimeError):
    """An expected user-facing CLI failure."""

    def __init__(
        self, message: str, *, code: str = "mdf_error", details: Any = None
    ):
        super().__init__(message)
        self.code = code
        self.details = details


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    path: str | None = None
    severity: str = "error"

    def as_dict(self, finding_id: str | None = None) -> dict[str, Any]:
        result: dict[str, Any] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.path:
            result["path"] = self.path
        if finding_id:
            result["id"] = finding_id
        return result


def serialize_findings(findings: Iterable[Finding]) -> list[dict[str, Any]]:
    return [
        finding.as_dict(f"MDF-{index:04d}")
        for index, finding in enumerate(findings, start=1)
    ]


def has_errors(findings: Iterable[Finding]) -> bool:
    return any(finding.severity == "error" for finding in findings)


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)


def add_finding(
    findings: list[Finding],
    code: str,
    message: str,
    path: str | None = None,
    severity: str = "error",
) -> None:
    findings.append(Finding(code, message, path, severity))
