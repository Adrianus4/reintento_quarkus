from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator


class RunCreateRequest(BaseModel):
    client_code: str = Field(..., min_length=2, max_length=64)
    job_id: Optional[str] = None
    files: Union[Dict[str, str], List[Dict[str, str]]] = Field(
        ...,
        description="Dictionary mapping relative file paths to content strings, or list of file dicts"
    )
    auto_verify: bool = True

    @model_validator(mode="before")
    @classmethod
    def normalize_files(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_files = data.get("files")
            if isinstance(raw_files, list):
                files_map = {}
                for item in raw_files:
                    if isinstance(item, dict) and "path" in item and "content" in item:
                        files_map[item["path"]] = str(item["content"])
                data["files"] = files_map
        return data


class FileHash(BaseModel):
    path: str
    sha256: str
    size_bytes: int


class VerificationManifest(BaseModel):
    version: str
    generated_at: str
    run_id: str
    client_code: str
    verification_status: str
    total_files: int
    files: List[FileHash]


class RunResponse(BaseModel):
    id: str
    user_id: str
    client_code: str
    job_id: Optional[str] = None
    status: str
    compilation_output: Optional[str] = None
    duration_ms: int
    manifest: Optional[Dict[str, Any]] = None
    download_url: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

