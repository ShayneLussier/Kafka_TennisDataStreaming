from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from confluent_kafka import Consumer
import json
import asyncio

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Kafka consumer setup
consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'tennis-match-consumer',
    'auto.offset.reset': 'earliest'
})
consumer.subscribe(['tennis-match-events'])

async def event_generator():
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            await asyncio.sleep(1)
            continue
        elif msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        else:
            message = msg.value().decode('utf-8')
            winner_data = json.loads(message)
            winner = winner_data.get('winner')
            yield f"data: {winner}\n\n"

@app.get("/sse")
async def sse_endpoint():
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/")
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})