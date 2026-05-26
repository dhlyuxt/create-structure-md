from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationIssue:
    level: str
    code: str
    json_path: str
    message: str

    def format(self) -> str:
        return f"{self.level}: {self.code}: {self.json_path}: {self.message}"


@dataclass
class ValidationResult:
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, code: str, json_path: str, message: str) -> None:
        self.errors.append(ValidationIssue("ERROR", code, json_path, message))

    def warn(self, code: str, json_path: str, message: str) -> None:
        self.warnings.append(ValidationIssue("WARNING", code, json_path, message))

    def extend(self, other: "ValidationResult") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def json_path(parts) -> str:
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path
