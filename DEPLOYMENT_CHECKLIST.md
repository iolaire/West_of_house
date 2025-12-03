# Deployment Checklist

Use this checklist before and after deploying to production.

## Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing locally (`npm test`)
- [ ] No TypeScript errors (`npx tsc --noEmit`)
- [ ] No console errors in browser DevTools
- [ ] Code reviewed (if team project)
- [ ] All changes committed to `main` branch

### Configuration
- [ ] Environment variables configured correctly
  - [ ] `.env.development` for local development
  - [ ] `.env.production` for production builds
  - [ ] `.env.local` for local overrides (if needed)
- [ ] `amplify.yml` configuration is correct
- [ ] `vite.config.ts` build settings are correct
- [ ] `package.json` scripts are working

### Assets
- [ ] All room images present in `images/` directory
- [ ] Images copied to `public/images/` (`npm run copy-images`)
- [ ] WebP conversion working (`npm run convert-webp`)
- [ ] Image file sizes optimized (<100 KB per image)

### Testing
- [ ] Local build successful (`npm run build`)
- [ ] Preview build locally (`npm run preview`)
- [ ] Test in sandbox environment (`npx ampx sandbox`)
- [ ] E2E tests passing (`npm run test:e2e`)

### Git
- [ ] All changes committed
- [ ] Commit messages are descriptive
- [ ] No merge conflicts with `production` branch
- [ ] Branch is up to date (`git pull origin main`)

## Deployment Steps

- [ ] Switch to production branch (`git checkout production`)
- [ ] Merge main branch (`git merge main --no-edit`)
- [ ] Push to trigger deployment (`git push origin production`)
- [ ] Monitor Amplify Console for build progress
- [ ] Wait for deployment to complete (5-12 minutes)

## Post-Deployment Verification

### Build Verification
- [ ] Build succeeded in Amplify Console
- [ ] No errors in build logs
- [ ] All phases completed successfully
  - [ ] Backend preBuild
  - [ ] Backend build
  - [ ] Frontend preBuild
  - [ ] Frontend build
  - [ ] Deploy

### Resource Verification
- [ ] Lambda functions deployed
  - [ ] `gameHandler` function exists
  - [ ] Function has correct IAM role
  - [ ] Environment variables set correctly
- [ ] DynamoDB table created
  - [ ] `GameSession` table exists
  - [ ] TTL enabled for session cleanup
- [ ] API Gateway configured
  - [ ] GraphQL endpoint accessible
  - [ ] CORS configured correctly
- [ ] Frontend deployed
  - [ ] Static files in S3/CloudFront
  - [ ] Cache headers configured
  - [ ] Security headers present

### Functional Testing
- [ ] Application loads at Amplify URL
- [ ] No console errors in browser DevTools
- [ ] Create new game session works
- [ ] Send commands and receive responses
- [ ] Room images load correctly
- [ ] Dissolve transitions work smoothly
- [ ] Command history displays correctly
- [ ] Session persists after page refresh
- [ ] Error handling works (invalid commands)

### Performance Testing
- [ ] Initial page load < 3 seconds
- [ ] Room transitions complete in 3 seconds
- [ ] API responses < 1 second
- [ ] Images load quickly (lazy loading working)
- [ ] No memory leaks (check DevTools Memory tab)

### Accessibility Testing
- [ ] Keyboard navigation works (Tab key)
- [ ] Focus indicators visible
- [ ] Screen reader compatible (test with VoiceOver/NVDA)
- [ ] Alt text present on images
- [ ] Color contrast meets WCAG AA standards

### Security Testing
- [ ] HTTPS enforced (no mixed content warnings)
- [ ] Security headers present (check Network tab)
  - [ ] X-Content-Type-Options: nosniff
  - [ ] X-Frame-Options: DENY
  - [ ] X-XSS-Protection: 1; mode=block
  - [ ] Referrer-Policy: strict-origin-when-cross-origin
- [ ] No sensitive data in client-side code
- [ ] API calls use proper authentication

### Monitoring Setup
- [ ] CloudWatch Logs accessible
- [ ] CloudWatch Metrics configured
- [ ] AWS Budgets alert set up ($5/month threshold)
- [ ] Error tracking enabled (if using service like Sentry)

### Cost Verification
- [ ] Check AWS Cost Explorer for current costs
- [ ] Verify costs are within expected range
- [ ] Cache headers reducing data transfer
- [ ] Lambda execution time < 500ms
- [ ] DynamoDB read/write units reasonable

## Post-Deployment Tasks

### Git Sync
- [ ] Switch back to main branch (`git checkout main`)
- [ ] Merge production changes (`git merge production`)
- [ ] Push updated main (`git push origin main`)

### Documentation
- [ ] Update CHANGELOG.md (if exists)
- [ ] Update version number (if applicable)
- [ ] Document any configuration changes
- [ ] Update README.md if needed

### Communication
- [ ] Notify team of deployment
- [ ] Share deployment URL
- [ ] Document any known issues
- [ ] Schedule follow-up monitoring

## Rollback Plan

If issues are found after deployment:

- [ ] Identify the issue (check logs, metrics, user reports)
- [ ] Determine if rollback is necessary
- [ ] Execute rollback:
  ```bash
  git checkout production
  git revert HEAD
  git push origin production
  ```
- [ ] Verify rollback successful
- [ ] Investigate root cause
- [ ] Fix issue on main branch
- [ ] Re-deploy when ready

## Monitoring Schedule

### First 24 Hours
- [ ] Check CloudWatch Logs every 2 hours
- [ ] Monitor error rates
- [ ] Watch for unusual patterns
- [ ] Respond to any alerts

### First Week
- [ ] Daily check of CloudWatch Metrics
- [ ] Review AWS costs daily
- [ ] Monitor user feedback
- [ ] Address any issues promptly

### Ongoing
- [ ] Weekly review of CloudWatch Logs
- [ ] Monthly cost analysis
- [ ] Quarterly security review
- [ ] Regular dependency updates

## Success Criteria

Deployment is considered successful when:

- ✅ All tests passing
- ✅ Build completed without errors
- ✅ Application loads and functions correctly
- ✅ No critical errors in logs
- ✅ Performance meets targets
- ✅ Costs within budget
- ✅ Security headers present
- ✅ Accessibility standards met

## Notes

Use this space to document deployment-specific notes:

- Deployment date: _______________
- Deployed by: _______________
- Version/commit: _______________
- Issues encountered: _______________
- Resolution: _______________
