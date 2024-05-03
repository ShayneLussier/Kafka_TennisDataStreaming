from flask import Flask, render_template
from flask_socketio import SocketIO
from confluent_kafka import Consumer, KafkaError
import json

app = Flask(__name__)
socketio = SocketIO(app)

# Kafka consumer configuration
consumer_conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'flask-consumer-group',
    'auto.offset.reset': 'earliest'
}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    consumer = Consumer(consumer_conf)
    consumer.subscribe(['tennis-match-events'])

    try:
        while True:
            msg = consumer.poll(timeout=1.0) # waits 1 sec for a msg before iterating the next loop
            if msg is None:
                continue
            if not msg.error():
                data = json.loads(msg.value().decode('utf-8'))
                winner_name = data.get('winner')
                socketio.emit('winner_update', winner_name)
            elif msg.error().code() != KafkaError._PARTITION_EOF:
                print(msg.error())
    finally:
        consumer.close()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)