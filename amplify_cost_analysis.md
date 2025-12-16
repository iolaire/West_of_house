# AWS Amplify Cost Analysis: West of Haunted House
**Project:** West_of_house (App ID: dhi9gcvt4p94z)  
**Analysis Period:** December 3-8, 2025  
**Ignoring Free Tier:** All costs calculated at full rate

---

## Amplify Pricing Structure

### Build Minutes
- **Standard (8GB):** $0.01 per minute
- **Large (16GB):** $0.025 per minute
- **XLarge (72GB):** $0.10 per minute
- **Free Tier:** 1,000 build minutes/month (first 12 months)

### Hosting
- **Requests:** $0.30 per 1M requests
- **Compute Duration:** $0.20 per GB-hour ($0.0000555556 per GB-second)
- **Data Transfer Out:** $0.15 per GB
- **Storage:** $0.023 per GB/month
- **Free Tier:** 15 GB served/month, 5 GB storage (first 12 months)

### WAF (Web Application Firewall)
- **Cost:** $15.00 per month (if enabled)
- **Note:** Not enabled for your project

---

## Your Amplify Usage (Dec 3-8, 2025)

### Build Activity

**Total Builds:** 10 (9 successful, 1 failed)

| Build | Date | Duration | Status | Cost |
|-------|------|----------|--------|------|
| #10 | Dec 6, 10:31 AM | 10.05 min | SUCCESS | $0.10 |
| #9 | Dec 6, 7:54 AM | 9.86 min | SUCCESS | $0.10 |
| #8 | Dec 5, 6:43 PM | 9.87 min | SUCCESS | $0.10 |
| #7 | Dec 5, 6:33 PM | 9.74 min | SUCCESS | $0.10 |
| #6 | Dec 5, 4:19 PM | 10.23 min | SUCCESS | $0.10 |
| #5 | Dec 5, 1:05 PM | 9.58 min | SUCCESS | $0.10 |
| #4 | Dec 5, 11:53 AM | 10.63 min | SUCCESS | $0.11 |
| #3 | Dec 3, 11:16 AM | 9.92 min | SUCCESS | $0.10 |
| #2 | Dec 3, 10:55 AM | 10.71 min | FAILED | $0.11 |
| #1 | Dec 3, 10:19 AM | 15.56 min | SUCCESS | $0.16 |

**Total Build Minutes:** 106.14 minutes  
**Build Cost (ignoring free tier):** **$1.06**

**Analysis:**
- Average build time: 10.6 minutes
- First build (#1) took longest: 15.56 minutes (initial infrastructure setup)
- Subsequent builds consistent: ~10 minutes each
- Build instance: Standard 8GB (4 vCPU, 7 GB memory)

### Hosting Usage (Dec 6-8)

**Total Requests:** 11,391

| Date | Requests | Cost @ $0.30/1M |
|------|----------|-----------------|
| Dec 6 | 11,245 | $0.0034 |
| Dec 7 | 78 | $0.000023 |
| Dec 8 | 68 | $0.000020 |

**Request Cost (ignoring free tier):** **$0.0034**

**Analysis:**
- Dec 6 had spike: 11,245 requests (likely testing/launch day)
- Dec 7-8 normalized: ~73 requests/day (actual user traffic)
- Average: 3,797 requests/day

### Data Transfer Out

**Estimated based on typical React app:**
- Average page size: ~500 KB (React bundle + assets)
- Total requests: 11,391
- Estimated data transfer: 11,391 × 0.5 MB = **5.7 GB**

**Data Transfer Cost (ignoring free tier):** **$0.86**

**Note:** This is an estimate. Actual data transfer depends on:
- React bundle size
- Image assets
- API responses (minimal for your game)
- Browser caching effectiveness

### Storage

**Estimated storage:**
- Build artifacts: ~50 MB (React build output)
- Deployment history: 10 builds × 50 MB = 500 MB
- Total: ~0.5 GB

**Storage Cost (ignoring free tier):** **$0.012/month**

For 6-day period: **$0.0024**

### Compute Duration

**Amplify Hosting Compute** (for SSR/dynamic content):
- Your app: Static React (no SSR)
- Compute duration: **$0.00** (not applicable)

---

## Total Amplify Costs (Ignoring Free Tier)

### December 3-8, 2025 (6 days)

| Component | Usage | Cost |
|-----------|-------|------|
| **Build Minutes** | 106.14 minutes | $1.06 |
| **Hosting Requests** | 11,391 requests | $0.0034 |
| **Data Transfer Out** | ~5.7 GB | $0.86 |
| **Storage** | ~0.5 GB (6 days) | $0.0024 |
| **WAF** | Not enabled | $0.00 |
| **TOTAL (6 days)** | | **$1.93** |

### Monthly Projection (30 days)

**Scenario 1: Current Build Frequency (10 builds/6 days)**
- Builds: 50 builds/month × 10.6 min = 530 minutes → **$5.30**
- Requests: 11,000/day × 30 = 330,000 → **$0.10**
- Data Transfer: 28.5 GB/month → **$4.28**
- Storage: 0.5 GB → **$0.012**
- **Monthly Total: $9.69**

**Scenario 2: Reduced Build Frequency (5 builds/month)**
- Builds: 5 builds × 10.6 min = 53 minutes → **$0.53**
- Requests: 2,500/day × 30 = 75,000 → **$0.023**
- Data Transfer: 9.4 GB/month → **$1.41**
- Storage: 0.5 GB → **$0.012**
- **Monthly Total: $1.98**

**Scenario 3: Production Usage (1,000 games/month)**
- Builds: 5 builds/month → **$0.53**
- Requests: 10,000 games × 20 requests = 200,000 → **$0.06**
- Data Transfer: 100 GB/month → **$15.00**
- Storage: 0.5 GB → **$0.012**
- **Monthly Total: $15.60**

---

## Cost Breakdown Analysis

### What's Driving Costs?

**1. Build Minutes (55% of 6-day cost)**
- **$1.06** for 106 minutes
- **Why:** 10 builds in 6 days (frequent deployments)
- **Impact:** High during development, low in production

**2. Data Transfer Out (45% of 6-day cost)**
- **$0.86** for ~5.7 GB
- **Why:** Large React bundle served to users
- **Impact:** Scales with user traffic

**3. Requests (0.2% of cost)**
- **$0.0034** for 11,391 requests
- **Why:** Very cheap per request
- **Impact:** Negligible even at high scale

**4. Storage (<0.1% of cost)**
- **$0.0024** for 0.5 GB
- **Why:** Minimal storage needs
- **Impact:** Negligible

---

## Free Tier Impact

### What Free Tier Covers (First 12 Months)

**Build Minutes:**
- Free tier: 1,000 minutes/month
- Your usage: 106 minutes (6 days) → ~530 minutes/month
- **Covered:** 100% ✅
- **Savings:** $5.30/month

**Data Transfer:**
- Free tier: 15 GB/month
- Your usage: 5.7 GB (6 days) → ~28.5 GB/month
- **Covered:** 52.6% (15 GB of 28.5 GB)
- **Savings:** $2.25/month
- **Billable:** 13.5 GB → $2.03/month

**Storage:**
- Free tier: 5 GB/month
- Your usage: 0.5 GB
- **Covered:** 100% ✅
- **Savings:** $0.012/month

### Actual Cost With Free Tier (Current Usage)

**6-Day Period:**
- Build minutes: $0.00 (covered)
- Requests: $0.00 (negligible)
- Data transfer: $0.00 (within 15 GB)
- Storage: $0.00 (covered)
- **Total: $0.00** ✅

**Monthly (at current rate):**
- Build minutes: $0.00 (covered)
- Requests: $0.10
- Data transfer: $2.03 (13.5 GB over free tier)
- Storage: $0.00 (covered)
- **Total: $2.13/month**

---

## Cost Optimization Recommendations

### 1. Reduce Build Frequency ⚠️ HIGH IMPACT

**Current:** 10 builds in 6 days (1.67 builds/day)

**Recommendation:**
- Batch changes before deploying
- Use `main` branch for development (no builds)
- Only merge to `production` when ready
- Target: 5-10 builds/month

**Savings:** $4.77/month (90% reduction in build costs)

### 2. Optimize Bundle Size 🎯 CRITICAL

**Current:** Estimated ~500 KB per page load

**Recommendations:**

a) **Code Splitting**
```javascript
// Use React lazy loading
const GameComponent = React.lazy(() => import('./GameComponent'));
```
**Impact:** Reduce initial bundle by 30-50%

b) **Tree Shaking**
```javascript
// Import only what you need
import { specific } from 'library'; // Good
import * as all from 'library';     // Bad
```

c) **Compress Assets**
- Enable Brotli compression (Amplify does this automatically)
- Optimize images (use WebP format)
- Minify JSON data files

d) **Analyze Bundle**
```bash
npm run build -- --stats
npx webpack-bundle-analyzer build/bundle-stats.json
```

**Potential Savings:** 50% reduction in data transfer → $7.50/month at scale

### 3. Implement Caching 📦 MEDIUM IMPACT

**Browser Caching:**
- Set long cache headers for static assets
- Use content hashing in filenames (Vite does this)
- Cache API responses in localStorage

**CDN Caching:**
- Amplify uses CloudFront CDN automatically
- Ensure proper cache headers are set

**Impact:** Reduce repeat data transfer by 60-80%

### 4. Monitor and Alert 📊 BEST PRACTICE

**Set up CloudWatch alarms:**
```bash
# Alert if data transfer exceeds 20 GB/month
aws cloudwatch put-metric-alarm \
  --alarm-name "Amplify-DataTransfer-Alert" \
  --metric-name BytesDownloaded \
  --namespace AWS/AmplifyHosting \
  --statistic Sum \
  --period 2592000 \
  --evaluation-periods 1 \
  --threshold 21474836480 \
  --comparison-operator GreaterThanThreshold
```

### 5. Consider Alternative Hosting (If Needed) 💡 LONG-TERM

**If costs exceed $10/month after free tier:**

**Option A: S3 + CloudFront**
- S3 storage: $0.023/GB
- CloudFront: $0.085/GB (first 10 TB)
- **Savings:** ~40% vs Amplify
- **Trade-off:** Manual deployment setup

**Option B: Netlify/Vercel**
- Similar pricing to Amplify
- Different free tier limits
- **Consider:** If Amplify-specific features not needed

**Option C: Self-hosted CDN**
- Cloudflare Pages: Free tier includes 500 builds/month, unlimited bandwidth
- **Savings:** Significant for high-traffic apps
- **Trade-off:** Less AWS integration

---

## Scaling Projections (Ignoring Free Tier)

### At Different Traffic Levels

**100 games/month:**
- Builds: $0.53 (5 builds)
- Requests: 20,000 → $0.006
- Data transfer: 10 GB → $1.50
- **Total: $2.04/month**

**1,000 games/month:**
- Builds: $0.53
- Requests: 200,000 → $0.06
- Data transfer: 100 GB → $15.00
- **Total: $15.60/month**

**10,000 games/month:**
- Builds: $0.53
- Requests: 2,000,000 → $0.60
- Data transfer: 1,000 GB → $150.00
- **Total: $151.13/month**

**With 50% bundle optimization:**

**1,000 games/month:**
- Data transfer: 50 GB → $7.50
- **Total: $8.10/month** ✅ (under $10 target)

**10,000 games/month:**
- Data transfer: 500 GB → $75.00
- **Total: $76.13/month**

---

## Summary

### Current State (Dec 3-8)

**Without Free Tier:** $1.93 (6 days) → **$9.69/month projected**
**With Free Tier:** $0.00 (6 days) → **$2.13/month projected**

### Cost Drivers

1. **Data Transfer (45%)** - Scales with users
2. **Build Minutes (55%)** - High during development
3. **Requests (<1%)** - Negligible
4. **Storage (<1%)** - Negligible

### Recommendations Priority

1. 🔴 **HIGH:** Reduce build frequency (save $4.77/month)
2. 🔴 **HIGH:** Optimize bundle size (save $7.50/month at scale)
3. 🟡 **MEDIUM:** Implement aggressive caching
4. 🟢 **LOW:** Monitor usage with CloudWatch alarms

### Bottom Line

Your Amplify costs are **well-optimized for a React app**. The main cost driver is data transfer, which is expected for a frontend application. With the free tier, you're currently at **$0/month** and projected at **$2.13/month** after the initial development phase.

To stay under $5/month at 1,000 games/month, focus on:
- Reducing bundle size by 50% (code splitting, tree shaking)
- Limiting builds to 5-10/month
- Leveraging browser caching

**Your $5/month target is achievable** with optimization! 🎉
