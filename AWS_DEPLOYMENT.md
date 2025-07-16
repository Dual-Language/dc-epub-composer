# AWS ECR Build, Publish, and Local Testing Guide

This guide explains how to build, test, and publish your Dockerized `composingservice` to AWS ECR, and how to test it locally with a mounted storage folder.

---

## Prerequisites

- **AWS Account** with ECR permissions
- **AWS CLI** installed and configured (`aws configure`)
- **Docker** installed and running
- **(Optional) ECS CLI or AWS Copilot** for ECS deployment

---

## 1. Clone the Repository

```bash
git clone <your-repo-url>
cd composingservice
```

---

## 2. Build and Test Locally with Mounted Storage

You can test your service locally and mount a host directory to the container’s `/storage` path.

```bash
# Create a storage directory if it doesn't exist
mkdir -p ./storage

# Build the Docker image
docker build -t composingservice:latest .

# Run the container, mounting the local ./storage folder
docker run --rm -it -p 8000:8000 -v $(pwd)/storage:/storage composingservice:latest
```

- Your application will now use the local `./storage` directory for persistent/shared data.

---

## 3. Create and Push Docker Image to Amazon ECR

### 1. Create an ECR Repository

```bash
aws ecr create-repository --repository-name composingservice
```

### 2. Authenticate Docker to ECR

```bash
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
```

### 3. Build and Tag the Image

```bash
docker build -t composingservice:latest .
docker tag composingservice:latest <account-id>.dkr.ecr.<region>.amazonaws.com/composingservice:latest
```

### 4. Push the Image

```bash
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/composingservice:latest
```

---

## 4. Deploying to ECS with Shared EFS Storage

### 1. Create an EFS File System

- Go to the [EFS Console](https://console.aws.amazon.com/efs/)
- Create a file system, note the EFS ID
- Ensure mount targets exist in your VPC subnets and security group allows NFS (port 2049)

### 2. ECS Task Definition Example (with EFS Volume)

```json
{
  "volumes": [
    {
      "name": "shared-storage",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-xxxxxxx",
        "rootDirectory": "/",
        "transitEncryption": "ENABLED"
      }
    }
  ],
  "containerDefinitions": [
    {
      "name": "composingservice",
      "image": "<account-id>.dkr.ecr.<region>.amazonaws.com/composingservice:latest",
      "mountPoints": [
        {
          "sourceVolume": "shared-storage",
          "containerPath": "/storage"
        }
      ]
    }
  ]
}
```

- This mounts the EFS volume at `/storage` inside your container, matching your local dev setup.

---

## 5. References

- [Amazon ECR](https://aws.amazon.com/ecr/)
- [Amazon ECS](https://aws.amazon.com/ecs/)
- [Amazon EFS](https://aws.amazon.com/efs/)
- [ECS Task Definition Volumes](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/efs-volumes.html)

---

## 6. Troubleshooting

- **ECR Login Failed:** Ensure AWS CLI is configured and you have ECR permissions.
- **Image Pull Failed:** Check if the image exists in ECR.
- **EFS Mount Issues:** Ensure security group allows NFS (2049) and mount targets are in correct subnets.

---

## 7. Security & Best Practices

- Never commit `.env` or secrets to version control.
- Use IAM roles for ECS tasks.
- Use VPC and security groups for network security.
- Set up ECR lifecycle policies to clean up old images.

---

## 8. Next Steps

- Set up CI/CD for automated builds and deployments.
- Configure monitoring and alerting (CloudWatch, etc).
- Implement backup and disaster recovery.

---

**You now have a complete workflow for building, testing, and deploying your composingservice with shared storage, both locally and on AWS!** 