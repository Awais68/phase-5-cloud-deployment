"""
Kafka Producer Configuration Template
Generated for: {{ environment }} environment
Message volume: {{ volume }}
Security: {{ security }}
"""

from aiokafka import AIOKafkaProducer
import asyncio
import json

# Producer configuration
producer_config = {
    "bootstrap_servers": "{{ kafka_servers }}",
    "acks": "all",
    "retries": 3,
    "max_in_flight_requests_per_connection": 5,
    "compression_type": "gzip",
    "batch_size": {{ batch_size }},
    "linger_ms": 10,
    "request_timeout_ms": 30000,
}

# Security configuration
{% if security == "tls" or security == "sasl-ssl" %}
producer_config.update({
    "security_protocol": "{{ security_protocol }}",
    "ssl_cafile": "/path/to/ca-cert.pem",
    "ssl_certfile": "/path/to/client-cert.pem",
    "ssl_keyfile": "/path/to/client-key.pem",
})
{% endif %}

{% if security == "sasl-scram" or security == "sasl-ssl" %}
producer_config.update({
    "sasl_mechanism": "SCRAM-SHA-512",
    "sasl_plain_username": "{{ username }}",
    "sasl_plain_password": "{{ password }}",
})
{% endif %}


async def produce_message(producer, topic, key, value):
    """
    Send a message to Kafka with error handling and retry.

    Args:
        producer: AIOKafkaProducer instance
        topic: Topic name
        key: Message key (for partitioning)
        value: Message value (dict)
    """
    try:
        # Serialize value to JSON
        serialized_value = json.dumps(value).encode('utf-8')
        serialized_key = key.encode('utf-8') if key else None

        # Send message
        metadata = await producer.send_and_wait(
            topic,
            value=serialized_value,
            key=serialized_key
        )

        print(f"Message sent to {metadata.topic} partition {metadata.partition} offset {metadata.offset}")
        return metadata

    except Exception as e:
        print(f"Error sending message: {e}")
        raise


async def main():
    """
    Example producer implementation with proper startup/shutdown.
    """
    producer = AIOKafkaProducer(**producer_config)

    await producer.start()

    try:
        # Send example message
        await produce_message(
            producer,
            "{{ topic_name }}",
            "example-key",
            {"message": "Hello Kafka", "timestamp": "2024-01-01T00:00:00Z"}
        )

    finally:
        # Ensure all messages are sent before shutdown
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
