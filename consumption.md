# Google Cloud Platform Cost Estimate for Clipsmith

## Executive Summary

**Monthly Cost Estimate: $450 - $750/month (light usage) to $2,500+ (moderate usage)**

This document provides a detailed cost analysis for deploying Clipsmith on Google Cloud Platform (GCP) based on the current architecture defined in `docker-compose.production.yml`.

---

## Core Infrastructure Costs

### 1. Compute (GKE or Cloud Run)

**GKE Autopilot Cluster** (recommended): $73-150/month base
- Backend API (2 vCPU, 1GB): ~$50/month
- Celery Workers (2 vCPU, 2GB): ~$75/month
- Frontend (Next.js): ~$30/month
- Nginx/Load Balancer: Included in GKE ingress

**Alternative - Cloud Run**: $0-100/month
- Scales to zero when idle
- Limited for video processing workloads

### 2. Database - Cloud SQL PostgreSQL

- **db-custom-2-7680** (2 vCPU, 7.5GB RAM): ~$150/month
- 100GB SSD storage: ~$17/month
- Automated backups: ~$10/month
- **Total: ~$177/month**

### 3. Cache - Memorystore Redis

- **Basic Tier M1** (1GB): ~$48/month
- **Standard Tier M1** (1GB, HA): ~$96/month (recommended for production)

### 4. Storage - Cloud Storage

**Video/Media Storage**: $0.020/GB/month
- 1TB videos: ~$20/month
- 10TB videos: ~$200/month
- 100TB videos: ~$2,000/month

**Egress/Bandwidth**: $0.12/GB (first 1TB free/month)
- Light: 1TB/month = Free
- Moderate: 5TB/month = ~$480/month
- Heavy: 20TB/month = ~$2,280/month

### 5. Logging & Monitoring

**Cloud Logging**: First 50GB free, then $0.50/GB
- Estimate: ~$25-50/month

**Cloud Monitoring**: Free tier usually sufficient

**Alternative**: Keep Prometheus/Grafana/Elasticsearch in-cluster
- Adds ~$100/month compute cost
- More control and customization

### 6. Third-Party Services

- **Sentry** (error tracking): $26-80/month (10K-50K events)
- **Stripe** (payments): 2.9% + $0.30 per transaction
- **AssemblyAI** (captions): $0.37/hour of audio

### 7. CDN - Cloud CDN

- Cache hit ratio ~80%: ~$20-100/month depending on traffic
- Critical for reducing egress costs

### 8. Load Balancing

- **Global HTTPS Load Balancer**: ~$18/month base + $0.008/GB

### 9. Video Processing (FFmpeg workers)

**This is the biggest variable cost**
- Light: 100 videos/day → ~$50/month
- Moderate: 1,000 videos/day → ~$300/month
- Heavy: 10,000 videos/day → ~$2,000+/month

---

## Cost Breakdown by Usage Tier

### Tier 1: Startup (100 users, 500 videos/day)

| Service | Monthly Cost |
|---------|--------------|
| GKE Compute | $155 |
| Cloud SQL PostgreSQL | $177 |
| Memorystore Redis (HA) | $96 |
| Cloud Storage (1TB) | $20 |
| Egress (1TB free) | $0 |
| Logging & Monitoring | $30 |
| CDN | $20 |
| Load Balancer | $18 |
| Sentry | $26 |
| **Monthly Total** | **~$542** |

### Tier 2: Growth (5,000 users, 2,000 videos/day)

| Service | Monthly Cost |
|---------|--------------|
| GKE Compute (scaled) | $350 |
| Cloud SQL (upgraded) | $350 |
| Memorystore Redis (HA) | $96 |
| Cloud Storage (10TB) | $200 |
| Egress (5TB) | $480 |
| Video Processing | $300 |
| Logging & Monitoring | $75 |
| CDN | $100 |
| Load Balancer | $40 |
| Sentry | $80 |
| **Monthly Total** | **~$2,071** |

### Tier 3: Scale (50,000 users, 10,000 videos/day)

| Service | Monthly Cost |
|---------|--------------|
| GKE Compute (autoscaled) | $800 |
| Cloud SQL (HA + replicas) | $700 |
| Memorystore Redis (HA) | $192 |
| Cloud Storage (100TB) | $2,000 |
| Egress (20TB) | $2,280 |
| Video Processing | $2,000 |
| Logging & Monitoring | $200 |
| CDN | $500 |
| Load Balancer | $100 |
| Sentry | $199 |
| **Monthly Total** | **~$8,971** |

---

## Cost Optimization Recommendations

### 1. Storage Optimization
- **Use Cloud Storage lifecycle policies** - Move old/rarely accessed videos to Coldline ($0.004/GB) or Archive ($0.0012/GB) storage
- **Implement intelligent tiering** - Videos older than 30 days → Coldline, older than 90 days → Archive
- **Enable compression** - Use modern codecs (H.265/HEVC) to reduce storage by 40-50%

### 2. Network Cost Reduction
- **Enable CDN caching** - Reduces egress costs by 70-90%
- **Use Cloud CDN or Cloud Storage signed URLs** - Cache popular videos at edge locations
- **Implement adaptive bitrate streaming** - Serve lower quality to users with slower connections
- **Consider multi-CDN strategy** - Mix GCP CDN with cheaper alternatives like Cloudflare or BunnyCDN

### 3. Compute Optimization
- **Use preemptible VMs** for Celery workers - 60-80% cost reduction
  - Perfect for batch video processing jobs
  - Implement job retry logic
- **Enable Horizontal Pod Autoscaling (HPA)** - Scale down during off-peak hours
- **Use spot instances** for non-critical workloads
- **Right-size your instances** - Monitor CPU/memory usage and adjust

### 4. Commitment Discounts
- **Committed Use Discounts** - 37% discount for 1-year, 55% for 3-year commitments
- **Sustained Use Discounts** - Automatic discounts for consistent usage (up to 30%)
- **Custom machine types** - Pay only for exactly what you need

### 5. Database Optimization
- **Use Cloud SQL read replicas** - Offload read traffic from primary
- **Enable query insights** - Identify and optimize slow queries
- **Implement connection pooling** - Reduce connection overhead
- **Use Cloud Storage for backups** - Cheaper than Cloud SQL automated backups

### 6. Video Processing Optimization
- **Batch video processing** during off-peak hours - Take advantage of preemptible VMs
- **Use Cloud Tasks** instead of Redis for job queuing - Cheaper at scale, serverless
- **Implement smart transcoding** - Only generate formats users actually request
- **Consider Cloud Functions** for lightweight processing - Pay per invocation

### 7. Monitoring & Logging
- **Set log retention policies** - Don't keep logs forever
- **Use sampling** for high-volume logs - 10% sampling often sufficient
- **Export logs to Cloud Storage** - Much cheaper long-term storage ($0.020/GB vs $0.50/GB)

### 8. Regional Considerations
- **Cloud Storage Dual-Region** instead of Multi-Region - 50% cheaper, still highly available
- **Deploy in lower-cost regions** - us-central1, us-east1 cheaper than us-west1
- **Use regional endpoints** - Reduce cross-region data transfer

---

## Alternative: Pure Serverless Approach

For early-stage deployments with <1,000 users:

| Service | Monthly Cost |
|---------|--------------|
| Cloud Run (API + Workers) | $50-150 |
| Cloud SQL (smallest instance) | $177 |
| Cloud Storage (1TB) | $20 |
| Cloud Tasks | $0.40/million tasks |
| CDN | $20 |
| Load Balancer | $18 |
| **Total** | **~$267-367/month** |

**Advantages:**
- Scales to zero when idle
- Pay only for actual usage
- Lower operational complexity

**Limitations:**
- Less suitable for long-running video processing jobs
- Missing some monitoring/logging infrastructure
- Limited control over execution environment

---

## Cost Drivers Analysis

### Top 3 Cost Drivers (in order):

1. **Bandwidth/Egress (30-50% of total cost at scale)**
   - Video delivery dominates costs
   - Scales linearly with user engagement
   - CDN caching is critical

2. **Video Processing (20-35% of total cost)**
   - FFmpeg workers for transcoding
   - CPU-intensive operations
   - Can be optimized with batch processing

3. **Storage (15-25% of total cost)**
   - Raw + processed videos
   - Grows continuously
   - Lifecycle policies essential

### Per-User Cost Model

**Expected cost per active user per month:**
- Light user (1-2 videos viewed/day): $0.50-$1.00
- Moderate user (10-20 videos viewed/day): $1.50-$2.50
- Heavy user (50+ videos viewed/day): $3.00-$5.00

**Expected cost per creator per month:**
- Light creator (1-5 videos uploaded/month): $2.00-$5.00
- Moderate creator (10-30 videos uploaded/month): $10.00-$20.00
- Heavy creator (100+ videos uploaded/month): $50.00-$100.00

---

## Scaling Projections

### Year 1: MVP Launch
- **Users**: 100-1,000
- **Videos**: 500-2,000/day
- **Monthly Cost**: $500-$1,500
- **Infrastructure**: Basic GKE cluster, single-region

### Year 2: Growth Phase
- **Users**: 5,000-50,000
- **Videos**: 5,000-20,000/day
- **Monthly Cost**: $2,000-$10,000
- **Infrastructure**: Multi-region, autoscaling, CDN optimization

### Year 3: Scale Phase
- **Users**: 100,000-500,000
- **Videos**: 50,000-200,000/day
- **Monthly Cost**: $15,000-$50,000
- **Infrastructure**: Global deployment, advanced caching, edge computing

---

## Budget Planning Recommendations

### Minimum Viable Infrastructure
**Budget: $600/month**
- Covers basic GKE, Cloud SQL, Redis, 1TB storage
- Supports 100-500 active users
- Limited monitoring and logging

### Recommended Starting Budget
**Budget: $1,500/month**
- Production-grade infrastructure
- High availability (HA) database and cache
- Comprehensive monitoring
- Supports 500-2,000 active users
- Room for growth and experimentation

### Buffer for Unexpected Costs
- Add 20-30% buffer for:
  - Traffic spikes
  - Development/testing environments
  - Third-party API costs (AssemblyAI, Stripe)
  - Security and compliance tools

---

## Comparison: GCP vs AWS vs Azure

| Service | GCP | AWS | Azure |
|---------|-----|-----|-------|
| Compute (K8s) | GKE - $73/mo | EKS - $73/mo | AKS - $73/mo |
| Database (2 vCPU) | Cloud SQL - $177/mo | RDS - $190/mo | Azure DB - $185/mo |
| Redis (1GB HA) | Memorystore - $96/mo | ElastiCache - $105/mo | Azure Cache - $100/mo |
| Storage (1TB) | Cloud Storage - $20/mo | S3 - $23/mo | Blob Storage - $18/mo |
| Egress (5TB) | $480/mo | $450/mo | $435/mo |
| CDN | Cloud CDN - competitive | CloudFront - cheaper | Azure CDN - similar |
| **Estimated Total** | **$846/mo** | **$841/mo** | **$811/mo** |

**GCP Advantages:**
- Best Kubernetes integration (GKE Autopilot)
- Superior data analytics and ML services
- Global fiber network (lower latency)
- Simpler pricing structure

**AWS Advantages:**
- Mature ecosystem
- More third-party integrations
- Better documentation
- Larger marketplace

**Azure Advantages:**
- Slightly lower egress costs
- Good for Microsoft stack integration
- Competitive pricing

**Recommendation:** GCP is ideal for this project due to superior Kubernetes support and future ML/AI integration potential for video analysis and recommendations.

---

## Monitoring and Alerts

Set up billing alerts at:
- 50% of monthly budget
- 75% of monthly budget
- 90% of monthly budget
- 100% of monthly budget

Use **Cloud Billing Budget Alerts** to prevent cost overruns.

Track key cost metrics:
- Cost per active user
- Cost per video processed
- Egress cost per GB
- Storage cost per TB

---

## Conclusion

Clipsmith on GCP can start lean at ~$500-750/month and scale efficiently to support millions of users. The biggest cost drivers are bandwidth, video processing, and storage - all of which can be optimized through caching, lifecycle policies, and smart architecture decisions.

For a TikTok-like social video platform, expect costs to scale proportionally with user engagement. Budget **$0.50-$2.00 per active user per month** depending on video consumption patterns.

**Next Steps:**
1. Start with Tier 1 configuration
2. Implement cost monitoring and alerts
3. Optimize CDN caching early
4. Use lifecycle policies from day one
5. Consider committed use discounts after 3 months of stable usage

---

*Last Updated: 2026-02-11*
*Based on: docker-compose.production.yml infrastructure*
