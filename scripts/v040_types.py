from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str
    severity: str = "ERROR"

    def format(self) -> str:
        return f"{self.severity}: {self.code}: {self.path}: {self.message}"


@dataclass
class ValidationResult:
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, code: str, path: str, message: str) -> None:
        self.errors.append(
            ValidationIssue(code=code, path=path, message=message, severity="ERROR")
        )

    def warning(self, code: str, path: str, message: str) -> None:
        self.warnings.append(
            ValidationIssue(code=code, path=path, message=message, severity="WARNING")
        )
