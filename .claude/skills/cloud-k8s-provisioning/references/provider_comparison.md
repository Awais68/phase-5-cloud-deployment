# Cloud Provider Comparison

## Free Tier Credits

| Provider | Credit | Duration | Best For |
|----------|--------|----------|----------|
| **Google Cloud (GKE)** | $300 | 90 days | Production workloads, high performance |
| **Azure (AKS)** | $200 | 30 days | Enterprise integration, Windows workloads |
| **Oracle Cloud (OKE)** | Always Free | Forever | Cost-sensitive projects, long-term dev/test |

## Recommendation

**Oracle Cloud (OKE) is recommended** for:
- Zero ongoing cost with Always Free tier
- VM.Standard.E2.1.Micro shape (2 instances free)
- 200GB total block storage
- 10GB object storage
- Suitable for dev/test and small production workloads

## Prerequisites Setup

### GCP
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Azure
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
az login
az account show
```

### Oracle Cloud
```bash
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
oci setup config
```

## Cost Optimization Tips

### GKE
- Use preemptible VMs for non-production
- Enable cluster autoscaler
- Use regional clusters only when needed
- Clean up unused node pools

### AKS
- Use B-series VMs for dev/test
- Enable cluster autoscaler
- Use spot instances for fault-tolerant workloads
- Monitor with Azure Monitor (included)

### OKE
- Use Always Free shapes exclusively
- Limit to 2 nodes (Always Free limit)
- Use object storage for backups (10GB free)
- Monitor resource usage regularly
