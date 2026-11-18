from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import base64
import uuid
import time
import logging

from services.generation.ai_engine import AIEngine
from routers.assets import _ASSETS

logger = logging.getLogger("router_generation")
router = APIRouter(prefix="/api/ai", tags=["AI Generation & Editing"])

# In-memory generation history
_GENERATION_HISTORY = []

class PromptEnhanceRequest(BaseModel):
    prompt: str = Field(..., description="Original user prompt")
    style: Optional[str] = Field("photorealistic", description="Target visual style")

class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Active generation prompt (original or enhanced)")
    originalPrompt: Optional[str] = Field(None, description="Preserved original user prompt")
    enhancedPrompt: Optional[str] = Field(None, description="Synthesized enhanced prompt")
    negativePrompt: Optional[str] = Field(None, description="Negative prompt to exclude elements")
    model: Optional[str] = Field("Flux-Diffusion-Pro", description="Model architecture")
    style: Optional[str] = Field("photorealistic", description="Visual style")
    aspectRatio: Optional[str] = Field("1:1", description="Target aspect ratio")
    seed: Optional[int] = Field(None, description="Random or deterministic seed")
    steps: Optional[int] = Field(30, description="Denoising sampling steps")
    guidanceScale: Optional[float] = Field(7.5, description="CFG guidance scale")
    width: Optional[int] = Field(None, description="Explicit pixel width")
    height: Optional[int] = Field(None, description="Explicit pixel height")
    numImages: Optional[int] = Field(1, description="Number of images to generate")

class KeysUpdateRequest(BaseModel):
    pollinationsKey: Optional[str] = Field(None, description="Pollinations API Key")
    hfToken: Optional[str] = Field(None, description="Hugging Face User Access Token")
    openAiKey: Optional[str] = Field(None, description="OpenAI API Key")

@router.get("/keys")
async def get_keys_status_endpoint():
    """Returns configuration status of cloud AI providers."""
    return {
        "success": True,
        **AIEngine.get_api_keys_status()
    }

@router.post("/keys")
async def update_keys_endpoint(req: KeysUpdateRequest):
    """Updates runtime cloud provider credentials."""
    AIEngine.update_api_keys(
        pollinations_key=req.pollinationsKey,
        hf_token=req.hfToken,
        openai_key=req.openAiKey
    )
    return {
        "success": True,
        "message": "AI Provider credentials updated successfully.",
        **AIEngine.get_api_keys_status()
    }

@router.get("/models")
async def get_supported_models():
    """Returns list of supported AI generation models and provider specifications."""
    return {
        "success": True,
        "models": [
            {"id": k, **v} for k, v in AIEngine.SUPPORTED_MODELS.items()
        ]
    }


@router.post("/enhance-prompt")
async def enhance_prompt_endpoint(req: PromptEnhanceRequest):
    """
    7-Component Prompt Decomposition & Intelligent Synthesizer:
    Extracts Subject, Environment, Action/State, Composition, Lighting, Style, Quality.
    Preserves exact user intent and core entities.
    """
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    return AIEngine.enhance_prompt(req.prompt, req.style or "photorealistic")

@router.post("/generate")
async def generate_image(req: GenerateRequest):
    """
    Authentic Text-to-Image Generation Endpoint:
    Dispatches to real neural diffusion providers (FLUX.1 / SDXL / DALL-E).
    Validates output image bytes, logs audit metrics, and persists to history.
    """
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Generation prompt is required")
    
    try:
        img_bytes, metadata = await AIEngine.generate_text_to_image_async(
            prompt=req.prompt,
            original_prompt=req.originalPrompt,
            enhanced_prompt=req.enhancedPrompt,
            negative_prompt=req.negativePrompt,
            model=req.model or "Flux-Diffusion-Pro",
            style=req.style or "photorealistic",
            aspect_ratio=req.aspectRatio or "1:1",
            seed=req.seed,
            steps=req.steps or 30,
            guidance_scale=req.guidanceScale or 7.5,
            width=req.width,
            height=req.height
        )

        mime = metadata.get("mimeType", "image/jpeg")
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        data_url = f"data:{mime};base64,{b64}"

        gen_id = f"gen-{uuid.uuid4().hex[:8]}"
        title_prompt = req.originalPrompt or req.prompt
        clean_title = f"AI Art: {title_prompt[:36]}..." if len(title_prompt) > 36 else f"AI Art: {title_prompt}"

        # Persist to generation history
        gen_record = {
            "id": gen_id,
            "title": clean_title,
            "prompt": req.prompt,
            "originalPrompt": req.originalPrompt or req.prompt,
            "enhancedPrompt": req.enhancedPrompt or req.prompt,
            "negativePrompt": req.negativePrompt,
            "model": req.model or "Flux-Diffusion-Pro",
            "modelName": metadata.get("modelName", "Flux Diffusion Pro"),
            "provider": metadata.get("provider", "Neural Engine"),
            "style": req.style or "photorealistic",
            "aspectRatio": req.aspectRatio or "1:1",
            "seed": metadata.get("seed"),
            "steps": req.steps or 30,
            "guidanceScale": req.guidanceScale or 7.5,
            "width": metadata.get("width", 1024),
            "height": metadata.get("height", 1024),
            "mimeType": mime,
            "sizeBytes": len(img_bytes),
            "createdAt": metadata.get("timestamp"),
            "dataUrl": data_url
        }

        _GENERATION_HISTORY.insert(0, gen_record)

        # Store in global asset library
        _ASSETS.insert(0, {
            "id": gen_record["id"],
            "title": gen_record["title"],
            "category": "Generated",
            "format": mime.split("/")[-1].upper(),
            "sizeBytes": len(img_bytes),
            "width": metadata.get("width", 1024),
            "height": metadata.get("height", 1024),
            "tags": ["ai-generated", req.style or "photorealistic", req.model or "flux"],
            "isFavorite": False,
            "createdAt": metadata.get("timestamp"),
            "dataUrl": data_url,
            "metadata": metadata
        })

        return {
            "success": True,
            "id": gen_record["id"],
            "status": "GENERATION_SUCCESS",
            "imageUrl": data_url,
            "dataUrl": data_url,
            "mimeType": mime,
            "width": metadata.get("width", 1024),
            "height": metadata.get("height", 1024),
            "model": req.model or "Flux-Diffusion-Pro",
            "provider": metadata.get("provider", "Neural Engine"),
            "seed": metadata.get("seed"),
            "prompt": req.prompt,
            "originalPrompt": req.originalPrompt or req.prompt,
            "enhancedPrompt": req.enhancedPrompt or req.prompt,
            "negativePrompt": req.negativePrompt,
            "generationTimeMs": metadata.get("generationTimeMs", 0),
            "sizeBytes": len(img_bytes),
            "metadata": metadata
        }
    except Exception as e:
        err_msg = str(e)
        logger.error(f"[Generation Endpoint] Generation Error: {err_msg}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=err_msg
        )

@router.get("/history")
async def get_generation_history():
    """Retrieve all user generation history."""
    return {"success": True, "history": _GENERATION_HISTORY}

@router.delete("/history/{gen_id}")
async def delete_history_item(gen_id: str):
    global _GENERATION_HISTORY
    _GENERATION_HISTORY = [g for g in _GENERATION_HISTORY if g["id"] != gen_id]
    return {"success": True, "message": "History record deleted"}

@router.post("/expand")
async def expand_image_endpoint(
    file: UploadFile = File(...),
    left: int = Form(100),
    right: int = Form(100),
    top: int = Form(100),
    bottom: int = Form(100)
):
    content = await file.read()
    try:
        expanded_bytes, meta = AIEngine.expand_image(content, left, right, top, bottom)
        b64 = base64.b64encode(expanded_bytes).decode("utf-8")
        return {
            "success": True,
            "metadata": meta,
            "dataUrl": f"data:image/png;base64,{b64}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
