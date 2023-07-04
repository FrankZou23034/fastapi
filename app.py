import os
import uvicorn
from fastapi import File, UploadFile, Request, FastAPI, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel

PORT = os.environ.get('APP_PORT') or 8080

app = FastAPI(
    title='Tagging', 
    version='0.0.1'
)

#templates = Jinja2Templates(directory="templates")
#app.mount("/static", StaticFiles(directory="static"), name="static")

#app.include_router(account_router)
#app.include_router(websocket_router)
#app.include_router(ai_router)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Create a sqlite database engine and a session factory
engine = create_engine("sqlite:///tagging.db")
Session = sessionmaker(bind=engine)

# Create a base class for the database models
Base = declarative_base()

# Define the models for tags and items
class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    items = relationship("Item", secondary="item_tags")

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    tags = relationship("Tag", secondary="item_tags")

# Define the association table for the many-to-many relationship between tags and items
class ItemTag(Base):
    __tablename__ = "item_tags"
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"), primary_key=True)

# Create the database tables if they do not exist
Base.metadata.create_all(engine)

# Define the pydantic models for the API requests and responses

class TagCreate(BaseModel):
    name: str

class TagOut(BaseModel):
    id: int
    name: str

class ItemCreate(BaseModel):
    name: str
    tag_names: list[str]

class ItemOut(BaseModel):
    id: int
    name: str
    tag_names: list[str]

# Define the API endpoints for creating and retrieving tags and items

@app.post("/tags", response_model=TagOut)
def create_tag(tag: TagCreate):
    # Create a new tag with the given name
    session = Session()
    new_tag = Tag(name=tag.name)
    session.add(new_tag)
    try:
        session.commit()
        return new_tag
    except:
        session.rollback()
        raise HTTPException(status_code=400, detail="Tag already exists")

@app.get("/tags/{tag_id}", response_model=TagOut)
def get_tag(tag_id: int):
    # Get the tag with the given id
    session = Session()
    tag = session.query(Tag).get(tag_id)
    if tag:
        return tag
    else:
        raise HTTPException(status_code=404, detail="Tag not found")

@app.post("/items", response_model=ItemOut)
def create_item(item: ItemCreate):
    # Create a new item with the given name and tags
    session = Session()
    new_item = Item(name=item.name)
    for tag_name in item.tag_names:
        # Get or create the tag with the given name
        tag = session.query(Tag).filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            session.add(tag)
        # Associate the item with the tag
        new_item.tags.append(tag)
    session.add(new_item)
    try:
        session.commit()
        return ItemOut(id=new_item.id, name=new_item.name, tag_names=[tag.name for tag in new_item.tags])
    except:
        session.rollback()
        raise HTTPException(status_code=400, detail="Item already exists")

@app.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: int):
    # Get the item with the given id and its tags
    session = Session()
    item = session.query(Item).get(item_id)
    if item:
        return ItemOut(id=item.id, name=item.name, tag_names=[tag.name for tag in item.tags])
    else:
        raise HTTPException(status_code=404, detail="Item not found")


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host='0.0.0.0',
        port=int(PORT),
        log_level="info",
        reload=True)
    
