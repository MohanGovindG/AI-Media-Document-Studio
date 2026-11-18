from fastapi import APIRouter, Form
from pydantic import BaseModel
from typing import Optional

from services.command.command_parser import AICommandParser

router = APIRouter(prefix="/api/command", tags=["AI Command Bar"])

class CommandQuery(BaseModel):
    query: str

@router.post("/parse")
async def parse_command_endpoint(req: CommandQuery):
    result = AICommandParser.parse_command(req.query)
    return {"success": True, "plan": result}

@router.get("/smart-presets")
async def get_smart_presets():
    return AICommandParser.SMART_USE_CASES
