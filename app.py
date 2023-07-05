import os
import uvicorn
import json
import asyncio
from fastapi import File, UploadFile, Request, FastAPI, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel

PORT = os.environ.get('APP_PORT') or 8080

app = FastAPI(
    title='SharedModule', 
    version='0.0.2'
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
engine = create_engine("sqlite:///shared_module.db")
Session = sessionmaker(bind=engine)

# Create a base class for the database models
Base = declarative_base()

class Schema(Base):
    __tablename__ = "schemas"
    metaid = Column(String, primary_key=True)
    msgbody = Column(String)
    
class Channel(Base):
    __tablename__ = "channels"
    channeltype = Column(String, primary_key=True)
    id = Column(String, primary_key=True)
    channlidmap = Column(String)

class Deidentification(Base):
    __tablename__ = "deidentification"
    methodid = Column(String, primary_key=True)
    id = Column(String, primary_key=True)
    encryptedid = Column(String)

# Create the database tables if they do not exist
Base.metadata.create_all(engine)

# Define the pydantic models for the API requests and responses

class SchemaValidate(BaseModel):
    result: str
    errormsg :str

class ChannelSearch(BaseModel):
    channlidmap: str

class IdDeIdentify(BaseModel):
    encryptedid: str

# Define the API endpoints for creating and retrieving tags and items

@app.post("/schema/validate", response_model=SchemaValidate)
def schema_validate(metaid: str, msgbody: str):
    session = Session()
    json_schema_db = session.query(Schema).get(metaid)
    if json_schema_db:
        result = json.loads(json_schema_db) == json.loads(msgbody)
        return result
    else:
        raise HTTPException(status_code=204, detail="Schema not found")

@app.post("/channel/search", response_model=ChannelSearch)
def channel_search(channeltype: str, id: str):
    session = Session()
    result = session.query(Channel).filter_by(channeltype=channeltype, id=id)
    if result:
        pass
        return result
    else:
        raise HTTPException(status_code=204, detail="Channel ID not found")
    
@app.post("/id/deidentify", response_model=IdDeIdentify)
def id_deidentify(methodid: str, id: str):
    session = Session()
    result = session.query(Deidentification).filter_by(methodid=methodid, id=id)
    if result:
        pass
        return result
    else:
        raise HTTPException(status_code=503, detail="Encrypt fail")

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host='0.0.0.0',
        port=int(PORT),
        log_level="info",
        reload=True)
    
