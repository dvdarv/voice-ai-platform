from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Float, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Agent configuration
    system_prompt = Column(Text, nullable=False)
    greeting = Column(Text, nullable=True)  # Initial greeting message
    
    # LLM settings
    llm_provider = Column(String(50), default="openai")  # openai, anthropic, google
    llm_type = Column(String(50), default="realtime")  # realtime, chat
    llm_model = Column(String(100), default="gpt-4o")
    
    # TTS (Text-to-Speech) settings
    tts_provider = Column(String(50), default="openai")  # openai, elevenlabs, deepgram, cartesia
    tts_voice = Column(String(100), default="alloy")  # Voice ID or name
    
    # STT (Speech-to-Text) settings
    stt_provider = Column(String(50), default="openai")  # openai, deepgram
    
    # Voice/Speech settings
    temperature = Column(Float, default=0.8)  # LLM temperature (0-2)
    max_output_tokens = Column(Integer, nullable=True)  # Max tokens in response
    
    # Turn detection settings
    turn_detection = Column(String(20), default="semantic")  # semantic, timed, disabled
    interrupt_min_words = Column(Integer, default=0)  # Min words to interrupt
    min_endpointing_delay = Column(String(10), default="0.3s")  # Min delay before ending turn
    max_endpointing_delay = Column(String(10), default="3s")  # Max delay before ending turn
    
    # VAD (Voice Activity Detection)
    vad_enabled = Column(Boolean, default=True)
    vad_model = Column(String(50), default="silero")  # silero, onnx
    
    # Timeout settings
    idle_timeout = Column(String(10), default="5m")  # Session idle timeout
    max_duration = Column(String(10), default="30m")  # Max call duration
    waiting_for_user_timeout = Column(String(10), default="30s")  # Wait for user input
    
    # Audio settings
    audio_sample_rate = Column(Integer, default=16000)
    audio_channels = Column(Integer, default=1)
    
    # Phone number assignment
    phone_number = Column(String(20), nullable=True, unique=True)
    
    # Agent capabilities
    tools = Column(JSON, default=list)  # List of tool configurations
    webhooks = Column(JSON, default=list)  # Webhook URLs for events
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    calls = relationship("Call", back_populates="agent")
    transcripts = relationship("Transcript", back_populates="agent")
    costs = relationship("Cost", back_populates="agent")
