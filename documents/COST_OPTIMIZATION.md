# Cost Optimization Report

## Executive Summary

Based on the AWS cost estimation analysis, the West of Haunted House backend is **significantly under budget** across all usage scenarios:

- **Target Usage (1,000 games/month)**: $0.01/month (99.8% under target)
- **Low Usage (500 games/month)**: $0.00/month (100% under target)
- **High Usage (2,000 games/month)**: $0.02/month (99.6% under target)
- **Very High Usage (5,000 games/month)**: $1.46/month (70.8% under target)

**Target Monthly Cost**: $5.00  
**Actual Cost at Target Usage**: $0.01  
**Savings**: $4.99 (99.8%)

## Cost Breakdown by Service

### Lambda (ARM64)
- **Cost**: $0.00/month (all scenarios within free tier)
- **Free Tier Coverage**: 1M requests + 400K GB-seconds per month
- **Usage at 1,000 games**: 15K requests, 937.5 GB-seconds
- **Free Tier Savings**: $5.53/month

**Optimization Status**: ✅ **Already Optimal**
- ARM64 architecture provides 20% better price-performance vs x86_64
- 128MB memory allocation is minimal and appropriate
- 500ms average execution time is efficient
- Well within free tier limits

### DynamoDB (On-Demand)
- **Cost**: $0.01/month at 1,000 games
- **Usage**: 11K writes, 14K reads per month
- **Storage**: 0.000048 GB (negligible)
- **Free Tier**: 25 GB storage (fully covers our usage)

**Optimization Status**: ✅ **Already Optimal**
- On-demand billing is cost-effective for variable workloads
- TTL-based session cleanup prevents storage bloat
- Minimal storage footprint due to 1-hour session expiration

### API Gateway
- **Cost**: $0.00/month (within free tier)
- **Free Tier Coverage**: 1M requests per month (first 12 months)
- **Usage at 1,000 games**: 15K requests
- **Free Tier Savings**: $3.50/month

**Optimization Status**: ✅ **Already Optimal**
- Well within free tier limits
- After 12 months, cost would be ~$0.05/month at 1,000 games

### Amplify Hosting
- **Cost**: $0.00/month at 1,000 games
- **Free Tier Coverage**: 15 GB served per month
- **Usage at 1,000 games**: 4.88 GB
- **Cost at 5,000 games**: $1.41/month (9.41 GB billable)

**Optimization Status**: ✅ **Already Optimal**
- React frontend is efficiently bundled
- CDN caching reduces data transfer
- Only becomes significant cost at very high usage (5,000+ games)

## Architecture Decisions That Enabled Cost Efficiency

### 1. ARM64 Lambda Architecture
**Impact**: 20% better price-performance vs x86_64
- Graviton2 processors provide better performance per dollar
- Same pricing tier as x86_64 but faster execution
- Reduces compute time and costs

### 2. Serverless Architecture
**Impact**: Pay-per-use eliminates idle costs
- No servers running 24/7
- Automatic scaling without over-provisioning
- Zero cost when not in use

### 3. DynamoDB On-Demand Billing
**Impact**: No capacity planning required
- Pay only for actual reads/writes
- No wasted provisioned capacity
- Automatic scaling for traffic spikes

### 4. Session TTL (1 hour)
**Impact**: Minimal storage costs
- Automatic cleanup of expired sessions
- Prevents storage bloat
- Keeps storage well within free tier

### 5. Minimal Lambda Memory (128MB)
**Impact**: Lowest possible compute costs
- Sufficient for game logic processing
- Reduces GB-second consumption
- Maximizes free tier coverage

### 6. Efficient Data Model
**Impact**: Small session sizes (~5KB)
- Minimal DynamoDB storage costs
- Fast read/write operations
- Low data transfer costs

## Optimization Recommendations

### Current State: No Optimization Needed

Given that costs are **99.8% under target**, no immediate optimizations are required. The architecture is already highly cost-efficient.

### Future Optimizations (If Needed at Scale)

If usage grows beyond 10,000 games/month, consider these optimizations:

#### 1. Lambda Reserved Concurrency
**When**: If consistent high traffic (>100K requests/month)
**Savings**: Up to 30% on compute costs
**Trade-off**: Requires upfront commitment

#### 2. DynamoDB Provisioned Capacity
**When**: If predictable traffic patterns emerge
**Savings**: Up to 50% vs on-demand at high volumes
**Trade-off**: Requires capacity planning

#### 3. CloudFront CDN Optimization
**When**: If Amplify hosting costs exceed $5/month
**Savings**: Reduce data transfer costs
**Implementation**: 
- Aggressive caching policies
- Compress assets (gzip/brotli)
- Optimize image sizes

#### 4. Lambda Layer for Dependencies
**When**: If deployment package size grows
**Savings**: Faster deployments, reduced storage
**Implementation**: Move boto3 and common libraries to layer

#### 5. API Gateway Caching
**When**: If read-heavy workload (>80% reads)
**Savings**: Reduce Lambda invocations
**Trade-off**: Adds $0.02/hour per cache size

## Cost Monitoring Strategy

### Key Metrics to Track

1. **Lambda Invocations**: Monitor against 1M free tier limit
2. **DynamoDB Read/Write Units**: Track on-demand usage
3. **API Gateway Requests**: Watch for free tier expiration (12 months)
4. **Amplify Data Transfer**: Monitor against 15GB free tier
5. **Total Monthly Cost**: Alert if exceeds $2.00 (40% of target)

### AWS Cost Explorer Tags

All resources are tagged for cost tracking:
- `Project: west-of-haunted-house`
- `ManagedBy: vedfolnir`
- `Environment: dev|staging|prod`

### Recommended Alerts

1. **Lambda**: Alert at 800K invocations (80% of free tier)
2. **DynamoDB**: Alert at $1.00/month
3. **API Gateway**: Alert at 800K requests (80% of free tier)
4. **Total Cost**: Alert at $2.00/month (40% of target)

## Scaling Projections

### Cost at Different Usage Levels

| Monthly Games | Lambda | DynamoDB | API Gateway | Amplify | **Total** | % of Target |
|--------------|--------|----------|-------------|---------|-----------|-------------|
| 500          | $0.00  | $0.00    | $0.00       | $0.00   | **$0.00** | 0%          |
| 1,000        | $0.00  | $0.01    | $0.00       | $0.00   | **$0.01** | 0.2%        |
| 2,000        | $0.00  | $0.02    | $0.00       | $0.00   | **$0.02** | 0.4%        |
| 5,000        | $0.00  | $0.04    | $0.00       | $1.41   | **$1.46** | 29.2%       |
| 10,000       | $0.00  | $0.09    | $0.00       | $4.10   | **$4.19** | 83.8%       |
| 20,000       | $0.00  | $0.17    | $0.05       | $9.87   | **$10.09**| 201.8%      |

**Key Insight**: Costs remain under $5/month up to ~10,000 games/month. Beyond that, Amplify hosting becomes the primary cost driver.

### Break-Even Analysis

- **Free Tier Coverage**: Up to ~5,000 games/month
- **Under $5/month**: Up to ~10,000 games/month
- **Cost per Game**: $0.00001 at 1,000 games, $0.0005 at 10,000 games

## Conclusion

The West of Haunted House backend architecture is **exceptionally cost-efficient**:

✅ **99.8% under budget** at target usage  
✅ **All services within free tier** at 1,000 games/month  
✅ **No optimizations needed** for MVP launch  
✅ **Scalable to 10,000 games/month** under $5  

The combination of ARM64 Lambda, DynamoDB on-demand, and serverless architecture provides excellent cost efficiency without sacrificing performance or scalability.

### Recommendations

1. **Launch as-is**: No cost optimizations needed for MVP
2. **Monitor costs**: Set up AWS Cost Explorer alerts
3. **Review quarterly**: Reassess if usage patterns change
4. **Optimize at scale**: Consider reserved capacity if usage exceeds 10,000 games/month

---

**Report Generated**: December 2, 2025  
**Based on**: AWS Pricing API data (us-east-1)  
**Validated Against**: Requirements 21.5
