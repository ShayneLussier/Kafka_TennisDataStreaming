from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from confluent_kafka import Consumer
import json
import asyncio

app = FastAPI()

# Kafka consumer setup
consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'tennis-match-consumer',
    'auto.offset.reset': 'earliest'
})
consumer.subscribe(['tennis-match-events'])

# Global variables to store match data
match_data = {
    'player1': None,
    'player2': None,
    'player1_sets': 0,
    'player2_sets': 0,
    'player1_games': 0,
    'player2_games': 0,
    'player1_points': 0,
    'player2_points': 0,
    'winner': None
}

async def event_generator():
    global match_data
    while True:
        msg = consumer.poll(0.1)  # Poll every 100 milliseconds
        if msg is None:
            if match_data['winner']:
                yield f"data: {json.dumps(match_data)}\n\n"
            await asyncio.sleep(0.01)  # Sleep for a short time to avoid excessive CPU usage
            continue
        elif msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        else:
            message = msg.value().decode('utf-8')
            event_data = json.loads(message)
            event_type = event_data.get('event_type')

            if event_type == 'point':
                match_data['player1'] = event_data.get('player1')
                match_data['player2'] = event_data.get('player2')
                match_data['player1_points'] = event_data.get('player1_score')
                match_data['player2_points'] = event_data.get('player2_score')
            elif event_type == 'game':
                match_data['player1_games'] = event_data.get('player1_score')
                match_data['player2_games'] = event_data.get('player2_score')
            elif event_type == 'set':
                match_data['player1_sets'] = event_data.get('player1_score')
                match_data['player2_sets'] = event_data.get('player2_score')
            elif 'winner' in event_data:
                match_data['winner'] = event_data.get('winner')

            yield f"data: {json.dumps(match_data)}\n\n"

@app.get("/sse")
async def sse_endpoint():
    return StreamingResponse(event_generator(), media_type="text/event-stream")