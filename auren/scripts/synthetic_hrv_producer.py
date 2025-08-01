import json, time, random
from confluent_kafka import Producer
p = Producer({"bootstrap.servers": "kafka:9093"})
while True:
    rmssd = round(random.uniform(15, 90), 1)
    p.produce("biometric-events",
              json.dumps({"user_id":"demo","rmssd_ms":rmssd}).encode())
    p.flush(); time.sleep(6) 