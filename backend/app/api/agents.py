from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.agent import Agent
from app.models.call import Call
from app.models.cost import Cost
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentWithStats

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new agent"""
    # Handle None values for optional fields
    agent = Agent(
        name=agent_data.name,
        description=agent_data.description,
        system_prompt=agent_data.system_prompt,
        greeting=agent_data.greeting,
        voice=agent_data.voice or "alloy",
        llm_provider=agent_data.llm_provider or "openai",
        llm_type=agent_data.llm_type or "realtime",
        llm_model=agent_data.llm_model or "gpt-4o",
        tts_provider=agent_data.tts_provider or "openai",
        tts_voice=agent_data.tts_voice or "alloy",
        stt_provider=agent_data.stt_provider or "openai",
        temperature=agent_data.temperature or 0.8,
        max_output_tokens=agent_data.max_output_tokens,
        turn_detection=agent_data.turn_detection or "semantic",
        interrupt_min_words=agent_data.interrupt_min_words or 0,
        min_endpointing_delay=agent_data.min_endpointing_delay or "0.3s",
        max_endpointing_delay=agent_data.max_endpointing_delay or "3s",
        vad_enabled=agent_data.vad_enabled if agent_data.vad_enabled is not None else True,
        vad_model=agent_data.vad_model or "silero",
        idle_timeout=agent_data.idle_timeout or "5m",
        max_duration=agent_data.max_duration or "30m",
        waiting_for_user_timeout=agent_data.waiting_for_user_timeout or "30s",
        audio_sample_rate=agent_data.audio_sample_rate or 16000,
        audio_channels=agent_data.audio_channels or 1,
        phone_number=agent_data.phone_number,
        tools=agent_data.tools or [],
        webhooks=agent_data.webhooks or [],
        is_active=agent_data.is_active if agent_data.is_active is not None else True
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all agents"""
    query = select(Agent)
    
    if is_active is not None:
        query = query.where(Agent.is_active == is_active)
    
    query = query.offset(skip).limit(limit).order_by(Agent.created_at.desc())
    result = await db.execute(query)
    agents = result.scalars().all()
    return agents


@router.get("/{agent_id}/", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get agent by ID"""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent


@router.get("/{agent_id}/stats/", response_model=AgentWithStats)
async def get_agent_stats(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get agent with statistics"""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get total calls
    calls_result = await db.execute(
        select(func.count(Call.id)).where(Call.agent_id == agent_id)
    )
    total_calls = calls_result.scalar() or 0
    
    # Get total cost
    cost_result = await db.execute(
        select(func.sum(Cost.total_cost)).where(Cost.agent_id == agent_id)
    )
    total_cost = cost_result.scalar() or 0.0
    
    return AgentWithStats(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        system_prompt=agent.system_prompt,
        voice=agent.voice,
        llm_model=agent.llm_model,
        phone_number=agent.phone_number,
        tools=agent.tools,
        is_active=agent.is_active,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        total_calls=total_calls,
        total_cost=total_cost
    )


@router.put("/{agent_id}/", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an agent"""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    update_data = agent_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(agent, key, value)
    
    agent.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(agent)
    return agent


@router.delete("/{agent_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an agent"""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    await db.delete(agent)
    await db.commit()


@router.post("/{agent_id}/phone/")
async def assign_phone(
    agent_id: str,
    phone_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Assign phone number to agent"""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.phone_number = phone_number
    agent.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(agent)
    return agent
