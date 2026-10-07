"""Project commands: python -m app.cli seed"""
import sys
from .database import Base, SessionLocal, engine
from .seed import seed_demo
def main():
    if len(sys.argv)!=2 or sys.argv[1]!="seed":raise SystemExit("Usage: python -m app.cli seed")
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        engagement=seed_demo(db);print(f"Seeded demonstration engagement {engagement.id}: {engagement.company_name}")
if __name__=="__main__":main()
