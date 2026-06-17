# Library Management System – Deployment Guide

> **Version:** 1.0  
> **Last updated:** June 2026  
> **Target platform:** Ubuntu 22.04 LTS on AWS EC2

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Launch EC2 Instance](#step-1--launch-ec2-instance)
3. [Initial Server Setup](#step-2--initial-server-setup)
4. [Install Docker & Docker Compose](#step-3--install-docker--docker-compose)
5. [Install Jenkins](#step-4--install-jenkins)
6. [Configure Jenkins Pipeline](#step-5--configure-jenkins-pipeline)
7. [GitHub Webhook Setup](#step-6--github-webhook-setup)
8. [Deploy the Application](#step-7--deploy-the-application)
9. [Configure Nginx (without Docker)](#step-8--configure-nginx-without-docker)
10. [SSL with Let's Encrypt](#step-9--ssl-with-lets-encrypt)
11. [Domain Configuration](#step-10--domain-configuration)
12. [Monitoring & Maintenance](#monitoring--maintenance)
13. [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Requirement | Details |
|---|---|
| **AWS Account** | Free-tier eligible for t2.micro; t2.medium recommended for production |
| **Domain name** | Optional but recommended for SSL |
| **Git repository** | GitHub / GitLab / Bitbucket with the project source |
| **Local tools** | SSH client, Git, a terminal |

---

## Step 1 – Launch EC2 Instance

### 1.1 Choose an AMI

- Navigate to **EC2 → Launch Instance**
- Select **Ubuntu Server 22.04 LTS (HVM), SSD Volume Type**

### 1.2 Instance Type

| Use-case | Recommended |
|---|---|
| Development / testing | `t2.micro` (1 vCPU, 1 GB RAM) |
| Staging | `t2.small` (1 vCPU, 2 GB RAM) |
| **Production** | **`t2.medium` (2 vCPU, 4 GB RAM)** |

### 1.3 Security Group Rules

| Type | Protocol | Port | Source | Purpose |
|---|---|---|---|---|
| SSH | TCP | 22 | Your IP | Remote access |
| HTTP | TCP | 80 | 0.0.0.0/0 | Web traffic |
| HTTPS | TCP | 443 | 0.0.0.0/0 | Encrypted web traffic |
| Custom TCP | TCP | 8080 | Your IP | Jenkins dashboard |

> **⚠️ Important:** Restrict port 22 and 8080 to your IP or a VPN CIDR block. Never expose them to `0.0.0.0/0` in production.

### 1.4 Key Pair

- Create or select an existing key pair (`.pem` file).
- Store it securely: `chmod 400 your-key.pem`

### 1.5 Storage

- **Minimum:** 20 GB gp3 SSD
- **Recommended:** 30 GB gp3 SSD

### 1.6 Elastic IP

```bash
# After launch, allocate and associate an Elastic IP so the
# public address survives stop/start cycles.
# AWS Console → EC2 → Elastic IPs → Allocate → Associate
```

---

## Step 2 – Initial Server Setup

### 2.1 SSH into the server

```bash
ssh -i your-key.pem ubuntu@<ELASTIC_IP>
```

### 2.2 Update packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git vim ufw software-properties-common
```

### 2.3 Configure firewall (UFW)

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp     # Jenkins
sudo ufw enable
sudo ufw status
```

### 2.4 Create a deploy user (optional)

```bash
sudo adduser deploy
sudo usermod -aG sudo deploy
# Copy your SSH key to the new user
sudo rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
```

### 2.5 Set the timezone

```bash
sudo timedatectl set-timezone Asia/Kolkata   # or your timezone
```

---

## Step 3 – Install Docker & Docker Compose

### 3.1 Install Docker

```bash
# Remove old versions
sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null

# Add Docker's official GPG key & repository
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 3.2 Post-install – run Docker without sudo

```bash
sudo usermod -aG docker $USER
newgrp docker          # or log out and back in
docker --version       # verify
docker compose version # verify compose v2
```

### 3.3 Install Docker Compose (standalone – if needed)

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

---

## Step 4 – Install Jenkins

### 4.1 Install Java (Jenkins dependency)

```bash
sudo apt install -y fontconfig openjdk-17-jre
java -version
```

### 4.2 Add Jenkins repository & install

```bash
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | \
    sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null

echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
    https://pkg.jenkins.io/debian-stable binary/" | \
    sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null

sudo apt update
sudo apt install -y jenkins
```

### 4.3 Start & enable Jenkins

```bash
sudo systemctl start jenkins
sudo systemctl enable jenkins
sudo systemctl status jenkins
```

### 4.4 Allow Jenkins to use Docker

```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

### 4.5 Initial setup

```bash
# Retrieve the initial admin password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

1. Open `http://<ELASTIC_IP>:8080` in your browser.
2. Paste the admin password.
3. Choose **Install Suggested Plugins**.
4. Create your admin user.

### 4.6 Install required plugins

Navigate to **Manage Jenkins → Plugins → Available** and install:

| Plugin | Purpose |
|---|---|
| Git | SCM checkout |
| Pipeline | Declarative & scripted pipelines |
| Docker Pipeline | Docker build steps |
| GitHub Integration | Webhooks & status checks |
| Timestamper | Timestamps in console output |
| Pipeline Utility Steps | File operations & utilities |

---

## Step 5 – Configure Jenkins Pipeline

### 5.1 Create a new Pipeline job

1. **Dashboard → New Item → Pipeline** → name it `library-management-system`.
2. Under **Pipeline**:
   - **Definition:** Pipeline script from SCM
   - **SCM:** Git
   - **Repository URL:** `https://github.com/your-org/library-management-system.git`
   - **Credentials:** Add your GitHub credentials (PAT recommended)
   - **Branch:** `*/main`
   - **Script Path:** `Jenkinsfile`
3. Save.

### 5.2 Set environment variables (optional)

Go to **Manage Jenkins → System → Global properties → Environment variables** and add:

| Variable | Value |
|---|---|
| `DOCKER_IMAGE` | `library-management-system` |
| `DEPLOY_ENV` | `production` |

---

## Step 6 – GitHub Webhook Setup

1. Go to your **GitHub repository → Settings → Webhooks → Add webhook**.
2. Configure:

| Field | Value |
|---|---|
| **Payload URL** | `http://<ELASTIC_IP>:8080/github-webhook/` |
| **Content type** | `application/json` |
| **Secret** | *(optional – configure in Jenkins too)* |
| **Events** | Just the push event |
| **Active** | ✅ |

3. Click **Add webhook**.
4. Verify delivery shows a green ✅ on the webhook page.

> **Tip:** If using HTTPS with a self-signed certificate, select *Disable SSL verification* during testing.

---

## Step 7 – Deploy the Application

### 7.1 Clone the repository

```bash
cd /home/ubuntu
git clone https://github.com/your-org/library-management-system.git
cd library-management-system
```

### 7.2 Create the `.env` file

```bash
cat > .env << 'EOF'
# Flask
SECRET_KEY=your-super-secret-key-change-me
FLASK_ENV=production

# MySQL
MYSQL_HOST=db
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-strong-root-password
MYSQL_DB=library_db
MYSQL_ROOT_PASSWORD=your-strong-root-password

# Mail (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=
MAIL_PASSWORD=
EOF

chmod 600 .env
```

### 7.3 Launch with Docker Compose

```bash
docker compose up -d
```

### 7.4 Verify

```bash
# Check all containers are healthy
docker compose ps

# View logs
docker compose logs -f web

# Test HTTP response
curl -I http://localhost
```

Expected output: three running containers (`lms-web`, `lms-db`, `lms-nginx`) all in a healthy state.

---

## Step 8 – Configure Nginx (without Docker)

> Use this section **only** if you are NOT using the Nginx Docker container (e.g. running Gunicorn directly with systemd).

### 8.1 Install Nginx

```bash
sudo apt install -y nginx
```

### 8.2 Copy the configuration

```bash
sudo cp deployment/nginx.conf /etc/nginx/sites-available/library-management
sudo ln -sf /etc/nginx/sites-available/library-management /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
```

### 8.3 Update upstream

Edit `/etc/nginx/sites-available/library-management` and change the upstream:

```nginx
upstream flask_app {
    server 127.0.0.1:5000;   # Gunicorn running locally
}
```

### 8.4 Test & reload

```bash
sudo nginx -t          # Verify syntax
sudo systemctl reload nginx
sudo systemctl enable nginx
```

---

## Step 9 – SSL with Let's Encrypt

### 9.1 Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 9.2 Obtain certificate

```bash
sudo certbot --nginx -d your_domain.com -d www.your_domain.com
```

Follow the prompts. Certbot will automatically update your Nginx configuration.

### 9.3 Verify auto-renewal

```bash
sudo certbot renew --dry-run
```

### 9.4 Cron for auto-renewal (usually automatic)

```bash
# Certbot installs a systemd timer; verify it is active:
sudo systemctl status certbot.timer

# If not, add a cron job manually:
# sudo crontab -e
# 0 3 * * * certbot renew --quiet && systemctl reload nginx
```

---

## Step 10 – Domain Configuration

### 10.1 DNS A Record

In your domain registrar (GoDaddy, Namecheap, Route 53, etc.):

| Type | Name | Value | TTL |
|---|---|---|---|
| A | `@` | `<ELASTIC_IP>` | 300 |
| A | `www` | `<ELASTIC_IP>` | 300 |

### 10.2 Update Nginx

Replace `server_name _;` with your domain:

```nginx
server_name your_domain.com www.your_domain.com;
```

Reload Nginx:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

### 10.3 Update CORS / allowed hosts

If your Flask app validates hosts, update the `.env` or config accordingly.

---

## Monitoring & Maintenance

### Application logs

```bash
# Docker
docker compose logs -f web        # Flask/Gunicorn logs
docker compose logs -f db         # MySQL logs
docker compose logs -f nginx      # Nginx access/error logs

# Systemd (non-Docker)
sudo journalctl -u library-management -f
```

### Container health

```bash
docker compose ps
docker stats --no-stream
```

### Database backups

```bash
# Manual backup
docker compose exec db mysqldump -u root -p library_db > backup_$(date +%F).sql

# Automated daily backup (add to crontab)
# sudo crontab -e
0 2 * * * docker compose -f /home/ubuntu/library-management-system/docker-compose.yml \
    exec -T db mysqldump -u root -p'YOUR_PASSWORD' library_db \
    | gzip > /home/ubuntu/backups/library_db_$(date +\%F).sql.gz
```

### Database restore

```bash
docker compose exec -T db mysql -u root -p library_db < backup_2026-06-16.sql
```

### Jenkins build history

- Visit `http://<ELASTIC_IP>:8080/job/library-management-system/`
- View console output, test reports, and build trends.

### System monitoring

```bash
# Resource usage
htop
df -h
free -m

# Docker disk usage
docker system df
docker system prune -f   # Clean up unused images/containers
```

---

## Troubleshooting

### Container won't start

```bash
# Check logs
docker compose logs web

# Common causes:
#   - Missing .env file → create it (see Step 7.2)
#   - Port already in use → sudo lsof -i :5000
#   - Database not ready → check db container health
```

### "Access denied" for MySQL

```bash
# Verify credentials match between .env and docker-compose.yml
docker compose exec db mysql -u root -p -e "SHOW DATABASES;"

# Reset root password if needed:
docker compose down -v    # WARNING: deletes data
# Re-configure MYSQL_ROOT_PASSWORD in .env, then:
docker compose up -d
```

### Nginx returns 502 Bad Gateway

```bash
# The web container is likely not running or not reachable
docker compose ps          # Is 'web' running?
docker compose logs web    # Any crash logs?

# Test connectivity from Nginx container:
docker compose exec nginx wget -qO- http://web:5000 || echo "Cannot reach web"
```

### Jenkins build fails

| Symptom | Solution |
|---|---|
| `docker: permission denied` | `sudo usermod -aG docker jenkins && sudo systemctl restart jenkins` |
| `pytest not found` | Ensure `venv` creation step succeeded in the pipeline |
| Git checkout fails | Verify credentials under **Jenkins → Credentials** |
| Health check timeout | Increase sleep/retry values in the Jenkinsfile |

### High memory / disk usage

```bash
# Prune Docker resources
docker system prune -af --volumes

# Check large log files
sudo find /var -name "*.log" -size +100M -exec ls -lh {} \;

# Rotate Docker logs (add to daemon.json)
# /etc/docker/daemon.json:
# {
#   "log-driver": "json-file",
#   "log-opts": { "max-size": "10m", "max-file": "3" }
# }
```

### Application throws 500 Internal Server Error

```bash
# Check Flask logs
docker compose logs -f web

# Enter the container for interactive debugging
docker compose exec web bash
python -c "from app import create_app; app = create_app(); print(app.config)"
```

---

## Quick Reference – Common Commands

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Rebuild and restart
docker compose up -d --build

# View real-time logs
docker compose logs -f

# Enter a container shell
docker compose exec web bash
docker compose exec db mysql -u root -p

# Check container resource usage
docker stats

# Restart a single service
docker compose restart web
```

---

## Architecture Diagram

```
┌─────────────┐     ┌─────────────────────────────────────────┐
│   Browser   │────▶│  Nginx (port 80/443)                    │
└─────────────┘     │  ┌──────────────┐  ┌─────────────────┐  │
                    │  │ /static/     │  │ / (proxy_pass)  │  │
                    │  │ served       │  │ → web:5000      │  │
                    │  │ directly     │  │                 │  │
                    │  └──────────────┘  └────────┬────────┘  │
                    └─────────────────────────────┼───────────┘
                                                  │
                    ┌─────────────────────────────▼───────────┐
                    │  Gunicorn + Flask (port 5000)            │
                    │  Workers: CPU × 2 + 1                    │
                    └──────────────────┬──────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────┐
                    │  MySQL 8.0 (port 3306)                   │
                    │  Database: library_db                     │
                    │  Volume: mysql_data                       │
                    └─────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Jenkins (port 8080)                                         │
│  Pipeline: Checkout → Test → Build → Deploy → Health Check   │
│  Trigger: GitHub webhook on push                             │
└──────────────────────────────────────────────────────────────┘
```

---

## AWS ECR & Jenkins Pipeline Integration

This section explains how to configure AWS and Jenkins to support the ECR container registry and remote EC2 deployments.

### 1. Create AWS ECR Repository
Log in to your AWS Console and navigate to **Elastic Container Registry (ECR)**:
1. Click **Create Repository**.
2. Select **Private**.
3. Name the repository: `library-management-system`.
4. Click **Create Repository**.

### 2. Configure AWS IAM User for Jenkins
In AWS Console, navigate to **IAM (Identity and Access Management)**:
1. Create a new IAM User (e.g., `jenkins-deployer`).
2. Attach the **AmazonEC2ContainerRegistryPowerUser** policy directly to allow the user to read and write images to ECR.
3. Generate an **Access Key ID** and **Secret Access Key** under the user's Security Credentials tab.

### 3. Store Credentials in Jenkins Credentials Manager
Navigate to your **Jenkins Dashboard → Manage Jenkins → Credentials → System → Global credentials**:

#### 3.1 AWS Credentials
* **Kind**: AWS Credentials (or two standard Secret Text credentials if the AWS credentials plugin is not installed)
* **ID**: `aws-credentials`
* **Access Key ID**: `YOUR_AWS_ACCESS_KEY_ID`
* **Secret Access Key**: `YOUR_AWS_SECRET_ACCESS_KEY`

#### 3.2 EC2 SSH Credentials
* **Kind**: SSH Username with private key
* **ID**: `ec2-ssh-key`
* **Username**: `ubuntu`
* **Private Key**: Paste the contents of your `.pem` key pair file used to launch the EC2 instance.

### 4. Deploying to EC2 Host
1. Make sure your EC2 Instance has Docker and Git installed.
2. In the Jenkins Pipeline Job settings, add an environment variable `EC2_IP` containing the Elastic IP of your EC2 instance.
3. When you push to the `main` branch, the pipeline will build the image, push it to AWS ECR, SSH into your EC2 host, and start the services using `docker-compose.prod.yml`.

---

## Security Checklist

- [ ] Change default `SECRET_KEY` in `.env`
- [ ] Use strong MySQL passwords
- [ ] Restrict SSH to your IP only
- [ ] Enable UFW firewall
- [ ] Set up SSL/TLS with Let's Encrypt
- [ ] Restrict Jenkins (port 8080) to your IP
- [ ] Enable Docker log rotation
- [ ] Set up automated database backups
- [ ] Keep system packages updated (`unattended-upgrades`)
- [ ] Review Nginx security headers

---

*End of deployment guide.*

