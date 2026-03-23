from pydantic import BaseModel, ConfigDict, Field


class Pricing(BaseModel):
    model_config = ConfigDict(extra="ignore")

    prompt: float | None = None
    completion: float | None = None


class TopProvider(BaseModel):
    model_config = ConfigDict(extra="ignore")

    context_length: int | None = None
    max_completion_tokens: int | None = None
    is_moderated: bool | None = None


class ModelInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str | None = None
    description: str | None = None
    pricing: Pricing | None = None
    context_length: int | None = None
    supported_parameters: list[str] = Field(default_factory=list)
    top_provider: TopProvider | None = None
    input_modalities: list[str] = Field(default_factory=list)
    output_modalities: list[str] = Field(default_factory=list)
