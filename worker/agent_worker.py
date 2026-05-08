import os
import sys
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentServer, AgentSession, Agent

# Import all plugins
from livekit.plugins import openai as openai_plugin

# Try to import additional TTS/STT providers
try:
    from livekit.plugins import elevenlabs
    ELEVENLABS_AVAILABLE = True
    print("[WORKER] ElevenLabs plugin available", flush=True)
except ImportError:
    ELEVENLABS_AVAILABLE = False
    print("[WORKER] ElevenLabs plugin NOT available", flush=True)

try:
    from livekit.plugins import deepgram
    DEEPGRAM_AVAILABLE = True
    print("[WORKER] Deepgram plugin available", flush=True)
except ImportError:
    DEEPGRAM_AVAILABLE = False
    print("[WORKER] Deepgram plugin NOT available", flush=True)

try:
    from livekit.plugins import google
    GOOGLE_AVAILABLE = True
    print("[WORKER] Google plugin available", flush=True)
except ImportError:
    GOOGLE_AVAILABLE = False
    print("[WORKER] Google plugin NOT available", flush=True)

try:
    from livekit.plugins import cartesia
    CARTESIA_AVAILABLE = True
    print("[WORKER] Cartesia plugin available", flush=True)
except ImportError:
    CARTESIA_AVAILABLE = False
    print("[WORKER] Cartesia plugin NOT available", flush=True)

# Database imports
try:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("[WORKER] Database modules not available")

load_dotenv()

AGENT_NAME = os.getenv("AGENT_NAME", "voice-agent")
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")

print(f"[WORKER] Starting with AGENT_NAME={AGENT_NAME}", flush=True)

# Database setup
async_session_maker = None
if DB_AVAILABLE and DATABASE_URL:
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    DATABASE_URL = DATABASE_URL.split("?")[0]
    
    print(f"[WORKER] Database configured: {DATABASE_URL[:50]}...", flush=True)
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def create_tts(tts_provider: str, tts_voice: str):
    """Create TTS instance based on provider"""
    provider = tts_provider.lower() if tts_provider else "openai"
    voice = tts_voice or "alloy"
    
    if provider == "openai":
        return openai_plugin.TTS(voice=voice)
    
    elif provider == "elevenlabs":
        if not ELEVENLABS_AVAILABLE:
            print("[WORKER] ElevenLabs not available, falling back to OpenAI", flush=True)
            return openai_plugin.TTS(voice="alloy")
        voice_id = voice.replace("elevenlabs:", "").replace("elevenlabs_", "")
        return elevenlabs.TTS(voice_id=voice_id)
    
    elif provider == "deepgram":
        if not DEEPGRAM_AVAILABLE:
            print("[WORKER] Deepgram not available, falling back to OpenAI", flush=True)
            return openai_plugin.TTS(voice="alloy")
        return deepgram.TTS(model="nova-2", voice=voice)
    
    elif provider == "cartesia":
        if not CARTESIA_AVAILABLE:
            print("[WORKER] Cartesia not available, falling back to OpenAI", flush=True)
            return openai_plugin.TTS(voice="alloy")
        voice_id = voice.replace("cartesia:", "").replace("cartesia_", "")
        return cartesia.TTS(voice_id=voice_id)
    
    else:
        print(f"[WORKER] Unknown TTS provider: {provider}, using OpenAI", flush=True)
        return openai_plugin.TTS(voice="alloy")


def create_stt(stt_provider: str):
    """Create STT instance based on provider"""
    provider = stt_provider.lower() if stt_provider else "openai"
    
    if provider == "openai":
        # OpenAI RealtimeModel handles STT automatically
        return None
    
    elif provider == "deepgram":
        if not DEEPGRAM_AVAILABLE:
            print("[WORKER] Deepgram not available, using OpenAI STT", flush=True)
            return None
        return deepgram.STT(model="nova-2")
    
    else:
        print(f"[WORKER] Unknown STT provider: {provider}, using OpenAI", flush=True)
        return None


def create_llm(llm_provider: str, llm_type: str, llm_model: str):
    """Create LLM instance based on provider and type"""
    provider = llm_provider.lower() if llm_provider else "openai"
    llm_type = llm_type.lower() if llm_type else "realtime"
    model = llm_model or "gpt-4o"
    
    if provider == "openai":
        if llm_type == "realtime":
            return openai_plugin.realtime.RealtimeModel(model="gpt-4o-realtime-preview")
        else:
            return openai_plugin.LLM(model=model)
    
    elif provider in ["google", "gemini"]:
        if not GOOGLE_AVAILABLE:
            print("[WORKER] Google not available, falling back to OpenAI", flush=True)
            return openai_plugin.realtime.RealtimeModel()
        if llm_type == "realtime":
            return google.realtime.RealtimeModel(model="gemini-2.0-flash-exp")
        else:
            return google.LLM(model="gemini-2.0-flash")
    
    elif provider == "anthropic":
        from livekit.plugins import anthropic
        return anthropic.LLM(model=model or "claude-3-5-sonnet-20241022")
    
    else:
        print(f"[WORKER] Unknown LLM provider: {provider}, using OpenAI", flush=True)
        return openai_plugin.realtime.RealtimeModel()


async def get_agent_config(agent_name: str) -> dict:
    """Get agent configuration from database"""
    defaults = {
        "system_prompt": "You are a helpful AI voice assistant.",
        "llm_provider": "openai",
        "llm_type": "realtime",
        "llm_model": "gpt-4o",
        "tts_provider": "openai",
        "tts_voice": "alloy",
        "stt_provider": "openai",
        "greeting": None
    }
    
    if not DB_AVAILABLE or not async_session_maker:
        print("[WORKER] DB not available, using defaults", flush=True)
        return defaults
    
    try:
        async with async_session_maker() as session:
            from sqlalchemy import text
            query = text("""
                SELECT system_prompt, llm_provider, llm_type, llm_model, 
                       tts_provider, tts_voice, stt_provider, greeting
                FROM agents 
                WHERE name = :name AND is_active = true
            """)
            result = await session.execute(query, {"name": agent_name})
            row = result.fetchone()
            
            if row:
                print(f"[WORKER] Found agent '{agent_name}' in DB!", flush=True)
                config = {
                    "system_prompt": row[0],
                    "llm_provider": row[1] or defaults["llm_provider"],
                    "llm_type": row[2] or defaults["llm_type"],
                    "llm_model": row[3] or defaults["llm_model"],
                    "tts_provider": row[4] or defaults["tts_provider"],
                    "tts_voice": row[5] or defaults["tts_voice"],
                    "stt_provider": row[6] or defaults["stt_provider"],
                    "greeting": row[7]
                }
                print(f"[WORKER] LLM: {config['llm_provider']}/{config['llm_type']}", flush=True)
                print(f"[WORKER] TTS: {config['tts_provider']}/{config['tts_voice']}", flush=True)
                print(f"[WORKER] STT: {config['stt_provider']}", flush=True)
                return config
            else:
                print(f"[WORKER] Agent '{agent_name}' NOT FOUND, using defaults", flush=True)
                return defaults
    except Exception as e:
        print(f"[WORKER] Error fetching agent config: {e}", flush=True)
        return defaults


# Create AgentServer
server = AgentServer()


@server.rtc_session(agent_name=AGENT_NAME)
async def voice_agent(ctx: agents.JobContext):
    print(f"[VOICE_AGENT] Session started!", flush=True)
    print(f"[VOICE_AGENT] Room: {ctx.room.name}", flush=True)
    
    try:
        # Get config from database
        config = await get_agent_config(AGENT_NAME)
        print(f"[VOICE_AGENT] Loaded config for agent: {AGENT_NAME}", flush=True)
        
        # Connect to room
        await ctx.connect()
        print(f"[VOICE_AGENT] Connected to room", flush=True)
        
        # Create LLM
        print(f"[VOICE_AGENT] Creating LLM...", flush=True)
        llm = create_llm(config["llm_provider"], config["llm_type"], config["llm_model"])
        
        # Create TTS
        print(f"[VOICE_AGENT] Creating TTS ({config['tts_provider']})...", flush=True)
        tts = create_tts(config["tts_provider"], config["tts_voice"])
        
        # Create STT (optional)
        stt = create_stt(config["stt_provider"])
        
        # Create session
        print(f"[VOICE_AGENT] Creating AgentSession...", flush=True)
        session_kwargs = {"llm": llm, "tts": tts}
        if stt:
            session_kwargs["stt"] = stt
        
        session = AgentSession(**session_kwargs)
        
        # Create agent
        class DynamicAgent(Agent):
            def __init__(self, instructions: str) -> None:
                super().__init__(instructions=instructions)
        
        # Start session
        print(f"[VOICE_AGENT] Starting session...", flush=True)
        await session.start(room=ctx.room, agent=DynamicAgent(config["system_prompt"]))
        
        # Generate greeting
        if config.get("greeting"):
            print(f"[VOICE_AGENT] Using configured greeting...", flush=True)
            await session.generate_reply(instructions=config["greeting"])
        else:
            print(f"[VOICE_AGENT] Generating default greeting...", flush=True)
            await session.generate_reply(instructions="Greet the user and offer your assistance.")
        
        print(f"[VOICE_AGENT] Ready!", flush=True)
        
    except Exception as e:
        print(f"[VOICE_AGENT] ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc(file=sys.stdout)


if __name__ == "__main__":
    print(f"[WORKER] Starting voice-agent: {AGENT_NAME}", flush=True)
    print(f"[WORKER] Plugins - ElevenLabs: {ELEVENLABS_AVAILABLE}, Deepgram: {DEEPGRAM_AVAILABLE}, Google: {GOOGLE_AVAILABLE}", flush=True)
    agents.cli.run_app(server)
