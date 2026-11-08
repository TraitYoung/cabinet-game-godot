"""Current Bina turn contract and durable result format (version 1)."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from schemas.protocols import TaskIntent


class RequestStatus(StrEnum):
    GENERATING = "generating"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMMITTING = "committing"
    COMPLETED = "completed"


class TurnRequest(BaseModel):
    request_id: str | None = Field(default=None, min_length=1, max_length=128)
    model: str | None = None
    reasoning_effort: Literal["off", "low", "high", "max"] | None = None
    text: str = Field(..., min_length=1, max_length=12000, description="用户输入")
    workflow_mode: Literal["default", "dev_pipeline"] = Field(
        default="default", description="仅 default 有效；dev_pipeline 为已归档的兼容值，返回 410"
    )
    forced_persona: str | None = Field(default=None, description="历史兼容字段；当前始终由 Bina 回复")
    strip_persona_prefix: bool = Field(default=False, description="是否省略回复中的 Bina 标签")
    group_mode: bool | None = Field(default=None, description="历史兼容字段；不启用群聊")
    memory_thread_id: str | None = Field(default=None, exclude=True)


class TurnResult(BaseModel):
    reply: str
    intent: TaskIntent
    trace_raw: list[dict] = Field(default_factory=list)
    active_task_type: str
    active_persona: str

    def to_saved(self) -> dict:
        return {"version": 1, **self.model_dump()}

    @classmethod
    def from_saved(cls, saved: dict):
        version = saved.get("version", 1)  # Compatibility with the initial unversioned format.
        if version != 1:
            raise ValueError(f"Unsupported saved turn version: {version}")
        return cls.model_validate({key: value for key, value in saved.items() if key != "version"})


class RequestRecord(BaseModel):
    session_id: str
    request_id: str
    fingerprint: str | None = None
    status: RequestStatus
    result: str | None = None
    recorded_at: str | None = None

    # Kept for callers of the initial store API while internals use typed attributes.
    def __getitem__(self, key: str):
        return getattr(self, key)


class RequestState(BaseModel):
    status: RequestStatus
    result: TurnResult | None = None
