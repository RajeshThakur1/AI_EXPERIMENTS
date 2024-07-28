# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Text,ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import requests

# Database setup
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:synechron_123@localhost:5432/demo"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True)

class UserProfileDB(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    preferences = Column(Text)
    interests = Column(Text)


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="messages")


User.messages = relationship("Message", order_by=Message.timestamp, back_populates="user")

Base.metadata.create_all(bind=engine)

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserProfile(BaseModel):
    preferences: str
    interests: str

class Token(BaseModel):
    access_token: str
    token_type: str

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    content: str
    timestamp: datetime

OLLAMA_API_URL = "http://localhost:11434/api/generate"  # Adjust if needed
OLLAMA_MODEL = "llama3:latest"

# Security
import secrets
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user


def generate_personalized_context(user: User, db: Session):
    profile = db.query(UserProfileDB).filter(UserProfileDB.user_id == user.id).first()
    context = f"User preferences: {profile.preferences}\nUser interests: {profile.interests}\n"
    return context


def generate_personalized_prompt(user: User, message: str, db: Session):
    context = generate_personalized_context(user, db)
    recent_messages = db.query(Message).filter(Message.user_id == user.id).order_by(Message.timestamp.desc()).limit(
        5).all()
    conversation_history = "\n".join([f"User: {msg.content}" for msg in reversed(recent_messages)])

    prompt = f"{context}\nConversation history:\n{conversation_history}\nUser: {message}\nAI:"
    return prompt

def get_ollama_response(prompt: str):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(OLLAMA_API_URL, json=payload)
    if response.status_code == 200:
        return response.json()['response']
    else:
        raise HTTPException(status_code=500, detail="Failed to get response from Ollama")



# Routes
@app.post("/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/profile")
async def create_profile(profile: UserProfile, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_profile = UserProfileDB(user_id=current_user.id, preferences=profile.preferences, interests=profile.interests)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return {"message": "Profile created successfully"}


@app.put("/profile")
async def update_profile(profile: UserProfile, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_profile = db.query(UserProfileDB).filter(UserProfileDB.user_id == current_user.id).first()
    if db_profile:
        db_profile.preferences = profile.preferences
        db_profile.interests = profile.interests
        db.commit()
        return {"message": "Profile updated successfully"}
    return {"message": "Profile not found"}

@app.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_profile = db.query(UserProfileDB).filter(UserProfileDB.user_id == current_user.id).first()
    if db_profile:
        return {"preferences": db_profile.preferences, "interests": db_profile.interests}
    return {"message": "Profile not found"}


@app.post("/chat", response_model=MessageResponse)
async def chat(message: MessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    personalized_prompt = generate_personalized_prompt(current_user, message.content, db)
    ai_response = get_ollama_response(personalized_prompt)

    # Save user message and AI response
    user_message = Message(user_id=current_user.id, content=message.content)
    ai_message = Message(user_id=current_user.id, content=ai_response)
    db.add(user_message)
    db.add(ai_message)
    db.commit()

    return MessageResponse(content=ai_response, timestamp=ai_message.timestamp)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)