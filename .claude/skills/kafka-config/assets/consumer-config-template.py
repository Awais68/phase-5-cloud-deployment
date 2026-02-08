"""
Kafka Consumer Configuration Template
Generated for: {{ environment }} environment
Message volume: {{ volume }}
Security: {{ security }}
"""

from aiokafka import AIOKafkaConsumer
import asyncio

# Consumer configuration
consumer_config = {
    "bootstrap_servers": "{{ kafka_servers }}",
    "group_id": "{{ group_id }}",
    "auto_offset_reset": "earliest",
    "enable_auto_commit": False,
    "max_poll_records": {{ max_poll_records }},
    "session_timeout_ms": 30000,
    "heartbeat_interval_ms": 10000,
    "max_poll_interval_ms": 300000,
}

# Security configuration
{% if security == "tls" or security == "sasl-ssl" %}
consumer_config.update({
    "security_protocol": "{{ security_protocol }}",
    "ssl_cafile": "/path/to/ca-cert.pem",
    "ssl_certfile": "/path/to/client-cert.pem",
    "ssl_keyfile": "/path/to/client-key.pem",
})
{% endif %}

{% if security == "sasl-scram" or security == "sasl-ssl" %}
consumer_config.update({
    "sasl_mechanism": "SCRAM-SHA-512",
    "sasl_plain_username": "{{ username }}",
    "sasl_plain_password": "{{ password }}",
})
{% endif %}


async def consume_messages():
    """
    Example consumer implementation with manual commit.
    """
    consumer = AIOKafkaConsumer(
        "{{ topic_name }}",
        **consumer_config
    )

    await consumer.start()

    try:
        async for msg in consumer:
            try:
                # Process message
                print(f"Received: {msg.value.decode('utf-8')}")

                # Manual commit after successful processing
                await consumer.commit()
            except Exception as e:
                print(f"Error processing message: {e}")
                # Don't commit on error - message will be reprocessed

    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(consume_messages())
