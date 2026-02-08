#!/usr/bin/env python3
"""
Calculate Kafka performance parameters based on environment and volume.

Usage:
    python calculate_performance_params.py --volume medium --environment production
"""

import argparse
from typing import Dict, Any


def calculate_params(volume: str, environment: str) -> Dict[str, Any]:
    """
    Calculate Kafka configuration parameters.

    Args:
        volume: Message volume (low, medium, high)
        environment: Deployment environment (local, staging, production)

    Returns:
        Dict with calculated parameters
    """
    # Partition count based on volume
    partition_map = {
        "low": 3,
        "medium": 6,
        "high": 12,
    }

    # Replication factor based on environment
    replication_map = {
        "local": 1,
        "staging": 2,
        "production": 3,
    }

    # Batch size based on volume (bytes)
    batch_size_map = {
        "low": 1024,
        "medium": 16384,
        "high": 32768,
    }

    # max_poll_records based on volume
    max_poll_map = {
        "low": 100,
        "medium": 500,
        "high": 1000,
    }

    partitions = partition_map.get(volume, 6)
    replicas = replication_map.get(environment, 2)
    batch_size = batch_size_map.get(volume, 16384)
    max_poll_records = max_poll_map.get(volume, 500)

    # Calculate min.insync.replicas (always replicas - 1)
    min_insync_replicas = max(1, replicas - 1)

    return {
        "partitions": partitions,
        "replicas": replicas,
        "min_insync_replicas": min_insync_replicas,
        "batch_size": batch_size,
        "max_poll_records": max_poll_records,
        "linger_ms": 10,  # Standard for all volumes
        "compression_type": "gzip",  # Standard for production
    }


def retention_ms(days: int) -> int:
    """Convert retention days to milliseconds."""
    return days * 86400000


def main():
    parser = argparse.ArgumentParser(
        description="Calculate Kafka performance parameters"
    )
    parser.add_argument(
        "--volume",
        required=True,
        choices=["low", "medium", "high"],
        help="Message volume classification",
    )
    parser.add_argument(
        "--environment",
        required=True,
        choices=["local", "staging", "production"],
        help="Deployment environment",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=7,
        help="Message retention in days (default: 7)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    params = calculate_params(args.volume, args.environment)
    params["retention_ms"] = retention_ms(args.retention_days)
    params["retention_days"] = args.retention_days

    if args.json:
        import json
        print(json.dumps(params, indent=2))
    else:
        print(f"Kafka Configuration Parameters")
        print(f"{'='*50}")
        print(f"Environment:          {args.environment}")
        print(f"Volume:               {args.volume}")
        print(f"")
        print(f"Topic Configuration:")
        print(f"  Partitions:         {params['partitions']}")
        print(f"  Replicas:           {params['replicas']}")
        print(f"  min.insync.replicas: {params['min_insync_replicas']}")
        print(f"  retention.ms:       {params['retention_ms']} ({params['retention_days']} days)")
        print(f"  compression.type:   {params['compression_type']}")
        print(f"")
        print(f"Producer Configuration:")
        print(f"  batch_size:         {params['batch_size']} bytes")
        print(f"  linger_ms:          {params['linger_ms']}")
        print(f"  acks:               all")
        print(f"  retries:            3")
        print(f"")
        print(f"Consumer Configuration:")
        print(f"  max_poll_records:   {params['max_poll_records']}")
        print(f"  enable_auto_commit: False")
        print(f"  auto_offset_reset:  earliest")


if __name__ == "__main__":
    main()
