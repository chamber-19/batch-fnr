from pydantic import BaseModel, Field


class FnrPair(BaseModel):
    find: str
    replace: str
    case_sensitive: bool = False
    use_regex: bool = False


class FileError(BaseModel):
    file: str
    error: str


class MatchRow(BaseModel):
    file: str
    entity_type: str
    layer: str
    current_value: str
    proposed_value: str
    space: str


class PreviewRequest(BaseModel):
    files: list[str] = Field(default_factory=list)
    pairs: list[FnrPair] = Field(default_factory=list)


class ExecuteRequest(BaseModel):
    files: list[str] = Field(default_factory=list)
    pairs: list[FnrPair] = Field(default_factory=list)


class ScanFolderRequest(BaseModel):
    folder: str


class PreviewResponse(BaseModel):
    status: str
    matches: list[MatchRow]
    files_scanned: int
    total_matches: int
    errors: list[FileError]


class ExecuteResponse(BaseModel):
    status: str
    total_changes: int
    files_modified: int
    errors: list[FileError]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
