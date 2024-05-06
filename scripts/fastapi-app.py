from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from confluent_kafka import Consumer
import json

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

winner = None

@app.get("/")
async def read_index(request: Request):
    global winner
    
    # Check for new messages
    msg = consumer.poll(1.0)
    if msg is None:
        pass
    elif msg.error():
        print(f"Consumer error: {msg.error()}")
    else:
        message = msg.value().decode('utf-8')
        winner_data = json.loads(message)
        winner = winner_data.get('winner')

    return templates.TemplateResponse("index.html", {"request": request, "winner": winner})