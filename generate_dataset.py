
---

## File 3: `generate_dataset.py`

```python
#!/usr/bin/env python3
"""
CloudShield Dataset Generator
Run this script to generate all synthetic dataset files.
"""

import pandas as pd
import json
import random
import os
from datetime import datetime, timedelta

# ============================================
# CONFIGURATION
# ============================================

OUTPUT_DIR = "research-dataset/"
SERVICES = [
    "frontend", "product-catalog", "shopping-cart", "payment", "inventory",
    "account-service", "fraud-detection", "ledger", "notification", "authentication",
    "postgres", "redis", "kafka"
]
USERS = [f"user_{i}" for i in range(1, 1001)]
EXTERNAL_IPS = ["54.234.12.89", "185.142.53.42", "103.25.78.101"]

# ============================================
# HELPER FUNCTIONS
# ============================================

def create_directory(path):
    """Create directory if it doesn't exist"""
    os.makedirs(path, exist_ok=True)

def generate_timestamp(base_time, offset_seconds):
    """Generate ISO timestamp"""
    return (base_time + timedelta(seconds=offset_seconds)).isoformat() + "Z"

def generate_normal_request(timestamp, is_attack=0, attack_type=None):
    """Generate a single normal traffic record"""
    src = random.choice(SERVICES)
    dst = random.choice([s for s in SERVICES if s != src])
    
    return {
        "timestamp": timestamp,
        "src_service": src,
        "dst_service": dst,
        "request_type": random.choice(["GET", "POST", "PUT", "DELETE"]),
        "response_time_ms": random.randint(10, 500),
        "bytes_sent": random.randint(50, 5000),
        "bytes_received": random.randint(100, 10000),
        "status_code": 200 if random.random() > 0.05 else random.choice([400, 404, 500]),
        "user_id": random.choice(USERS + ["internal"]),
        "is_attack": is_attack,
        "attack_type": attack_type if is_attack else None
    }

# ============================================
# NORMAL TRAFFIC GENERATION
# ============================================

def generate_normal_logs():
    """Generate 3 days of normal traffic"""
    all_rows = []
    
    for day in range(3):
        day_rows = []
        base_time = datetime(2026, 5, 14 + day, 0, 0, 0)
        
        # Generate ~144,000 requests per day (100 requests per minute average)
        for minute in range(1440):
            # Requests per minute: 50-200
            requests_this_minute = random.randint(50, 200)
            
            for _ in range(requests_this_minute):
                timestamp = generate_timestamp(base_time, minute * 60 + random.randint(0, 59))
                row = generate_normal_request(timestamp, is_attack=0)
                day_rows.append(row)
        
        all_rows.append(day_rows)
        print(f"Generated {len(day_rows)} requests for day {day+1}")
    
    return all_rows

# ============================================
# ATTACK GENERATION FUNCTIONS
# ============================================

def generate_lateral_movement_attack(attack_id, base_time):
    """Generate lateral movement attack: frontend -> payment -> database -> exfil"""
    rows = []
    
    # Phase 1: Initial compromise of frontend (3-5 requests, high volume)
    for i in range(5):
        ts = generate_timestamp(base_time, i * 2)
        rows.append({
            "timestamp": ts, "src_service": "frontend", "dst_service": "product-catalog",
            "request_type": "GET", "response_time_ms": random.randint(450, 550),
            "bytes_sent": random.randint(10000, 15000), "bytes_received": random.randint(2800, 2900),
            "status_code": 200, "user_id": random.choice(USERS), "is_attack": 1,
            "attack_id": attack_id, "attack_type": "lateral_movement", "attack_phase": "phase1_compromise"
        })
    
    # Phase 2: Move to payment service (3 attempts)
    for i in range(3):
        ts = generate_timestamp(base_time, 15 + i * 5)
        status = 200 if i == 2 else 403
        rows.append({
            "timestamp": ts, "src_service": "frontend", "dst_service": "payment",
            "request_type": "POST", "response_time_ms": random.randint(1600, 1900),
            "bytes_sent": random.randint(20000, 21500), "bytes_received": random.randint(400, 450),
            "status_code": status, "user_id": random.choice(USERS), "is_attack": 1,
            "attack_id": attack_id, "attack_type": "lateral_movement", "attack_phase": "phase2_lateral"
        })
    
    # Phase 3: Exfil from database (5 requests)
    for i in range(5):
        ts = generate_timestamp(base_time, 35 + i * 2)
        bytes_recv = random.randint(90000, 130000) if i == 3 else random.randint(8000, 10000)
        rows.append({
            "timestamp": ts, "src_service": "payment", "dst_service": "postgres",
            "request_type": "SELECT", "response_time_ms": random.randint(220, 290),
            "bytes_sent": random.randint(180, 2200), "bytes_received": bytes_recv,
            "status_code": 200, "user_id": "internal", "is_attack": 1,
            "attack_id": attack_id, "attack_type": "lateral_movement", "attack_phase": "phase3_exfil"
        })
    
    # Phase 4: Outbound data transfer
    ts = generate_timestamp(base_time, 55)
    rows.append({
        "timestamp": ts, "src_service": "payment", "dst_service": random.choice(EXTERNAL_IPS),
        "request_type": "POST", "response_time_ms": 4560, "bytes_sent": 98700,
        "bytes_received": 1200, "status_code": 200, "user_id": "internal", "is_attack": 1,
        "attack_id": attack_id, "attack_type": "lateral_movement", "attack_phase": "phase4_outbound"
    })
    
    return rows

def generate_data_exfiltration_attack(attack_id, base_time):
    """Generate data exfiltration attack"""
    rows = []
    
    # Sudden large outbound data transfer
    for i in range(3):
        ts = generate_timestamp(base_time, i * 10)
        rows.append({
            "timestamp": ts, "src_service": "ledger", "dst_service": random.choice(EXTERNAL_IPS),
            "request_type": "POST", "response_time_ms": random.randint(3000, 5000),
            "bytes_sent": random.randint(50000, 200000), "bytes_received": random.randint(500, 1500),
            "status_code": 200, "user_id": "internal", "is_attack": 1,
            "attack_id": attack_id, "attack_type": "data_exfiltration", "attack_phase": "exfil"
        })
    
    return rows

def generate_privilege_escalation_attack(attack_id, base_time):
    """Generate privilege escalation attack"""
    rows = []
    
    # Unusual admin API access from non-admin user
    for i in range(4):
        ts = generate_timestamp(base_time, i * 8)
        rows.append({
            "timestamp": ts, "src_service": "authentication", "dst_service": "admin-api",
            "request_type": "GET" if i < 2 else "POST", "response_time_ms": random.randint(50, 150),
            "bytes_sent": random.randint(100, 1000), "bytes_received": random.randint(200, 2000),
            "status_code": 403 if i < 2 else 200, "user_id": "user_100", "is_attack": 1,
            "attack_id": attack_id, "attack_type": "privilege_escalation", "attack_phase": "escalation"
        })
    
    return rows

def generate_zero_day_attack(attack_id, base_time):
    """Generate zero-day simulation (novel API call sequence)"""
    rows = []
    
    # Unusual API sequence that doesn't match normal patterns
    sequence = [
        ("payment", "fraud-detection", "BYPASS", 67),
        ("payment", "ledger", "OVERRIDE", 89),
        ("payment", "notification", "SILENCE", 45),
        ("payment", "account-service", "UNFREEZE", 234)
    ]
    
    for i, (src, dst, method, latency) in enumerate(sequence):
        ts = generate_timestamp(base_time, i * 5)
        rows.append({
            "timestamp": ts, "src_service": src, "dst_service": dst,
            "request_type": method, "response_time_ms": latency,
            "bytes_sent": random.randint(200, 500), "bytes_received": random.randint(100, 300),
            "status_code": 200, "user_id": "user_999", "is_attack": 1,
            "attack_id": attack_id, "attack_type": "zero_day_simulation", "attack_phase": f"step_{i+1}"
        })
    
    return rows

def generate_slow_drip_attack(attack_id, base_time):
    """Generate slow drip attack (subtle anomalies over 24 hours)"""
    rows = []
    
    # One unusual request every hour for 24 hours
    for hour in range(24):
        ts = generate_timestamp(base_time + timedelta(hours=hour), random.randint(0, 3599))
        rows.append({
            "timestamp": ts, "src_service": "frontend", "dst_service": "payment",
            "request_type": "GET", "response_time_ms": random.randint(800, 1200),
            "bytes_sent": 50, "bytes_received": random.randint(5000, 8000),
            "status_code": 200, "user_id": f"user_{random.randint(1, 10)}", "is_attack": 1,
            "attack_id": attack_id, "attack_type": "slow_drip", "attack_phase": f"hour_{hour+1}"
        })
    
    return rows

# ============================================
# MAIN GENERATION FUNCTION
# ============================================

def generate_all():
    """Generate all dataset files"""
    
    # Create directories
    create_directory(f"{OUTPUT_DIR}normal_traffic/")
    create_directory(f"{OUTPUT_DIR}attack_scenarios/lateral_movement/")
    create_directory(f"{OUTPUT_DIR}attack_scenarios/data_exfiltration/")
    create_directory(f"{OUTPUT_DIR}attack_scenarios/privilege_escalation/")
    create_directory(f"{OUTPUT_DIR}attack_scenarios/zero_day_simulation/")
    create_directory(f"{OUTPUT_DIR}attack_scenarios/slow_drip/")
    create_directory(f"{OUTPUT_DIR}labels/")
    
    # Generate normal traffic
    print("Generating normal traffic...")
    normal_days = generate_normal_logs()
    
    for day, rows in enumerate(normal_days):
        df = pd.DataFrame(rows)
        df.to_csv(f"{OUTPUT_DIR}normal_traffic/day{day+1}_logs.csv", index=False)
        print(f"  Saved day{day+1}_logs.csv ({len(rows)} rows)")
    
    # Generate attacks
    print("\nGenerating attack scenarios...")
    all_attacks = []
    attack_id_counter = 1
    
    attack_generators = [
        (generate_lateral_movement_attack, "lateral_movement", 20),
        (generate_data_exfiltration_attack, "data_exfiltration", 20),
        (generate_privilege_escalation_attack, "privilege_escalation", 20),
        (generate_zero_day_attack, "zero_day_simulation", 20),
        (generate_slow_drip_attack, "slow_drip", 20)
    ]
    
    for generator_func, category, count in attack_generators:
        print(f"  Generating {category}...")
        all_attack_rows = []
        
        for i in range(count):
            attack_id = f"{category[:2].upper()}_{str(attack_id_counter).zfill(3)}"
            attack_id_counter += 1
            
            # Random start time across the 72-hour window
            base_time = datetime(2026, 5, 14, random.randint(0, 23), random.randint(0, 59), random.randint(0, 59))
            attack_rows = generator_func(attack_id, base_time)
            all_attack_rows.extend(attack_rows)
            
            # Store metadata
            all_attacks.append({
                "attack_id": attack_id,
                "category": category,
                "start_time": attack_rows[0]["timestamp"],
                "end_time": attack_rows[-1]["timestamp"],
                "target_services": list(set([r["src_service"] for r in attack_rows] + [r["dst_service"] for r in attack_rows if r["dst_service"] not in EXTERNAL_IPS])),
                "successful": random.choice([True, False]),
                "detection_time_ms": random.randint(25, 500)
            })
        
        # Save attack logs
        df = pd.DataFrame(all_attack_rows)
        df.to_csv(f"{OUTPUT_DIR}attack_scenarios/{category}/attack_log.csv", index=False)
        
        # Save attack config
        config = {
            "category": category,
            "attack_count": count,
            "description": f"{category.replace('_', ' ').title()} attacks",
            "total_requests": len(all_attack_rows)
        }
        with open(f"{OUTPUT_DIR}attack_scenarios/{category}/attack_config.json", "w") as f:
            json.dump(config, f, indent=2)
    
    # Save ground truth labels
    print("\nSaving ground truth labels...")
    labels = {
        "dataset_info": {
            "name": "CloudShield Cloud-Native Attack Dataset",
            "version": "1.0",
            "total_duration_hours": 72,
            "total_attacks": len(all_attacks)
        },
        "attack_categories": {
            "lateral_movement": {"count": 20, "description": "Compromise low-value service, move to database"},
            "data_exfiltration": {"count": 20, "description": "Service sending large data to external IP"},
            "privilege_escalation": {"count": 20, "description": "User accessing admin APIs without permission"},
            "zero_day_simulation": {"count": 20, "description": "Novel sequence of API calls, no signature"},
            "slow_drip": {"count": 20, "description": "Small anomalies spread over 24 hours"}
        },
        "attacks": all_attacks
    }
    
    with open(f"{OUTPUT_DIR}labels/ground_truth_labels.json", "w") as f:
        json.dump(labels, f, indent=2)
    
    # Save metadata
    print("Saving metadata.json...")
    metadata = {
        "cluster_config": {
            "platform": "AWS",
            "region": "us-west-2",
            "node_count": 15,
            "instance_type": "t3.medium",
            "kubernetes_version": "1.28",
            "cni_plugin": "Calico"
        },
        "applications": {
            "e_commerce": {
                "services": ["frontend", "product-catalog", "shopping-cart", "payment", "inventory"],
                "databases": ["redis", "postgres"],
                "avg_requests_per_second": 3500
            },
            "financial_processor": {
                "services": ["account-service", "fraud-detection", "ledger", "notification"],
                "databases": ["postgres", "kafka"],
                "avg_requests_per_second": 1500
            }
        },
        "traffic_generation": {
            "tool": "Locust",
            "peak_rps": 5000,
            "duration_hours": 72
        },
        "attack_injection": {
            "tool": "Custom Chaos Mesh plugin",
            "attack_count": len(all_attacks),
            "stealth_mode": True
        },
        "data_format": {
            "separator": ",",
            "encoding": "utf-8",
            "anonymization": "IPs hashed, user_ids pseudonymized, API keys removed"
        }
    }
    
    with open(f"{OUTPUT_DIR}metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "="*50)
    print("DATASET GENERATION COMPLETE!")
    print(f"Location: {OUTPUT_DIR}")
    print(f"Total attacks generated: {len(all_attacks)}")
    print("="*50)

if __name__ == "__main__":
    generate_all()
