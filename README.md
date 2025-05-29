# aws-usage-report
aws netapp (storage gride) get usage report total size (object , versioning , delete marker)
!! unit binary -> SI 
A Python CLI tool for analyzing S3 bucket storage usage across multiple tenants and zones. It supports directory-level scanning, total file/object counting, cache control, and Discord notification.

---

## 🗂️ Project Structure

```
s3_usage_report.py       # get paginator list_object (versioning & Deletemarker) buckets and directory size usage
s3-tenants-report.py    # get paginator list_object (versioning & Deletemarker) size usage of tenants
.env                    # environment file
requirements.txt          # Python dependencies
s3_cache_*.pkl            # (Auto-created) Cache files per tenant
```
---

## 🔧 Features

- ✅ Multi-tenant / multi-zone (PRO, UAT, DEV)
- ✅ Per-directory size reporting and filtering
- ✅ Total file and object counting
- ✅ Select specific or all buckets/directories
- ✅ Summarize file/object count and total size
- ✅ Discord webhook output with detailed embeds
- ✅ Cache support with hybrid CLI/interactive control
- ✅ CLI automation support (`--all`, `--all-buckets`, `--no-cache`)

---

## 📂 Script Overview

### 1. `s3-usage-report.py` (Hybrid CLI)
- Interactive CLI prompts:
  - Show total object count?
  - Show total file count?
  - Save results to cache?  (cached_objects form pickle.dump)
  - Send results to Discord?
- Supports non-interactive CLI use `--skip`, `--all`, `--tenants` (bug), and `--no-cache`
- Useful for flexible manual exploration

### 2. `s3_usage_report_commented.py` (CLI Overall Ternans usage )
- Non-interactive, CLI-controlled
- Automatically sends reports to Discord
- Simplified logic for automated or scheduled runs

---

## ⚙️ CLI Usage

### Hybrid CLI:
```bash
python3 s3-usage-report-v3.py --tenants 5 --skip --no-cache
```

### CLI Overall tenants usages:
```bash
python3 s3_usage_report_commented.py --tenants 5,6 --no-cache

```
---

### CLI Arguments Explained:

| Argument        | Description                                         |
|-----------------|-----------------------------------------------------|
| `--tenants`     | Comma , tenant numbers e.g. 1,2,3 (CLI tenants)     |
| `--skip`        | Skip manual selection (Hybrid only)                |
| `--no-cache`    | Do not use or save cached S3 object metadata       |
| `--all`         | Calculate all directories (Hybrid only)            |
| `--all-buckets` | Process all buckets (Hybrid only)                  |

---

## 🛠 Python Environment Setup

You can create and manage a virtual Python environment with the following steps:

```bash
# Step 1: Create a virtual environment
python3 -m venv .venv

# Step 2: Activate the environment
source .venv/bin/activate   # On Windows use: .venv\Scripts\activate

# Step 3: Install required packages
pip install -r requirements.txt

# Step 4: Create a .env file with your credentials and settings

# Step 5: Run the script
python3 s3_usage_report_commented.py --tenants 5,6 --no-cache

# Step 6: Deactivate the environment when done
deactivate
```

> Ensure you have Python 3.7+ installed and that `pip`, `boto3`, `requests`, `python-dotenv`, and `pytz` are listed in your `requirements.txt`.

## 📝 Requirements (requirements.txt)

```txt
boto3
requests
python-dotenv
pytz
```

---

## 🔐 Environment Configuration (`.env`)

Create a `.env` file with the following format:

```dotenv
# s3 endpoit
S3_ENDPOINT_URL=https://endpoint:port/

# Chanel : s3-report
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Production
# no = number endpoint
S3_PRO_TENANT1_NO=
S3_PRO_TENANT1_QUOTA=105.00 TB
S3_PRO_TENANT1_ACCESS_KEY=
S3_PRO_TENANT1_SECRET_KEY=
# Maria-Backup
S3_PRO_TENANT2_NO=
S3_PRO_TENANT2_QUOTA=10.00 TB
S3_PRO_TENANT2_ACCESS_KEY=
S3_PRO_TENANT2_SECRET_KEY=

# UAT
# no = number endpoint
S3_UAT_TENANT1_NO=
S3_UAT_TENANT1_QUOTA=20.00 TB
S3_UAT_TENANT1_ACCESS_KEY=
S3_UAT_TENANT1_SECRET_KEY=

S3_UAT_TENANT2_NO=
S3_UAT_TENANT2_QUOTA=2.00 TB
S3_UAT_TENANT2_ACCESS_KEY=
S3_UAT_TENANT2_SECRET_KEY=

S3_UAT_TENANT3_NO=
S3_UAT_TENANT3_QUOTA=2.00 TB
S3_UAT_TENANT3_ACCESS_KEY=
S3_UAT_TENANT3_SECRET_KEY=

S3_UAT_TENANT4_NO=
S3_UAT_TENANT4_QUOTA=2.00 TB
S3_UAT_TENANT4_ACCESS_KEY=
S3_UAT_TENANT4_SECRET_KEY=

# Dev
S3_DEV_TENANT1_NO=
S3_DEV_TENANT1_QUOTA=5.00 TB
S3_DEV_TENANT1_ACCESS_KEY=
S3_DEV_TENANT1_SECRET_KEY=
```

---

## 📦 Output Example


### Interactive (Hybrid CLI)

```bash
python3 s3-usage-report.py
```

The script will prompt for:
- Show total object count? (y/n)
- Show total file count? (y/n)
- Send results to Discord? (y/n)
- Save results to cache? (y/n)
- Tenant, Bucket, and Directory selections

---

### CLI Automation

```bash
python3 s3-tenants-report.py --tenants 5,6 --no-cache 
```

---

## 📤 Discord Output Example

```bash
python3 s3-usage-report.py
```

```text
เหมาะสำหรับต้องการทราบเฉพาะ directory app_name นั้นๆ แทน ทั้งหมด

S3 Bucket & Directory Size Report - PRO_TENANT1 #900009
📦 Bucket: bucket-xx
Directory: xx
Total size: 189.92 MB (189922576 Bytes)
Total objects: 458
Directory: xx
Total size: 860.75 KB (860747 Bytes)
Total objects: 4
Directory: xx
Total size: 145.94 MB (145942927 Bytes)
Total objects: 355
Directory: xx
Total size: 183.98 KB (183979 Bytes)
Total objects: 4
Directory: xx
Total size: 203.58 MB (203583965 Bytes)
Total objects: 260
Total size: 540.49 MB (540494194 Bytes)
Total objects: 1081
report s3-usage-report.py | Time Duration: 00:00:03.938364 Today at xx:xx
```

```bash
python3 s3-usage-report.py --all --no-cache
Select bucket (1,2,.. or '.' for all, 'q' to quit): 994,995
```

```text
print  bucket & directory ของ bucket 994,995 ออกมาทั้งหมด เหมาะสำหรับใช้ดูภาพรวมdriectory ทั้งหมด ในแต่ buckets ที่เลือก
```

```bash
python3 python3 s3-tenants-report.py --tenants 5,6 --no-cache  
```

```text
print  bucket & directory ของ bucket 994,995 ออกมาทั้งหมด เหมาะสำหรับใช้ดูภาพรวมdriectory ทั้งหมด ในแต่ buckets ที่เลือก
```

---
