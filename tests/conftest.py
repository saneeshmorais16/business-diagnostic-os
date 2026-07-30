import os
os.environ["DATABASE_URL"]="sqlite:///./test_business_diagnostic.db"
import pytest
from fastapi.testclient import TestClient
from app.database import Base,engine,SessionLocal
from app.main import app
@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine);Base.metadata.create_all(engine);yield;Base.metadata.drop_all(engine)
@pytest.fixture
def client():
    with TestClient(app) as c:yield c
@pytest.fixture
def db():
    s=SessionLocal();yield s;s.close()
