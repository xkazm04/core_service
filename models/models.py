from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Table, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    user = Column(String, nullable=True)
    type = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    theme = Column(String, nullable=True)
    concept = Column(String, nullable=True)
    overview = Column(String, nullable=True)

    scenes = relationship('Scene', back_populates="project", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan")
    prompts = relationship("Prompt", back_populates="project", cascade="all, delete-orphan")
    acts = relationship("Act", back_populates="project", cascade="all, delete-orphan")
    factions = relationship("Faction", back_populates="project", cascade="all, delete-orphan")
    
class Faction(Base):
    __tablename__ = "factions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    image_url = Column(String, nullable=True)
    color = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="factions")
    characters = relationship("Character", back_populates="faction")


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(String, nullable=False)
    type = Column(String, nullable=True)
    subtype = Column(String, nullable=True)
    char_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"), nullable=True) 
    scene_id = Column(UUID(as_uuid=True), ForeignKey("scenes.id"), nullable=True) 
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    project = relationship("Project", back_populates="prompts")
    characters = relationship("Character", back_populates="prompts")
    scenes = relationship("Scene", back_populates="prompts")
    

# Character models
class Character(Base):
    __tablename__ = "characters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    faction_id = Column(UUID(as_uuid=True), ForeignKey("factions.id"), nullable=True)
    voice = Column(String, nullable=True, default="")
    description = Column(String, nullable=True, default="")
    avatar_url = Column(String, nullable=True, default="")
    transparent_avatar_url = Column(String, nullable=True, default="")

    project = relationship("Project", back_populates="characters")
    prompts = relationship("Prompt", back_populates="characters")
    trait = relationship("CharacterTrait", back_populates="character")
    faction = relationship("Faction", back_populates="characters")
    lines = relationship("Line", back_populates="character")


class CharacterTrait(Base):
    __tablename__ = "character_trait"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"), nullable=False)
    label = Column(String, nullable=False)
    description = Column(String, nullable=True)
    type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    character = relationship("Character")
    
# ----------- Scene models ------------- 

class Scene(Base):
    __tablename__ = "scenes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    act = Column(Integer, nullable=True)
    name = Column(String, nullable=False)
    order = Column(Integer, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    assigned_image_url = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)

    project = relationship("Project", back_populates="scenes")
    prompts = relationship("Prompt", back_populates="scenes")
    scene_params = relationship("SceneParams", back_populates="scene")

dialog_transitions = Table(
    "dialog_transitions",
    Base.metadata,
    Column("source_id", UUID(as_uuid=True), ForeignKey("lines.id"), primary_key=True),
    Column("target_id", UUID(as_uuid=True), ForeignKey("lines.id"), primary_key=True),
    Column("transition_name", String, nullable=True),  
)

class Line(Base):
    __tablename__ = "lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=True)
    scene_id = Column(UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    text = Column(String, nullable=False)
    tone = Column(String, nullable=True, default="Normal")
    order = Column(Integer, nullable=True)

    # New fields
    x = Column(Integer, nullable=True, default=0)  # X position on the diagram
    y = Column(Integer, nullable=True, default=0)  # Y position on the diagram
    is_final = Column(Boolean, default=True)  # Marks if the node is a final dialog

    # Relationships
    character = relationship("Character")
    scene = relationship("Scene")
    
    # Predecessors (only one allowed per node)
    predecessor_id = Column(UUID(as_uuid=True), ForeignKey("lines.id"), nullable=True)
    predecessor = relationship("Line", remote_side=[id])

    # Successors (one-to-many relationship via dialog_transitions)
    successors = relationship(
        "Line",
        secondary=dialog_transitions,
        primaryjoin=id == dialog_transitions.c.source_id,
        secondaryjoin=id == dialog_transitions.c.target_id,
        backref="predecessors",
    )
    

class SceneParams(Base):
    __tablename__ = "scene_params"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scene_id = Column(UUID(as_uuid=True), ForeignKey("scenes.id"), nullable=False)
    param_name = Column(String, nullable=False)
    param_value = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime)
    updated_at = Column(DateTime, default=datetime)

    scene = relationship("Scene", back_populates="scene_params")
    
class Act(Base):
    __tablename__ = "acts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    order = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="acts")
    beats = relationship("Beat", back_populates="act", cascade="all, delete-orphan")

    
class Beat(Base):
    __tablename__ = "beats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    act_id = Column(UUID(as_uuid=True), ForeignKey("acts.id"), nullable=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'act' or 'story'
    order = Column(Integer, nullable=True)
    description = Column(String, nullable=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    default_flag = Column(Boolean, default=False)
    
    act = relationship("Act", back_populates="beats")
