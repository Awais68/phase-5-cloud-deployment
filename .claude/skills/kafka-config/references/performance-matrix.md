# Kafka Performance Tuning Matrix

## Message Volume Classifications

### Low Volume (<1K messages/sec)
- **Partitions**: 3
- **Replication Factor**: 2 (staging/production), 1 (local)
- **Batch Size**: 1024 bytes
- **max_poll_records**: 100
- **linger_ms**: 10ms
- **Use Case**: Low-traffic applications, audit logs, infrequent events

### Medium Volume (1-10K messages/sec)
- **Partitions**: 6
- **Replication Factor**: 3 (production), 2 (staging), 1 (local)
- **Batch Size**: 16384 bytes (16 KB)
- **max_poll_records**: 500
- **linger_ms**: 10ms
- **Use Case**: Standard application events, user activity tracking

### High Volume (>10K messages/sec)
- **Partitions**: 12
- **Replication Factor**: 3 (production), 2 (staging), 1 (local)
- **Batch Size**: 32768 bytes (32 KB)
- **max_poll_records**: 1000
- **linger_ms**: 10ms
- **Use Case**: High-frequency events, IoT data streams, real-time analytics

## Environment-Specific Tuning

### Local Development
- **Replication**: 1 (no redundancy)
- **min.insync.replicas**: 1
- **acks**: "1" (leader only) - acceptable for local testing
- **Retention**: 1-3 days
- **Focus**: Fast startup, minimal resource usage

### Staging
- **Replication**: 2
- **min.insync.replicas**: 1
- **acks**: "all" (both replicas)
- **Retention**: 7 days
- **Focus**: Production-like configuration with lower resource cost

### Production
- **Replication**: 3
- **min.insync.replicas**: 2
- **acks**: "all" (wait for all in-sync replicas)
- **Retention**: 30-90 days (based on compliance requirements)
- **Focus**: Durability, fault tolerance, compliance

## Consumer Group Tuning

### session_timeout_ms
- **Default**: 30000 (30 seconds)
- **High-volume**: Increase to 45000-60000 to avoid false rebalances
- **Low-latency**: Keep at 30000 for faster failure detection

### heartbeat_interval_ms
- **Default**: 10000 (10 seconds)
- **Rule**: Should be 1/3 of session_timeout_ms
- **Example**: session_timeout_ms=30000 → heartbeat_interval_ms=10000

### max_poll_interval_ms
- **Default**: 300000 (5 minutes)
- **Fast processing**: 60000-120000 (1-2 minutes)
- **Slow processing**: 600000 (10 minutes) for heavy computation

## Producer Optimization

### Throughput vs Latency Tradeoff

**High Throughput Configuration:**
```python
{
    "batch_size": 32768,
    "linger_ms": 100,  # Wait up to 100ms to batch messages
    "compression_type": "gzip",
    "acks": "1",  # Leader only (faster but less durable)
}
```

**Low Latency Configuration:**
```python
{
    "batch_size": 1024,
    "linger_ms": 0,  # Send immediately
    "compression_type": "none",
    "acks": "all",  # Maximum durability
}
```

**Balanced (Recommended for Production):**
```python
{
    "batch_size": 16384,
    "linger_ms": 10,
    "compression_type": "gzip",
    "acks": "all",
}
```

## Compression Type Comparison

| Type   | CPU Usage | Compression Ratio | Network Reduction | Use Case                |
|--------|-----------|-------------------|-------------------|-------------------------|
| none   | None      | 1:1               | 0%                | Low-latency, small msgs |
| gzip   | Medium    | ~3:1              | 60-70%            | **Recommended default** |
| snappy | Low       | ~2:1              | 40-50%            | CPU-constrained envs    |
| lz4    | Low       | ~2:1              | 40-50%            | Fast compression needed |
| zstd   | Medium    | ~3:1              | 60-70%            | Best ratio, Kafka 2.1+  |

**Recommendation**: Use `gzip` for production unless you have specific requirements.

## Partition Count Guidelines

### Formula for Partition Count
```
Partitions = max(
    target_throughput / partition_throughput,
    max_consumer_parallelism
)
```

### Examples:
- **Target**: 10K msg/sec, **Partition throughput**: 2K msg/sec → **5 partitions**
- **Target parallelism**: 12 consumers → **12 partitions**

### Key Considerations:
- More partitions = higher parallelism but more overhead
- Cannot reduce partition count (only increase)
- Start conservative, increase based on monitoring
- Typical range: 3-12 partitions for most applications

## Monitoring Metrics

### Producer Metrics
- `record-send-rate`: Messages sent per second
- `request-latency-avg`: Average request latency
- `batch-size-avg`: Average batch size (tune with linger_ms)
- `compression-rate-avg`: Compression effectiveness

### Consumer Metrics
- `records-consumed-rate`: Messages consumed per second
- `fetch-latency-avg`: Average fetch latency
- `records-lag-max`: Maximum consumer lag (should be < 1000)
- `commit-latency-avg`: Commit performance

### Broker Metrics
- `UnderReplicatedPartitions`: Should be 0
- `OfflinePartitionsCount`: Should be 0
- `ActiveControllerCount`: Should be 1
- `RequestsPerSec`: Overall load

## Retention Policy Guidelines

### Time-Based Retention
```yaml
retention.ms: {{ days * 86400000 }}
```

**Recommendations:**
- **Audit logs**: 365+ days (compliance)
- **Application events**: 7-30 days
- **High-volume streams**: 1-7 days
- **Development**: 1-3 days

### Size-Based Retention
```yaml
retention.bytes: {{ bytes_per_partition }}
```

Use when disk space is limited. Combine with time-based retention.

### Log Compaction
```yaml
cleanup.policy: compact
```

For event sourcing where you need latest state per key (e.g., user profiles, configuration).
