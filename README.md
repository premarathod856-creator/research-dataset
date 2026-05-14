
# CloudShield Research Dataset

This dataset accompanies the thesis: **"CloudShield: AI-Native Security for Public Cloud Applications"**

## Dataset Overview

| Property | Value |
|----------|-------|
| Duration | 72 hours |
| Environment | Kubernetes (15 nodes, t3.medium) |
| Applications | E-commerce + Financial transaction processor |
| Traffic volume | ~5,000 requests/second (peak) |
| Compressed size | ~4.2 GB |

## Attack Categories

| Category | Count | Description |
|----------|-------|-------------|
| Lateral movement | 20 | Compromise low-value service, move to database |
| Data exfiltration | 20 | Service sending large data to external IP |
| Privilege escalation | 20 | User accessing admin APIs without permission |
| Zero-day simulation | 20 | Novel sequence of API calls, no signature |
| Slow drip | 20 | Small anomalies spread over 24 hours |

## File Structure
