# aws-usage-report
aws netapp (storage gride) get usage report total size (object , versioning , delete marker)
!! unit binary -> SI 
A Python CLI tool for analyzing S3 bucket storage usage across multiple tenants and zones. It supports directory-level scanning, total file/object counting, cache control, and Discord notification.

---

## 🗂️ Project Structure

```
aws-usage-report.py      # Main Python script
.env.example              # Sample environment file
requirements.txt          # Python dependencies
README.md                 # This file
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

## 📦 Installation

- [optional] created env
```bash
python3 -m venv .venv  
```bash

```bash
source .venv/bin/activate  & deactivate
```

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Configuration (`.env`)

Create a `.env` file based on the following example:

```env
S3_ENDPOINT_URL=https://your-s3-endpoint.com
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

S3_PRO_TENANT1_ACCESS_KEY=...
S3_PRO_TENANT1_SECRET_KEY=...
S3_UAT_TENANT1_ACCESS_KEY=...
S3_UAT_TENANT1_SECRET_KEY=...
S3_DEV_TENANT1_ACCESS_KEY=...
S3_DEV_TENANT1_SECRET_KEY=...
```

---

## 🚀 Usage

### Interactive Mode

```bash
python s3_usage_report.py
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
python aws-usage-report.py--all --all-buckets --no-cache
```

| Flag             | Description                                              |
|------------------|----------------------------------------------------------|
| `--all`          | Scan all directories within selected buckets             |
| `--all-buckets`  | Scan all available buckets under the selected tenant     |
| `--no-cache`     | Disable caching for this run                             |

---

## 📤 Discord Output Example

```text
📦 Bucket: bucket-dump
Directory: app-name
  Files: 120
  Total size: 520.11 MB (520110000 Bytes)
  Total objects: 120

Total size: 520.11 MB (520110000 Bytes)
Total Files: 120
Total objects: 120

S3 PRO_TENANT1 total usage = 1.75 GB (1750000000 Bytes)
```
```
python3 aws-usage-report.py --all-bucket --no-cache

S3 Bucket Directory Size Report - PRO_TENANT1

total buckets: 6
Total Files: 687
Total objects: 687
Total size: 906.49 MB (906487833 Bytes)

report aws-usage-report.py | Time Duration: 00:00:04.182873
```

---

