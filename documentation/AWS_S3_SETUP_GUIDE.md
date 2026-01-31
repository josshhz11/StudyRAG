# AWS_S3_SETUP_GUIDE.md

# 🚀 AWS S3 Integration Setup Guide

## Step-by-Step Instructions

### 1️⃣ Complete AWS Console Setup

#### A. Create IAM User
1. Go to [IAM Console](https://console.aws.amazon.com/iam/)
2. Click **Users** → **Create user**
3. Username: `studyrag-app-user`
4. Click **Next**
5. Select **Attach policies directly**
6. Search and select: `AmazonS3FullAccess` (or use custom policy below)
7. Click **Next** → **Create user**

#### B. Generate Access Keys
1. Click on the newly created user
2. Go to **Security credentials** tab
3. Scroll to **Access keys** → **Create access key**
4. Choose: **Application running outside AWS**
5. Click **Next** → **Create access key**
6. **IMPORTANT**: Copy both keys now (you won't see the secret again!)
   - Access Key ID: `AKIA...`
   - Secret Access Key: `wJalr...`

#### C. Configure S3 Bucket
1. Go to [S3 Console](https://console.aws.amazon.com/s3/)
2. Click on `studyrag-prototyping-s3-bucket-1`
3. **Permissions** tab:
   - **Block Public Access**: Keep ALL enabled (secure)
   - **Bucket Policy**: Add this (replace `YOUR-ACCOUNT-ID`):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "AWS": "arn:aws:iam::YOUR-ACCOUNT-ID:user/studyrag-app-user"
         },
         "Action": [
           "s3:GetObject",
           "s3:PutObject",
           "s3:DeleteObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::studyrag-prototyping-s3-bucket-1",
           "arn:aws:s3:::studyrag-prototyping-s3-bucket-1/*"
         ]
       }
     ]
   }