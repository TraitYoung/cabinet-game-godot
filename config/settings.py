"""Validated startup settings. Importing this module never reads local secrets."""

from collections.abc import Mapping
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="ignore", str_strip_whitespace=True)

    db_path: str = Field(default=str(ROOT / "data/axiodrasil_core.db"), alias="AX_DB_PATH")
    llm_provider: Literal["deepseek", "qwen"] = Field(default="deepseek", alias="AX_LLM_PROVIDER")
    chat_model: str = Field(default="", alias="AX_CHAT_MODEL")
    deepseek_api_key: SecretStr = Field(default=SecretStr(""), alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_thinking: bool = Field(default=False, alias="AX_DEEPSEEK_THINKING")
    qwen_api_key: SecretStr = Field(default=SecretStr(""), alias="QWEN_API_KEY")
    qwen_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1", alias="QWEN_BASE_URL"
    )
    memory_user_id: str = Field(default="bina-local-user", alias="AX_MEMORY_USER_ID")
    hindsight_url: str = Field(default="http://127.0.0.1:8888", alias="AX_HINDSIGHT_URL")
    hindsight_api_key: SecretStr = Field(default=SecretStr(""), alias="AX_HINDSIGHT_API_KEY")
    interaction_hooks: bool = Field(default=True, alias="AX_INTERACTION_HOOKS_ENABLED")
    reunion_gap_minutes: float = Field(default=120, ge=0, alias="AX_REUNION_GAP_MINUTES")
    mood_observation: float = Field(default=0.2, ge=0, le=1, alias="AX_MOOD_OBS_THRESHOLD")
    mood_contact: float = Field(default=0.35, ge=0, le=1, alias="AX_MOOD_CONTACT_THRESHOLD")
    mood_force_contact: float = Field(default=0.5, ge=0, le=1, alias="AX_MOOD_FORCE_CONTACT_THRESHOLD")
    mood_pride_block: float = Field(default=0.5, ge=-1, le=1, alias="AX_MOOD_PRIDE_BLOCK")
    proactive_enabled: bool = Field(default=True, alias="AX_PROACTIVE_ENABLED")
    proactive_interval: int = Field(default=300, ge=30, alias="AX_PROACTIVE_INTERVAL_SEC")
    proactive_cooldown: float = Field(default=45, ge=0, alias="AX_PROACTIVE_COOLDOWN_MIN")
    proactive_quiet_start: int = Field(default=0, ge=0, le=23, alias="AX_PROACTIVE_QUIET_START")
    proactive_quiet_end: int = Field(default=8, ge=0, le=23, alias="AX_PROACTIVE_QUIET_END")
    search_enabled: bool = Field(default=False, alias="AX_SEARCH_ENABLED")
    image_enabled: bool = Field(default=True, alias="AX_IMAGE_GEN_ENABLED")
    image_out_dir: str = Field(default=str(ROOT / "data/generated"), alias="AX_IMAGE_OUT_DIR")
    comfyui_url: str = Field(default="http://127.0.0.1:8188", alias="AX_COMFYUI_URL")
    comfyui_checkpoint: str = Field(default="sd_xl_base_1.0.safetensors", alias="AX_COMFYUI_CKPT")
    comfyui_width: int | None = Field(default=None, gt=0, alias="AX_COMFYUI_WIDTH")
    comfyui_height: int | None = Field(default=None, gt=0, alias="AX_COMFYUI_HEIGHT")
    comfyui_steps: int | None = Field(default=None, gt=0, alias="AX_COMFYUI_STEPS")
    comfyui_cfg: float | None = Field(default=None, gt=0, alias="AX_COMFYUI_CFG")
    comfyui_sampler: str = Field(default="euler", alias="AX_COMFYUI_SAMPLER")
    comfyui_scheduler: str = Field(default="normal", alias="AX_COMFYUI_SCHEDULER")
    bina_positive_prompt: str = Field(default="", alias="AX_BINA_POSITIVE_PROMPT")
    bina_negative_prompt: str = Field(default="", alias="AX_BINA_NEGATIVE_PROMPT")
    bina_lora: str = Field(default="", alias="AX_BINA_LORA")
    bina_lora_weight: float = Field(default=0.85, ge=0, le=2, alias="AX_BINA_LORA_WEIGHT")
    bina_lora_trigger: str = Field(default="", alias="AX_BINA_LORA_TRIGGER")
    stt_model: str = Field(default="qwen2-audio-instruct", alias="AX_STT_MODEL")
    vl_model: str = Field(default="qwen-vl-plus", alias="AX_VL_MODEL")

    @model_validator(mode="after")
    def normalize(self):
        if not self.chat_model:
            object.__setattr__(
                self, "chat_model", "deepseek-flash" if self.llm_provider == "deepseek" else "qwen-plus"
            )
        object.__setattr__(self, "deepseek_base_url", self.deepseek_base_url.rstrip("/").removesuffix("/v1"))
        if not self.db_path:
            raise ValueError("AX_DB_PATH must not be empty")
        if not self.memory_user_id:
            object.__setattr__(self, "memory_user_id", "bina-local-user")
        return self

    @classmethod
    def load(cls, env: Mapping[str, str] | None = None, env_file: Path | None = ROOT / ".env"):
        from dotenv import dotenv_values

        raw = dict(dotenv_values(env_file)) if env_file and env_file.exists() else {}
        raw.update(os.environ if env is None else env)
        for name, alias in {
            "AX_CHAT_MODEL": "LLM_MODEL",
            "DEEPSEEK_API_KEY": "LLM_API_KEY",
            "DEEPSEEK_BASE_URL": "LLM_BASE_URL",
            "AX_COMFYUI_CKPT": "AX_COMFYUI_CHECKPOINT",
        }.items():
            if not raw.get(name) and raw.get(alias):
                raw[name] = raw[alias]
        # Empty optional settings use the documented defaults, never an invalid empty number.
        return cls.model_validate({key: value for key, value in raw.items() if value not in (None, "")})
