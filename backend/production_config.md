# Production Configuration for Clipsmith

## Media/CDN Configuration

# For production, serve user-uploaded content from a separate domain
# This helps prevent XSS attacks from user-uploaded content

# Option 1: CDN Domain (recommended for production)
MEDIA_DOMAIN=https://cdn.clipsmith.com
MEDIA_BUCKET=clipsmith-media

# Option 2: Separate subdomain
# MEDIA_DOMAIN=https://media.clipsmith.com

# S3/Media Storage Configuration
AWS_S3_BUCKET=clipsmith-media
AWS_S3_REGION=us-east-1
AWS_CLOUDFRONT_DISTRIBUTION_ID=

# For local development, set to empty/null
# MEDIA_DOMAIN=

## Security Headers for Media

# When serving user content, add these headers:
# X-Content-Type-Options: nosniff
# X-Download-Options: noopen
# X-XSS-Protection: 1; mode=block
