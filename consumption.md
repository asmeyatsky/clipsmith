# Google Cloud Platform Cost Estimate for Clipsmith

## Executive Summary

**Monthly Cost Estimate:**
- **MVP (Ultra-Low-Cost)**: $50-150/month for 100-500 users
- **Production (Light Usage)**: $450-750/month for 500-2,000 users
- **Production (Moderate Usage)**: $2,500+ for 5,000+ users

This document provides a detailed cost analysis for deploying Clipsmith on Google Cloud Platform (GCP) based on the current architecture defined in `docker-compose.production.yml`, plus ultra-low-cost MVP alternatives.

> **💡 For MVP deployment**: See the [Ultra-Low-Cost MVP](#ultra-low-cost-mvp-deployment) section below for $50-150/month serverless options.

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

## Ultra-Low-Cost MVP Deployment

### MVP Option 1: Serverless Stack (~$50-150/month)

**Recommended for MVPs with 100-1,000 users**

| Service | Provider | Monthly Cost |
|---------|----------|--------------|
| Database | Neon (Serverless Postgres) | $0 (free tier) |
| Cache | Upstash Redis | $0 (free tier) |
| Backend API | Cloud Run | $10-30 |
| Frontend | Vercel | $0 (free tier) |
| Storage (100GB) | Cloudflare R2 | $1.50 |
| CDN | Cloudflare | $0 (free tier) |
| Processing | Cloud Run Jobs | $20-40 |
| Monitoring | Sentry + GCP Free | $0 (free tiers) |
| Domain | Namecheap | $1 |
| Email | Resend | $0 (free tier) |
| **Total** | | **$32.50-72.50** |

**With 100 users, 50 videos/day:**
- Egress: <1TB = $0 (free tier)
- Processing: 50 videos × $0.03 = $45/month
- **Total: ~$77-117/month**

**With 500 users, 200 videos/day:**
- Egress: ~2TB = $120/month
- Processing: 200 videos × $0.03 = $180/month
- **Total: ~$332-372/month**

**Key Services:**
- **Neon** - Serverless Postgres with free tier (0.5GB storage, 3GB transfer)
- **Upstash** - Serverless Redis with free tier (10K commands/day)
- **Cloudflare R2** - S3-compatible storage with **zero egress fees** (game-changer!)
- **Cloud Run** - Pay only when processing, scales to zero
- **Vercel** - Free tier with 100GB bandwidth/month

**Advantages:**
- Scales to zero when idle
- Pay only for actual usage
- No infrastructure management
- Free tier maximization
- Quick deployment (1-2 hours)

**Limitations:**
- Free tier limits (will need upgrades at scale)
- Serverless cold starts (300ms-1s delay)
- Less suitable for long-running video processing
- Limited by quotas

**When to upgrade:** When you hit 1,000+ active users or $300/month costs

### MVP Option 2: Single VPS (~$15-30/month)

**Absolute cheapest option for true MVP**

| Service | Provider | Monthly Cost |
|---------|----------|--------------|
| VPS | Hetzner (2 vCPU, 4GB) | €4.49 (~$5) |
| Storage | Backblaze B2 (100GB) | $0.50 |
| CDN | Cloudflare | $0 |
| Domain | Namecheap | $1 |
| SSL | Let's Encrypt | $0 |
| **Total** | | **$6.50** |

**With 100GB video storage + traffic:**
- VPS: $5/month
- Storage: $0.50/100GB
- Egress: Free (Cloudflare CDN)
- **Total: ~$15-30/month**

**Setup:**
Run entire `docker-compose.yml` on a single server:
- PostgreSQL (local)
- Redis (local)
- Backend API
- Frontend (static build)
- Nginx
- Celery workers

**Advantages:**
- Lowest possible cost
- Full control
- Simple deployment
- No vendor lock-in

**Limitations:**
- Single point of failure
- Manual scaling required
- Limited to ~500 users, <100 videos/day
- No high availability

**When to upgrade:** When you consistently exceed 500 active users

### MVP Cost Comparison

| Approach | Monthly Cost | Users | Videos/Day | Setup Time |
|----------|--------------|-------|------------|------------|
| **Single VPS** | **$15-30** | 100-500 | <100 | 2-4 hours |
| **Serverless MVP** | **$50-150** | 100-1,000 | 50-200 | 1-2 hours |
| **GCP Production** | **$542+** | 1,000+ | 500+ | 1-2 days |

### Key MVP Cost Optimizations

1. **Use Cloudflare R2** instead of Cloud Storage
   - **Zero egress fees** vs $0.12/GB
   - Saves $480+/month at moderate scale
   - S3-compatible API

2. **Lazy Video Processing**
   - Only process videos that get viewed (not all uploads)
   - Reduces processing costs by 70-90%
   - Process on-demand vs pre-processing

3. **Free Tier Maximization**
   - Neon: Free Postgres (0.5GB)
   - Upstash: Free Redis (10K commands/day)
   - Vercel: Free hosting (100GB bandwidth)
   - Cloudflare: Free CDN
   - Sentry: Free tier (5K events/month)

4. **Skip Non-Essential Features**
   - ❌ Auto-generated captions (save $0.37/hour)
   - ❌ Multiple quality transcoding (serve original only)
   - ❌ Advanced analytics (use basic metrics)
   - ❌ Real-time notifications (use polling)
   - ❌ Elasticsearch (use PostgreSQL full-text search)

5. **Serverless-First Architecture**
   - Cloud Run: Pay per request, scales to zero
   - Cloud Run Jobs: Pay only when processing videos
   - Cloud Functions: Pay per invocation
   - No idle compute costs

### MVP Migration Path

**Stage 1: MVP ($50-150/month)**
- 100-500 users
- Fully serverless
- Free tier maximization
- Single region

**Stage 2: Growth ($300-800/month)**
- 1,000-5,000 users
- Upgrade database to Cloud SQL
- Add Memorystore Redis
- Enable pre-processing
- Multi-region CDN

**Stage 3: Production ($500-2,000/month)**
- 5,000-20,000 users
- GKE cluster
- Multi-region deployment
- Advanced monitoring
- HA infrastructure

**Stage 4: Scale ($2,000+/month)**
- 20,000+ users
- Auto-scaling
- Global deployment
- Edge computing
- Advanced caching

### MVP Feature Recommendations

**Essential (Keep for MVP):**
- ✅ Video upload & storage
- ✅ Video playback (original quality only)
- ✅ User authentication
- ✅ Basic feed (following/discover)
- ✅ Likes, comments, shares
- ✅ User profiles
- ✅ Search (basic PostgreSQL)
- ✅ Hashtags

**Optional (Add after validation):**
- ⏸️ Auto-generated captions
- ⏸️ Multiple quality transcoding
- ⏸️ Advanced analytics dashboard
- ⏸️ Real-time notifications
- ⏸️ Video editor features
- ⏸️ Payments/monetization
- ⏸️ Live streaming

### Quick Start: Serverless MVP

**1. Set up free tier services:**
```bash
# Sign up for:
- Neon.tech (free Postgres)
- Upstash.com (free Redis)
- Cloudflare R2 (create bucket)
- Vercel.com (free hosting)
- Sentry.io (free monitoring)
```

**2. Deploy backend to Cloud Run:**
```bash
gcloud run deploy clipsmith-backend \
  --image gcr.io/PROJECT/clipsmith-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --min-instances 0 \
  --max-instances 10
```

**3. Deploy frontend to Vercel:**
```bash
cd frontend
vercel --prod
```

**4. Configure Cloudflare:**
- Point domain to Vercel
- Enable proxy (CDN)
- Create R2 bucket for videos

**Total setup time: 2-3 hours**
**Total cost: $50-100/month for first 500 users**

---

## Alternative: Pure Serverless Approach (GCP Only)

For deployments with <1,000 users who want to stay on GCP:

| Service | Monthly Cost |
|---------|--------------|
| Cloud Run (API + Workers) | $50-150 |
| Cloud SQL (db-g1-small) | $27 |
| Cloud Storage (1TB) | $20 |
| Cloud Tasks | $0.40/million tasks |
| CDN | $20 |
| Load Balancer | $18 |
| **Total** | **~$135-235/month** |

**Advantages:**
- All on GCP (single vendor)
- Integrated billing
- Better for enterprise compliance

**Disadvantages:**
- More expensive than multi-cloud MVP
- Still has egress costs ($0.12/GB)
- No free tier benefits from other providers

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

### Phase 0: MVP Launch (Months 1-3)
- **Users**: 100-500
- **Videos**: 50-200/day
- **Monthly Cost**: $50-150
- **Infrastructure**: Serverless MVP (Neon, Upstash, Cloud Run, Vercel, R2)

### Phase 1: Validation (Months 4-6)
- **Users**: 500-2,000
- **Videos**: 200-1,000/day
- **Monthly Cost**: $200-500
- **Infrastructure**: Upgraded serverless or basic GKE

### Phase 2: Growth (Year 1)
- **Users**: 2,000-10,000
- **Videos**: 1,000-5,000/day
- **Monthly Cost**: $500-2,000
- **Infrastructure**: GKE cluster, Cloud SQL, single-region

### Phase 3: Expansion (Year 2)
- **Users**: 10,000-50,000
- **Videos**: 5,000-20,000/day
- **Monthly Cost**: $2,000-$10,000
- **Infrastructure**: Multi-region, autoscaling, CDN optimization

### Phase 4: Scale (Year 3+)
- **Users**: 50,000-500,000
- **Videos**: 20,000-200,000/day
- **Monthly Cost**: $10,000-$50,000
- **Infrastructure**: Global deployment, advanced caching, edge computing

---

## Budget Planning Recommendations

### MVP Budget (Launch Phase)
**Budget: $100-200/month**
- Serverless stack (Neon, Upstash, Cloud Run, Vercel)
- Free tier maximization
- Supports 100-500 active users
- Minimal monitoring and logging
- Perfect for validation phase

### Minimum Viable Infrastructure
**Budget: $600/month**
- Covers basic GKE, Cloud SQL, Redis, 1TB storage
- Supports 500-2,000 active users
- Limited monitoring and logging
- Good for post-validation scaling

### Recommended Starting Budget
**Budget: $1,500/month**
- Production-grade infrastructure
- High availability (HA) database and cache
- Comprehensive monitoring
- Supports 2,000-5,000 active users
- Room for growth and experimentation

### Buffer for Unexpected Costs
- Add 20-30% buffer for:
  - Traffic spikes
  - Development/testing environments
  - Third-party API costs (AssemblyAI, Stripe)
  - Security and compliance tools
  - Viral growth scenarios

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

Clipsmith can start **extremely lean at ~$50-150/month** for MVP using serverless architecture, then scale efficiently to support millions of users. The biggest cost drivers are bandwidth, video processing, and storage - all of which can be optimized through caching, lifecycle policies, and smart architecture decisions.

### Cost Per User

**Expected cost per active user per month:**
- **MVP Phase** (serverless): $0.10-$0.30
- **Growth Phase** (GCP basic): $0.50-$1.00
- **Scale Phase** (GCP production): $1.50-$2.50

For a TikTok-like social video platform, expect costs to scale proportionally with user engagement.

### Recommended Path

**For MVPs (0-500 users):**
1. Start with serverless stack ($50-150/month)
2. Use Cloudflare R2 for zero egress fees
3. Maximize free tiers (Neon, Upstash, Vercel)
4. Implement lazy video processing
5. Set billing alerts at $100, $200

**For Growth (500-5,000 users):**
1. Migrate to Cloud SQL when Neon limits hit
2. Add Memorystore Redis for performance
3. Consider GKE for better control
4. Implement CDN caching aggressively
5. Enable pre-processing for popular videos

**For Scale (5,000+ users):**
1. Full GKE deployment
2. Multi-region infrastructure
3. Advanced monitoring stack
4. Committed use discounts
5. Edge computing for global users

### Next Steps

**Week 1: MVP Launch**
1. Deploy serverless stack (1-2 hours)
2. Set up billing alerts
3. Configure Cloudflare R2 + CDN
4. Launch to first 100 users

**Month 1-3: Validate**
1. Monitor costs daily
2. Optimize based on usage patterns
3. Identify bottlenecks
4. Gather user feedback

**Month 4+: Scale**
1. Migrate to production infrastructure when needed
2. Implement committed use discounts
3. Enable advanced features
4. Plan for global expansion

---

## Additional Resources

- **Full MVP Guide**: See [MVP-DEPLOYMENT.md](./MVP-DEPLOYMENT.md) for complete serverless deployment instructions
- **Architecture**: See [docker-compose.production.yml](./docker-compose.production.yml) for production infrastructure
- **Audit Report**: See [audit.md](./audit.md) for security and quality findings

---

*Last Updated: 2026-02-11*
*Based on: docker-compose.production.yml infrastructure + serverless MVP alternatives*
