from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel as _BaseModel
from pydantic import Field

from qcflow.utils import IS_PYDANTIC_V2_OR_NEWER


class BaseModel(_BaseModel):
    @classmethod
    def validate_compat(cls, obj: Any):
        if IS_PYDANTIC_V2_OR_NEWER:
            return cls.model_validate(obj)
        else:
            return cls.parse_obj(obj)


class TextContentPart(BaseModel):
    type: Literal["text"]
    text: str


class ImageUrl(BaseModel):
    url: str  # either URL of an image, or bas64 encoded data
    detail: Literal["auto", "low", "high"]


class ImageContentPart(BaseModel):
    type: Literal["image_url"]
    image_url: ImageUrl


class InputAudio(BaseModel):
    data: str  # base64 encoded data
    format: Literal["wav", "mp3"]


class AudioContentPart(BaseModel):
    type: Literal["input_audio"]
    input_audio: InputAudio


ContentPartsList = list[
    Annotated[
        Union[TextContentPart, ImageContentPart, AudioContentPart], Field(discriminator="type")
    ]
]


ContentType = Annotated[Union[str, ContentPartsList], Field(union_mode="left_to_right")]


class Function(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    id: str
    type: Literal["function"]
    function: Function


class ChatMessage(BaseModel):
    """
    A chat request. ``content`` can be a string, or an array of content parts.

    A content part is one of the following:

    - :py:class:`TextContentPart <qcflow.types.chat.TextContentPart>`
    - :py:class:`ImageContentPart <qcflow.types.chat.ImageContentPart>`
    - :py:class:`AudioContentPart <qcflow.types.chat.AudioContentPart>`
    """

    role: str
    content: Optional[ContentType] = None
    # NB: In the actual OpenAI chat completion API spec, these fields only
    #   present in either the request or response message (tool_call_id is only in
    #   the request, while the other two are only in the response).
    #   Strictly speaking, we should separate the request and response message types
    #   to match OpenAI's API spec. However, we don't want to do that because we the
    #   request and response message types are not distinguished in many parts of the
    #   codebase, and also we don't want to ask users to use two different classes.
    #   Therefore, we include all fields in this class, while marking them as optional.
    # TODO: Define a sub classes for different type of messages (request/response, and
    #   system/user/assistant/tool, etc), and create a factory function to allow users
    #   to create them without worrying about the details.
    tool_calls: Optional[list[ToolCall]] = Field(None, min_items=1)
    refusal: Optional[str] = None
    tool_call_id: Optional[str] = None


class ParamType(BaseModel):
    type: Optional[Literal["string", "number", "integer", "object", "array", "boolean", "null"]] = (
        None
    )


class ParamProperty(ParamType):
    description: Optional[str] = None
    enum: Optional[list[str]] = None
    items: Optional[ParamType] = None


class FunctionParams(BaseModel):
    properties: dict[str, ParamProperty]
    type: Literal["object"] = "object"
    required: Optional[list[str]] = None
    additionalProperties: Optional[bool] = None


class FunctionToolDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Optional[FunctionParams] = None
    strict: Optional[bool] = None


class ChatTool(BaseModel):
    """A tool definition passed to the chat completion API."""

    type: Literal["function"]
    function: Optional[FunctionToolDefinition] = None


class BaseRequestPayload(BaseModel):
    """Common parameters used for chat completions and completion endpoints."""

    temperature: float = Field(0.0, ge=0, le=2)
    n: int = Field(1, ge=1)
    stop: Optional[list[str]] = Field(None, min_items=1)
    max_tokens: Optional[int] = Field(None, ge=1)
    stream: Optional[bool] = None
    model: Optional[str] = None


class ChatCompletionRequest(BaseRequestPayload):
    """
    A request to the chat completion API.

    Must be compatible with OpenAI's Chat Completion API.
    https://platform.openai.com/docs/api-reference/chat
    """

    messages: list[ChatMessage] = Field(..., min_items=1)
    tools: Optional[list[ChatTool]] = Field(None, min_items=1)


class ChatCompletionResponse(BaseModel):
    """
    A response from the chat completion API.

    Must be compatible with OpenAI's Chat Completion API.
    https://platform.openai.com/docs/api-reference/chat
    """

    id: Optional[str] = None
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]
    usage: ChatUsage


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


class ChatUsage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class ChatCompletionChunk(BaseModel):
    """A chunk of a chat completion stream response."""

    id: Optional[str] = None
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[ChatChunkChoice]


class ChatChoiceDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class ChatChunkChoice(BaseModel):
    index: int
    finish_reason: Optional[str] = None
    delta: ChatChoiceDelta
