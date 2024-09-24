from flask import Flask, render_template, request, make_response, g
from redis import Redis
from kafka import KafkaProducer
from kafka.errors import KafkaError  # Importar desde kafka.errors
import os
import socket
import random
import json
import logging
import time

option_a = os.getenv('OPTION_A', "Cats")
option_b = os.getenv('OPTION_B', "Dogs")
hostname = socket.gethostname()

app = Flask(__name__)

# Función para crear el productor de Kafka con reintentos
def create_kafka_producer():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers='kafka:29092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            return producer  # Devuelve el productor si se conecta exitosamente
        except KafkaError as e:
            app.logger.error('Error connecting to Kafka: %s', e)
            time.sleep(3)  # Espera 30 segundos antes de reintentar

# Inicializa el productor de Kafka
producer = create_kafka_producer()

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="redis", db=0, socket_timeout=5)
    return g.redis

@app.route("/", methods=['POST', 'GET'])
def hello():
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]

    vote = None

    if request.method == 'POST':
        redis = get_redis()
        vote = request.form['vote']
        app.logger.info('Received vote for %s', vote)
        
        # Guardar el voto en Redis
        data = json.dumps({'voter_id': voter_id, 'vote': vote})
        redis.rpush('votes', data)

        # Enviar el mensaje de voto al tópico de Kafka
        try:
            producer.send('votes', {'voter_id': voter_id, 'vote': vote})
            app.logger.info('Sent vote to Kafka: %s', data)
        except KafkaError as e:
            app.logger.error('Failed to send message to Kafka: %s', e)

    resp = make_response(render_template(
        'index.html',
        option_a=option_a,
        option_b=option_b,
        hostname=hostname,
        vote=vote,
    ))
    resp.set_cookie('voter_id', voter_id)
    return resp

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
