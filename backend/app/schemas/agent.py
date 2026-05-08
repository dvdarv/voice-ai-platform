from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Agent Schemas
class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: str = Field(..., min_length=1)
    
    # LLM Configuration
    llm_provider: str = "openai"  # openai, anthropic, google, cartesia
    llm_model: str = "gpt-4-turbo"
    temperature: float = 0.8  # 0-2
    max_output_tokens: Optional[int] = None
    
    # Voice Configuration
    voice: str = "alloy"  # OpenAI voices: alloy, echo, fable, onyx, nova, shimmer
    greeting: Optional[str] = None  # Initial greeting message
    
    # Turn Detection
    turn_detection: str = "semantic"  # semantic, timed, disabled
    interrupt_min_words: int = 0
    min_endpointing_delay: str = "0.3s"
    max_endpointing_delay: str = "3s"
    
    # VAD (Voice Activity Detection)
    vad_enabled: bool = True
    vad_model: str = "silero"  # silero, onnx
    
    # Timeout Settings
    idle_timeout: str = "5m"
    max_duration: str = "30m"
    waiting_for_user_timeout: str = "30s"
    
    # Audio Settings
    audio_sample_rate: int = 16000
    audio_channels: int = 1
    
    # Capabilities
    tools: List[Dict[str, Any]] = []
    webhooks: List[Dict[str, Any]] = []
    
    # Status
    is_active: bool = True
    phone_number: Optional[str] = None


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    
    # LLM Configuration
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    temperature: Optional[float] = None
    max_output_tokens: Optional[int] = None
    
    # Voice Configuration
    voice: Optional[str] = None
    greeting: Optional[str] = None
    
    # LLM Configuration
    llm_type: Optional[str] = None
    
    # TTS/STT Configuration
    tts_provider: Optional[str] = None
    tts_voice: Optional[str] = None
    stt_provider: Optional[str] = None
    
    # Turn Detection
    turn_detection: Optional[str] = None
    interrupt_min_words: Optional[int] = None
    min_endpointing_delay: Optional[str] = None
    max_endpointing_delay: Optional[str] = None
    
    # VAD
    vad_enabled: Optional[bool] = None
    vad_model: Optional[str] = None
    
    # Timeout Settings
    idle_timeout: Optional[str] = None
    max_duration: Optional[str] = None
    waiting_for_user_timeout: Optional[str] = None
    
    # Audio Settings
    audio_sample_rate: Optional[int] = None
    audio_channels: Optional[int] = None
    
    # Capabilities
    tools: Optional[List[Dict[str, Any]]] = None
    webhooks: Optional[List[Dict[str, Any]]] = None
    
    # Status
    is_active: Optional[bool] = None
    phone_number: Optional[str] = None


class AgentResponse(AgentBase):
    id: str
    phone_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AgentWithStats(AgentResponse):
    total_calls: int = 0
    total_cost: float = 0.0


# LLM Provider options
LLM_PROVIDERS = {
    "openai": {
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
        "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    },
    "anthropic": {
        "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-3-5-sonnet-latest", "claude-3-opus-latest", "claude-3-sonnet-latest", "claude-3-haiku-latest"],
        "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    },
    "google": {
        "models": ["gemini-2.5-pro-preview-06-05", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
        "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    },
    "cartesia": {
        "models": ["sonic-2", "sonic-2-2025-06-03", "sonic-3-2025-07-15"],
        "voices": []  # Uses custom voice IDs
    }
}

# Voice options for each provider
VOICE_OPTIONS = {
    "alloy": "Alloy - Neutral, balanced",
    "echo": "Echo - Male, warm",
    "fable": "Fable - British accent",
    "onyx": "Onyx - Deep male voice",
    "nova": "Nova - Female, upbeat",
    "shimmer": "Shimmer - Female, smooth"
}
