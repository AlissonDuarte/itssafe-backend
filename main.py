from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from routers import user, occurrence, zones
from database import Base, engine
from services.rabbit.consumer import Consumer
from services.singleton.producer import producer

Base.metadata.create_all(bind=engine)
consumer = Consumer("alerts")

@asynccontextmanager
async def startup_event(app: FastAPI):
    import threading
    producer.send_message({"message": "Hello!"})
    thread = threading.Thread(target=consumer.consume, daemon=True, name="RabbitConsumer")
    thread.start()
    yield
    producer.close_connection()
    print("encerrando app")


app = FastAPI(lifespan=startup_event)
app.include_router(user.router, prefix="/api")
app.include_router(occurrence.router, prefix="/api")
app.include_router(zones.router, prefix="/api")
app.mount("/api/static", StaticFiles(directory="static"), name="static")

# app = FastAPI()
# app.include_router(user.router, prefix="/api")
# app.include_router(occurrence.router, prefix="/api")
# app.include_router(zones.router, prefix="/api")
# app.mount("/static", StaticFiles(directory="static"), name="static")
