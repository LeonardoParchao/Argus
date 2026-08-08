from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import orchestrator, graphing, database

app = FastAPI(title="Argus OSINT API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    target_type: str
    target_value: str


class ProfileRequest(BaseModel):
    name: str
    notes: Optional[str] = None
    entity_ids: Optional[List[str]] = []


class LinkEntityRequest(BaseModel):
    entity_id: str


@app.post("/api/search")
async def search(request: SearchRequest):
    """
    Accept JSON { target_type, target_value }.
    Call orchestrator.run_search().
    Return JSON results.
    """
    try:
        results = await orchestrator.run_search(request.target_type, request.target_value)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/graph")
async def get_graph():
    """
    Return graphing.build_cytoscape_json() for frontend to consume.
    """
    try:
        graph_data = graphing.build_cytoscape_json()
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get graph data: {str(e)}")


@app.post("/api/profiles")
async def create_profile(request: ProfileRequest):
    """
    Accept profile creation data.
    Insert into SQLite.
    """
    try:
        # Create profile
        profile_id = database.create_profile(request.name, request.notes)
        
        # Link entities if provided
        if request.entity_ids:
            for entity_id in request.entity_ids:
                database.link_entity_to_profile(profile_id, entity_id)
        
        return {
            "profile_id": profile_id,
            "name": request.name,
            "notes": request.notes,
            "linked_entities": len(request.entity_ids) if request.entity_ids else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create profile: {str(e)}")


@app.get("/api/profiles")
async def get_profiles():
    """Get all profiles."""
    try:
        profiles = database.get_profiles()
        return {"profiles": profiles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profiles: {str(e)}")


@app.get("/api/profiles/{profile_id}")
async def get_profile(profile_id: str):
    """Get a specific profile with its entities."""
    try:
        # Get profile details
        profiles = database.get_profiles()
        profile = next((p for p in profiles if p['id'] == profile_id), None)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get profile entities
        entities = database.get_profile_entities(profile_id)
        
        return {
            "profile": profile,
            "entities": entities
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@app.post("/api/profiles/{profile_id}/entities")
async def link_entity_to_profile(profile_id: str, request: LinkEntityRequest):
    """Link an entity to a profile."""
    try:
        link_id = database.link_entity_to_profile(profile_id, request.entity_id)
        return {
            "link_id": link_id,
            "profile_id": profile_id,
            "entity_id": request.entity_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to link entity: {str(e)}")


@app.get("/api/entities/{entity_id}")
async def get_entity(entity_id: str):
    """Get details of a specific entity."""
    try:
        entity = database.get_entity_by_id(entity_id)
        
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        return entity
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "argus-osint-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
