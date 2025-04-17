from fastapi import APIRouter
from routes.project import router as project_router
from routes.act import router as act_router
from routes.faction import router as faction_router
from routes.prompt import router as prompt_router
from routes.character import router as character_router
from routes.trait import router as trait_router
from routes.scene import router as scene_router
from routes.scene_params import router as scene_params_router
from routes.line import router as line_router
from routes.beats import router as beats_router

api_router = APIRouter()

api_router.include_router(project_router, prefix="/projects", tags=["Projects"])
api_router.include_router(act_router, prefix="/acts", tags=["Acts"])
api_router.include_router(character_router, prefix="/characters", tags=["Characters"])
api_router.include_router(scene_router, prefix="/scenes", tags=["Scenes"])
api_router.include_router(scene_params_router, prefix="/scene/params", tags=["Scene-params"])
api_router.include_router(line_router, prefix="/lines", tags=["Lines"])
api_router.include_router(prompt_router, prefix="/prompts", tags=["Prompts"])
api_router.include_router(faction_router, prefix="/factions", tags=["Factions"])
api_router.include_router(trait_router, prefix="/traits", tags=["Traits"])
api_router.include_router(beats_router, prefix="/beats", tags=["Beats"])