# MVP Low-Cost Deployment Guide

## Target: $150-250/month for 100-500 users

This guide outlines the most cost-effective deployment strategy for Clipsmith MVP while maintaining core functionality.

---

## Architecture Changes for MVP

### 1. Replace GKE with Cloud Run (Serverless)
**Savings: ~$150/month**

- Backend API → Cloud Run (scales to zero)
- Frontend → Cloud Run or Vercel/Netlify (free tier)
- Workers → Cloud Run Jobs or Cloud Functions
- No cluster management overhead

### 2. Downgrade Cloud SQL
**Savings: ~$100/month**

- Use **db-f1-micro** (shared CPU, 0.6GB RAM): ~$7/month
- Or **db-g1-small** (1 vCPU, 1.7GB RAM): ~$25/month
- Start with 10GB storage: ~$2/month
- **Alternative**: Use **Neon** (serverless Postgres) - $0-20/month with free tier

### 3. Skip Memorystore Redis
**Savings: ~$96/month**

- Use **Upstash Redis** serverless: $0-10/month (10K commands/day free)
- Or use Cloud SQL for caching initially
- Or run Redis in-process with Cloud Run (not recommended long-term)

### 4. Remove Monitoring Stack
**Savings: ~$100/month**

- Remove Prometheus, Grafana, Elasticsearch, Kibana
- Use GCP's free tier:
  - Cloud Monitoring (free)
  - Cloud Logging (50GB/month free)
- Keep Sentry free tier (5K events/month)

### 5. Optimize Storage Strategy
**Target: <100GB = $2/month**

- Start with 100GB limit
- Delete videos older than 30 days initially
- Use **Cloud Storage Coldline** for anything >7 days old
- Implement aggressive compression (H.265)

### 6. Use Free/Cheap Alternatives

**Email Service:**
- ~~AWS SES~~ → **Resend** or **Mailgun** free tier (100 emails/day)

**Video Transcoding:**
- Process on-demand instead of pre-transcoding
- Use **Cloud Run Jobs** with FFmpeg (pay per execution)
- Only generate 1-2 quality levels initially

**CDN:**
- Use **Cloudflare Free** tier instead of Cloud CDN
- Or rely on Cloud Storage direct serving for MVP

**Captions/AI:**
- Skip AssemblyAI initially ($0.37/hour adds up)
- Use **Whisper API** ($0.006/minute) or disable auto-captions
- Let users add manual captions only

---

## Minimal MVP Infrastructure

### Core Services (Required)

| Service | Provider | Tier | Monthly Cost |
|---------|----------|------|--------------|
| **Database** | Cloud SQL | db-g1-small | $27 |
| **Redis Cache** | Upstash | Serverless | $0-10 |
| **Backend API** | Cloud Run | Pay-per-use | $10-30 |
| **Frontend** | Vercel | Free/Hobby | $0-20 |
| **Storage** | Cloud Storage | Standard | $2-10 |
| **Functions** | Cloud Functions | Free tier | $0-5 |
| **CDN** | Cloudflare | Free | $0 |
| **Monitoring** | GCP Free Tier | Free | $0 |
| **Error Tracking** | Sentry | Free | $0 |
| **Load Balancer** | Cloud Run | Included | $0 |
| **Domain** | Namecheap | - | $1 |
| **SSL** | Let's Encrypt | Free | $0 |
| **Total** | | | **$40-103** |

### Additional Costs (Variable)

| Item | Cost |
|------|------|
| Egress (first 1TB free) | $0-50 |
| Video processing | $20-50 |
| Stripe fees (if monetizing) | Variable |
| **Estimated Total** | **$60-200/month** |

---

## Detailed Cloud Run Configuration

### Backend API Service

```yaml
# cloud-run-backend.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: clipsmith-backend
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"  # Scale to zero
        autoscaling.knative.dev/maxScale: "10"
    spec:
      containerConcurrency: 80
      containers:
      - image: gcr.io/PROJECT_ID/clipsmith-backend
        resources:
          limits:
            cpu: "1"
            memory: 512Mi
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
```

**Pricing:**
- CPU: $0.00002400/vCPU-second
- Memory: $0.00000250/GiB-second
- Requests: $0.40/million
- **Estimate**: ~$10-30/month for 100-500 users

### Worker Service (Video Processing)

```yaml
# cloud-run-worker.yaml
apiVersion: run.googleapis.com/v1
kind: Job
metadata:
  name: clipsmith-worker
spec:
  template:
    spec:
      template:
        spec:
          containers:
          - image: gcr.io/PROJECT_ID/clipsmith-worker
            resources:
              limits:
                cpu: "2"
                memory: 2Gi
          maxRetries: 3
          timeoutSeconds: 3600
```

**Pricing:**
- Only pay when processing videos
- ~$0.02-0.05 per video processed
- 100 videos/day = $2-5/month

---

## Alternative: Single VPS Approach

**Even cheaper option for true MVP:**

### DigitalOcean/Hetzner/Linode VPS

| Provider | Specs | Cost |
|----------|-------|------|
| **Hetzner** | 2 vCPU, 4GB RAM, 40GB SSD | **€4.49 (~$5/month)** |
| **DigitalOcean** | 1 vCPU, 2GB RAM, 50GB SSD | **$12/month** |
| **Linode** | 1 vCPU, 2GB RAM, 50GB SSD | **$12/month** |
| **Vultr** | 1 vCPU, 2GB RAM, 55GB SSD | **$12/month** |

**Total MVP Cost with VPS:**
- VPS: $5-12/month
- Cloudflare CDN: Free
- Backblaze B2 storage: $0.005/GB = $5 for 1TB
- Domain: $1/month
- SSL: Free (Let's Encrypt)
- **Total: $11-18/month**

**Setup:**
```bash
# Single server runs everything
- PostgreSQL (local)
- Redis (local)
- Backend API
- Frontend (static build)
- Nginx
- Celery workers

# Use docker-compose.yml from repo
docker-compose up -d
```

**Limitations:**
- Single point of failure
- Manual scaling required
- Less reliable than cloud
- Good for <500 users, <100 videos/day

---

## Database Optimization for MVP

### Option 1: Cloud SQL db-g1-small ($27/month)
```
1 vCPU, 1.7GB RAM, 10GB storage
Good for 500-1000 users
```

### Option 2: Neon Serverless Postgres ($0-20/month)
```
Free tier: 0.5GB storage, 3GB data transfer
Scales to zero
Perfect for MVP
No maintenance
```

### Option 3: PlanetScale MySQL ($0-29/month)
```
Free tier: 5GB storage, 1 billion row reads
Serverless, auto-scaling
Great developer experience
```

### Option 4: Supabase ($0-25/month)
```
Free tier: 500MB database, 1GB file storage
Includes auth, realtime, storage
All-in-one backend
```

**Recommendation**: Start with **Neon** or **Supabase** free tier, migrate to Cloud SQL when you hit limits.

---

## Storage Strategy for MVP

### 1. Cloud Storage Only (No CDN initially)
- Use signed URLs for direct access
- Enable CORS for browser uploads
- ~$2/month for 100GB

### 2. Cloudflare R2 (S3-compatible, no egress fees)
- $0.015/GB storage (cheaper than GCS)
- **Zero egress fees** (huge savings)
- Compatible with AWS SDK
- ~$1.50/month for 100GB + FREE bandwidth

### 3. Backblaze B2 (Cheapest option)
- $0.005/GB storage (4x cheaper than Cloud Storage)
- $0.01/GB egress (but first 3x storage is free)
- ~$0.50/month for 100GB

**Recommendation**: Use **Cloudflare R2** for best economics (no egress fees is game-changer).

---

## Video Processing Strategy

### MVP Approach: Lazy Processing

**Don't pre-process everything:**
```python
# On upload:
1. Store original video in R2/Cloud Storage
2. Generate thumbnail only
3. Return success immediately

# On first view:
1. Check if processed version exists
2. If not, trigger Cloud Run job to process
3. Serve original while processing
4. Cache processed version
```

**Benefits:**
- Only process videos that get viewed
- Reduce processing costs by 70-90%
- Faster upload experience

### Processing Costs

| Approach | Cost/Video | 100 videos/day |
|----------|-----------|----------------|
| Pre-process all | $0.05 | $150/month |
| Lazy process (30% viewed) | $0.05 | $45/month |
| On-demand only | $0.05 | $15/month |

**Recommendation**: Start with lazy processing, move to pre-processing as you grow.

---

## Frontend Deployment

### Option 1: Vercel (Recommended for MVP)
- Free tier: 100GB bandwidth/month
- Automatic deployments
- Edge network
- **$0/month** until you hit limits

### Option 2: Netlify
- Free tier: 100GB bandwidth/month
- Similar to Vercel
- **$0/month**

### Option 3: Cloud Run
- More control
- ~$5-10/month
- Self-hosted

### Option 4: Cloudflare Pages
- Free tier: Unlimited bandwidth
- **$0/month** with best bandwidth deal

**Recommendation**: Start with **Vercel** or **Cloudflare Pages** free tier.

---

## Monitoring on a Budget

### Free Monitoring Stack

1. **Cloud Monitoring** (GCP Free Tier)
   - Basic metrics included
   - Custom metrics: 150 metrics free

2. **Sentry** (Free Tier)
   - 5,000 events/month
   - Error tracking
   - Performance monitoring

3. **UptimeRobot**
   - Free uptime monitoring
   - 50 monitors
   - 5-minute checks

4. **Better Stack (formerly Logtail)**
   - 1GB logs/month free
   - Log management
   - Alerting

**Cost**: $0/month with free tiers

---

## Complete MVP Tech Stack

### Infrastructure
```yaml
Compute: Cloud Run (serverless, pay-per-use)
Database: Neon Postgres (serverless, free tier)
Cache: Upstash Redis (serverless, free tier)
Storage: Cloudflare R2 (S3-compatible, no egress fees)
CDN: Cloudflare (free tier)
Frontend: Vercel (free tier)
Processing: Cloud Run Jobs (on-demand)
```

### Services
```yaml
Auth: Supabase Auth (free) or custom JWT
Email: Resend (free tier: 100/day)
SMS: Twilio (pay-as-go, skip for MVP)
Payments: Stripe (skip for MVP, add later)
Analytics: Plausible self-hosted or Google Analytics
Error Tracking: Sentry (free tier)
Monitoring: Cloud Monitoring + UptimeRobot (free)
```

---

## Cost Breakdown: Ultra-Low MVP

| Service | Provider | Monthly Cost |
|---------|----------|--------------|
| Database | Neon | $0 (free tier) |
| Cache | Upstash Redis | $0 (free tier) |
| Backend API | Cloud Run | $10-20 |
| Frontend | Vercel | $0 (free tier) |
| Storage (100GB) | Cloudflare R2 | $1.50 |
| CDN | Cloudflare | $0 (free tier) |
| Processing | Cloud Run Jobs | $20-40 |
| Monitoring | Sentry + GCP | $0 (free tiers) |
| Domain | Namecheap | $1 |
| Email | Resend | $0 (free tier) |
| **Total** | | **$32.50-62.50** |

### With 100 active users, 50 videos/day:
- Egress: <1TB = $0 (free tier)
- Processing: 50 videos × $0.03 = $1.50/day = $45/month
- **Total: ~$77-107/month**

### With 500 active users, 200 videos/day:
- Egress: ~2TB = $120/month
- Processing: 200 videos × $0.03 = $6/day = $180/month
- **Total: ~$332-382/month**

---

## Migration Path (as you grow)

### Stage 1: MVP ($50-150/month)
- 100-500 users
- Fully serverless
- Free tier maximization
- Single region

### Stage 2: Growth ($300-800/month)
- 1,000-5,000 users
- Upgrade database to Cloud SQL
- Add Memorystore Redis
- Enable pre-processing
- Multi-region CDN

### Stage 3: Scale ($2,000+/month)
- 10,000+ users
- GKE cluster
- Multi-region deployment
- Dedicated infrastructure
- Advanced monitoring

---

## Deployment Steps (Serverless MVP)

### 1. Set up Neon Database
```bash
# Sign up at neon.tech
# Create database
# Get connection string
export DATABASE_URL="postgresql://user:pass@neon.tech/clipsmith"
```

### 2. Set up Cloudflare R2
```bash
# Create R2 bucket
# Get access credentials
export R2_ACCESS_KEY_ID="..."
export R2_SECRET_ACCESS_KEY="..."
export R2_BUCKET_NAME="clipsmith-videos"
```

### 3. Deploy Backend to Cloud Run
```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/clipsmith-backend

# Deploy
gcloud run deploy clipsmith-backend \
  --image gcr.io/PROJECT_ID/clipsmith-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$DATABASE_URL \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10
```

### 4. Deploy Frontend to Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel --prod
```

### 5. Set up Cloudflare CDN
```bash
# Point domain to Vercel
# Enable Cloudflare proxy
# Configure caching rules
```

**Total setup time: 2-3 hours**

---

## Feature Cuts for MVP

To keep costs minimal, consider cutting:

### Non-Essential Features (Add Later)
- ❌ Auto-generated captions (save $0.37/hour)
- ❌ Multiple quality transcoding (serve original only)
- ❌ Advanced analytics (use basic metrics)
- ❌ Real-time notifications (use polling)
- ❌ Elasticsearch (use PostgreSQL full-text search)
- ❌ Video editor (TikTok-style effects)
- ❌ Payments/monetization
- ❌ Live streaming

### Essential Features (Keep)
- ✅ Video upload & storage
- ✅ Video playback
- ✅ User authentication
- ✅ Basic feed (following/discover)
- ✅ Likes, comments, shares
- ✅ User profiles
- ✅ Search (basic)
- ✅ Hashtags

---

## Performance Considerations

### Database (Neon Free Tier)
- **Limit**: 0.5GB storage
- **Capacity**: ~5,000-10,000 users (metadata only)
- **Strategy**: Store only essential data, offload to storage

### Storage (Cloudflare R2)
- **No egress fees** = unlimited video views at no extra cost
- **Limit**: None (pay-as-you-go)
- **Capacity**: Unlimited

### Compute (Cloud Run)
- **Limit**: 1000 concurrent requests
- **Capacity**: ~5,000-10,000 active users
- **Strategy**: Scales automatically

---

## Risk Assessment

### Low-Cost MVP Risks

**Technical Risks:**
- Free tier limits hit faster than expected
- Serverless cold starts (300ms-1s delay)
- No dedicated support
- Harder to debug distributed issues

**Mitigation:**
- Set up billing alerts at $50, $100, $150
- Use Cloud Run min instances (1) during peak hours
- Implement comprehensive logging
- Keep architecture simple

**Business Risks:**
- Viral growth → sudden cost spike
- Can't handle traffic spikes well
- Limited by free tier quotas

**Mitigation:**
- Implement rate limiting
- Use waitlist for growth control
- Have scaling plan ready
- Monitor costs daily

---

## Success Metrics for MVP

### When to upgrade from free tiers:

**Database (Neon):**
- Approaching 0.5GB storage limit
- Need more than 3GB data transfer/month
- Require better performance

**Backend (Cloud Run):**
- Consistently using >500M requests/month
- Need lower latency (<100ms)
- Require WebSocket support

**Storage:**
- Using >1TB (Cloud Storage free tier)
- Need better performance/reliability

---

## Conclusion: Ultra-Low-Cost MVP

### Recommended Approach: **Serverless Stack ($50-150/month)**

**Benefits:**
- Zero infrastructure management
- Automatic scaling
- Pay only for usage
- Quick to deploy
- Easy to iterate

**When to migrate to GKE:**
- Consistent 10,000+ active users
- $500+ monthly cloud costs
- Need better control/customization
- Require advanced features

### Absolute Minimum: **Single VPS ($15-30/month)**

**Benefits:**
- Lowest possible cost
- Full control
- Simple deployment

**Limitations:**
- Manual scaling
- Single point of failure
- Limited to ~500 users

---

## Quick Start Checklist

- [ ] Sign up for Neon (free Postgres)
- [ ] Sign up for Upstash (free Redis)
- [ ] Create Cloudflare R2 bucket
- [ ] Set up Vercel account
- [ ] Configure environment variables
- [ ] Deploy backend to Cloud Run
- [ ] Deploy frontend to Vercel
- [ ] Configure domain & SSL
- [ ] Set up monitoring (Sentry, UptimeRobot)
- [ ] Configure billing alerts
- [ ] Test end-to-end flow
- [ ] Launch! 🚀

**Total time**: 1 day
**Total cost**: $50-100/month
**Capacity**: 500-1,000 users

---

*Last Updated: 2026-02-11*
*Target: Ultra-low-cost MVP deployment*
