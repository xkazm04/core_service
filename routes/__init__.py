from fastapi import APIRouter
from routes.project import router as project_router
from routes.act import router as act_router
from routes.faction import router as faction_router
from routes.faction_rel import router as faction_rel_router
from routes.prompt import router as prompt_router
from routes.character import router as character_router
from routes.character_llm import router as character_llm_router
from routes.character_rel import router as character_rel_router
from routes.trait import router as trait_router
from routes.scene import router as scene_router
from routes.scene_params import router as scene_params_router
from routes.line import router as line_router
from routes.beats import router as beats_router
from routes.agent import router as agent_router
from routes.improve import router as improve_router
from routes.sse import router as sse_router
from routes.analytics import router as analytics_router
from routes.paragraph import router as paragraph_router

api_router = APIRouter()

api_router.include_router(project_router, prefix="/projects", tags=["Projects"])
api_router.include_router(act_router, prefix="/acts", tags=["Acts"])
api_router.include_router(character_router, prefix="/characters", tags=["Characters"])
api_router.include_router(character_rel_router, prefix="/characters/rel", tags=["Character-Relationships"])
api_router.include_router(character_llm_router, prefix="/characters/llm", tags=["Characters-LLM"])
api_router.include_router(scene_router, prefix="/scenes", tags=["Scenes"])
api_router.include_router(scene_params_router, prefix="/scene/params", tags=["Scene-params"])
api_router.include_router(line_router, prefix="/lines", tags=["Lines"])
api_router.include_router(prompt_router, prefix="/prompts", tags=["Prompts"])
api_router.include_router(faction_router, prefix="/factions", tags=["Factions"])
api_router.include_router(faction_rel_router, prefix="/factionrel", tags=["Faction-Relationships"])
api_router.include_router(trait_router, prefix="/traits", tags=["Traits"])
api_router.include_router(beats_router, prefix="/beats", tags=["Beats"])
api_router.include_router(agent_router, prefix="/agent", tags=["Agent"])
api_router.include_router(improve_router, prefix="/improve", tags=["Improve"])
api_router.include_router(sse_router, prefix="/sse", tags=["SSE"])
api_router.include_router(analytics_router, prefix="/anal", tags=["Anal"])
api_router.include_router(paragraph_router, prefix="/paragraphs", tags=["Paragraphs"])