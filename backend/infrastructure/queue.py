import os
import redis
from rq import Queue

# Get Redis connection details from environment variables
# with defaults for local development.
redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = int(os.environ.get("REDIS_PORT", 6379))

# Establish a connection to Redis
redis_conn = redis.Redis(host=redis_host, port=redis_port)

# Create a queue. We can have multiple queues (e.g., 'high', 'default', 'low')
# For now, we'll use a 'video_processing' queue and a 'default' one.
video_queue = Queue('video_processing', connection=redis_conn)
default_queue = Queue('default', connection=redis_conn)

def get_video_queue():
    return video_queue

def get_default_queue():
    return default_queue
