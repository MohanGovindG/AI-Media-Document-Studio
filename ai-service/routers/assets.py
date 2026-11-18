from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import time
import uuid

router = APIRouter(prefix="/api/assets", tags=["Asset Library"])

# In-memory mock asset store for demo persistence
_ASSETS = [
    {
        "id": "ast-1",
        "title": "E-Commerce Hero Banner",
        "category": "Generated",
        "format": "PNG",
        "sizeBytes": 1420500,
        "width": 1920,
        "height": 1080,
        "tags": ["hero", "ecommerce", "ai-generated"],
        "isFavorite": True,
        "createdAt": "2026-10-02T14:30:00Z",
        "dataUrl": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&auto=format&fit=crop&q=80"
    },
    {
        "id": "ast-2",
        "title": "Q3 Financial Performance Report",
        "category": "Documents",
        "format": "PDF",
        "sizeBytes": 425000,
        "width": 800,
        "height": 1100,
        "tags": ["finance", "quarterly", "report"],
        "isFavorite": False,
        "createdAt": "2026-10-01T09:15:00Z",
        "dataUrl": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=1200&auto=format&fit=crop&q=80"
    },
    {
        "id": "ast-3",
        "title": "Product Cutout Transparent",
        "category": "Edited",
        "format": "WEBP",
        "sizeBytes": 284000,
        "width": 1200,
        "height": 1200,
        "tags": ["product", "transparent", "background-removed"],
        "isFavorite": True,
        "createdAt": "2026-09-30T18:20:00Z",
        "dataUrl": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=1200&auto=format&fit=crop&q=80"
    },
    {
        "id": "ast-4",
        "title": "Vector Logo Blueprint",
        "category": "Converted",
        "format": "SVG",
        "sizeBytes": 45000,
        "width": 500,
        "height": 500,
        "tags": ["vector", "logo", "branding"],
        "isFavorite": False,
        "createdAt": "2026-09-29T11:00:00Z",
        "dataUrl": "https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?w=1200&auto=format&fit=crop&q=80"
    }
]

class AssetCreate(BaseModel):
    title: str
    category: str
    format: str
    dataUrl: str
    sizeBytes: int
    tags: Optional[List[str]] = []
    width: Optional[int] = 1000
    height: Optional[int] = 1000

@router.get("")
async def list_assets(category: Optional[str] = None, search: Optional[str] = None, favoriteOnly: bool = False):
    res = list(_ASSETS)
    if category and category != "All":
        res = [a for a in res if a.get("category", "").lower() == category.lower()]
    if favoriteOnly:
        res = [a for a in res if a.get("isFavorite")]
    if search:
        s = search.lower()
        res = [a for a in res if s in a.get("title", "").lower() or any(s in t.lower() for t in a.get("tags", []))]
    return res

@router.post("")
async def create_asset(asset: AssetCreate):
    new_asset = {
        "id": f"ast-{uuid.uuid4().hex[:8]}",
        "title": asset.title,
        "category": asset.category,
        "format": asset.format.upper(),
        "sizeBytes": asset.sizeBytes,
        "width": asset.width,
        "height": asset.height,
        "tags": asset.tags or [],
        "isFavorite": False,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataUrl": asset.dataUrl
    }
    _ASSETS.insert(0, new_asset)
    return {"success": True, "asset": new_asset}

@router.post("/{asset_id}/favorite")
async def toggle_favorite(asset_id: str):
    for a in _ASSETS:
        if a["id"] == asset_id:
            a["isFavorite"] = not a.get("isFavorite", False)
            return {"success": True, "isFavorite": a["isFavorite"]}
    raise HTTPException(status_code=404, detail="Asset not found")

@router.delete("/{asset_id}")
async def delete_asset(asset_id: str):
    global _ASSETS
    _ASSETS = [a for a in _ASSETS if a["id"] != asset_id]
    return {"success": True}
