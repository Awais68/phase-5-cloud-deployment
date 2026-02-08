# Kafka Security Configuration Patterns

## Security Level Comparison

| Environment | Security Level | Authentication | Encryption | ACLs |
|------------|---------------|----------------|------------|------|
| Local      | None          | None           | No         | No   |
| Staging    | TLS           | Optional       | Yes        | Optional |
| Production | SASL-SSL      | Required       | Yes        | Required |

## Pattern 1: No Security (Development Only)

**Use Case**: Local development, rapid prototyping

### Strimzi Kafka Cluster
```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: dev-cluster
spec:
  kafka:
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
```

### Client Configuration
```python
config = {
    "bootstrap_servers": "localhost:9092",
    "security_protocol": "PLAINTEXT"
}
```

**Warning**: Never use in staging or production.

## Pattern 2: TLS Only (Staging)

**Use Case**: Staging environments, internal services with network-level security

### Strimzi Kafka Cluster
```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: staging-cluster
spec:
  kafka:
    listeners:
      - name: tls
        port: 9093
        type: internal
        tls: true
```

### Client Configuration
```python
config = {
    "bootstrap_servers": "kafka-bootstrap:9093",
    "security_protocol": "SSL",
    "ssl_cafile": "/path/to/ca-cert.pem",
    "ssl_certfile": "/path/to/client-cert.pem",
    "ssl_keyfile": "/path/to/client-key.pem",
}
```

### Certificate Management
```bash
# Extract CA certificate from Kubernetes secret
kubectl get secret staging-cluster-cluster-ca-cert -o jsonpath='{.data.ca\.crt}' | base64 -d > ca-cert.pem

# For client authentication, create KafkaUser with TLS
kubectl apply -f - <<EOF
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaUser
metadata:
  name: app-user
  labels:
    strimzi.io/cluster: staging-cluster
spec:
  authentication:
    type: tls
EOF

# Extract client certificates
kubectl get secret app-user -o jsonpath='{.data.user\.crt}' | base64 -d > client-cert.pem
kubectl get secret app-user -o jsonpath='{.data.user\.key}' | base64 -d > client-key.pem
```

## Pattern 3: SASL-SCRAM (Simple Authentication)

**Use Case**: Production with username/password authentication (no TLS)

### Strimzi Kafka Cluster
```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: prod-cluster
spec:
  kafka:
    listeners:
      - name: sasl
        port: 9094
        type: internal
        tls: false
        authentication:
          type: scram-sha-512
```

### KafkaUser with SCRAM
```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaUser
metadata:
  name: app-user
  labels:
    strimzi.io/cluster: prod-cluster
spec:
  authentication:
    type: scram-sha-512
  authorization:
    type: simple
    acls:
      - resource:
          type: topic
          name: task-events
        operation: Write
      - resource:
          type: topic
          name: task-events
        operation: Read
      - resource:
          type: group
          name: task-consumer-group
        operation: Read
```

### Client Configuration
```python
config = {
    "bootstrap_servers": "kafka-bootstrap:9094",
    "security_protocol": "SASL_PLAINTEXT",
    "sasl_mechanism": "SCRAM-SHA-512",
    "sasl_plain_username": "app-user",
    "sasl_plain_password": "password-from-secret",
}
```

### Extracting SCRAM Credentials
```bash
# Get password from Kubernetes secret
kubectl get secret app-user -o jsonpath='{.data.password}' | base64 -d
```

**Warning**: Without TLS, credentials are transmitted in plaintext. Use only in secure internal networks.

## Pattern 4: SASL-SSL (Production Recommended)

**Use Case**: Production with strong authentication and encryption

### Strimzi Kafka Cluster
```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: prod-cluster
spec:
  kafka:
    listeners:
      - name: sasl-tls
        port: 9095
        type: internal
        tls: true
        authentication:
          type: scram-sha-512
```

### KafkaUser with SASL-SSL
```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaUser
metadata:
  name: app-user
  labels:
    strimzi.io/cluster: prod-cluster
spec:
  authentication:
    type: scram-sha-512
  authorization:
    type: simple
    acls:
      - resource:
          type: topic
          name: task-events
          patternType: literal
        operations:
          - Write
          - Read
          - Describe
      - resource:
          type: group
          name: task-consumer-group
          patternType: literal
        operations:
          - Read
```

### Client Configuration
```python
config = {
    "bootstrap_servers": "kafka-bootstrap:9095",
    "security_protocol": "SASL_SSL",
    "sasl_mechanism": "SCRAM-SHA-512",
    "sasl_plain_username": "app-user",
    "sasl_plain_password": "password-from-secret",
    "ssl_cafile": "/path/to/ca-cert.pem",
}
```

### Complete Setup Script
```bash
#!/bin/bash
# Extract all required security credentials

CLUSTER_NAME="prod-cluster"
USER_NAME="app-user"

# CA certificate
kubectl get secret ${CLUSTER_NAME}-cluster-ca-cert \
  -o jsonpath='{.data.ca\.crt}' | base64 -d > ca-cert.pem

# SCRAM password
PASSWORD=$(kubectl get secret ${USER_NAME} \
  -o jsonpath='{.data.password}' | base64 -d)

echo "CA Certificate: ca-cert.pem"
echo "Username: ${USER_NAME}"
echo "Password: ${PASSWORD}"
```

## ACL Patterns

### Read-Only Consumer
```yaml
spec:
  authorization:
    type: simple
    acls:
      - resource:
          type: topic
          name: events
        operation: Read
      - resource:
          type: topic
          name: events
        operation: Describe
      - resource:
          type: group
          name: consumer-group
        operation: Read
```

### Write-Only Producer
```yaml
spec:
  authorization:
    type: simple
    acls:
      - resource:
          type: topic
          name: events
        operation: Write
      - resource:
          type: topic
          name: events
        operation: Describe
```

### Full Access (Admin)
```yaml
spec:
  authorization:
    type: simple
    acls:
      - resource:
          type: topic
          name: "*"
          patternType: literal
        operations:
          - All
      - resource:
          type: group
          name: "*"
          patternType: literal
        operations:
          - All
```

### Wildcard Topic Access
```yaml
spec:
  authorization:
    type: simple
    acls:
      - resource:
          type: topic
          name: "task-"
          patternType: prefix
        operations:
          - Read
          - Write
          - Describe
```

## Security Best Practices

### 1. Credential Management
- Store credentials in Kubernetes Secrets
- Mount secrets as environment variables or files
- Rotate credentials regularly (every 90 days)
- Never commit credentials to version control

### 2. Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: kafka-access
spec:
  podSelector:
    matchLabels:
      app: kafka
  ingress:
    - from:
      - podSelector:
          matchLabels:
            access: kafka-client
      ports:
        - protocol: TCP
          port: 9095
```

### 3. Least Privilege ACLs
- Grant minimal required permissions
- Use specific topic names (avoid wildcards in production)
- Separate read and write users when possible
- Audit ACLs regularly

### 4. TLS Configuration
- Use TLS 1.2 or higher
- Disable weak cipher suites
- Validate certificates (don't disable verification)
- Use certificate rotation

### 5. Monitoring Security
- Log authentication attempts
- Alert on ACL violations
- Monitor unauthorized access attempts
- Track certificate expiration

## Troubleshooting Security Issues

### Common Issues

**Authentication Failures:**
```bash
# Verify credentials
kubectl get secret app-user -o jsonpath='{.data.password}' | base64 -d

# Check KafkaUser status
kubectl describe kafkauser app-user
```

**Certificate Issues:**
```bash
# Verify CA certificate
openssl x509 -in ca-cert.pem -text -noout

# Test TLS connection
openssl s_client -connect kafka-bootstrap:9093 -CAfile ca-cert.pem
```

**ACL Denials:**
```bash
# Check KafkaUser ACLs
kubectl get kafkauser app-user -o yaml

# View Kafka ACLs directly
kubectl exec -it prod-cluster-kafka-0 -- \
  bin/kafka-acls.sh --bootstrap-server localhost:9092 --list --topic task-events
```

## Migration Path

**Phase 1: Development → Staging**
- Add TLS encryption
- Test with self-signed certificates
- Validate application changes

**Phase 2: Staging → Production**
- Add SASL-SCRAM authentication
- Implement ACLs
- Rotate to production certificates
- Enable monitoring and alerting

**Phase 3: Production Hardening**
- Enforce strict ACLs
- Implement network policies
- Set up certificate rotation
- Enable audit logging
