import boto3
import requests
import os
import pickle
from dotenv import load_dotenv
import time
import argparse
from datetime import datetime, timezone
import pytz
from concurrent.futures import ThreadPoolExecutor

# --- Load from .env ---
load_dotenv()
webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
s3_endpoint = os.getenv("S3_ENDPOINT_URL")

def print_to_console(message):
    print(message)

def send_to_discord_webhook(content, tenant_label, duration=None):
    if not webhook_url:
        print("Webhook URL not set.")
        return
    embed = {
        "title": f"S3 Bucket & Directory Size Report - {tenant_label}",
        "description": content,
        "color": 3066993, #green
        "footer": {"text": f"report {os.path.basename(__file__)} | Time Duration: {duration}"},
        "timestamp": datetime.now(pytz.timezone("Asia/Bangkok")).isoformat()
    }
    data = {"embeds": [embed]}
    try:
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()
        print("Successfully sent to Discord webhook.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send webhook: {e}")

## Prompt user for valid input with optional multi-select
def get_valid_input(prompt, valid_options, allow_multiple=False):
    while True:
        user_input = input(prompt).strip().lower()
        if user_input == 'b':
            return 'back'
        if allow_multiple:
            parts = [p.strip() for p in user_input.split(',') if p.strip()]
            if user_input == '.' or all(p in valid_options for p in parts):
                return user_input
        elif user_input == '.' or user_input in valid_options:
            return user_input
        print("Invalid input. Try again or type 'b' to go back.")

def setup_s3_client(zone_env, tenant_number):
    access_key = os.getenv(f"S3_{zone_env}_TENANT{tenant_number}_ACCESS_KEY")
    secret_key = os.getenv(f"S3_{zone_env}_TENANT{tenant_number}_SECRET_KEY")
    print("[DEBUG] Loaded credentials")
    return boto3.client(
        's3',
        endpoint_url=s3_endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )

# Generator that yields objects  bucket
def get_bucket_objects(s3_client, bucket_name):
    paginator = s3_client.get_paginator('list_object_versions')
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get('Versions', []):
            yield obj
        for marker in page.get('DeleteMarkers', []):
            yield marker

## List top-level directories from S3 keys
def list_directories(objects):
    directories = set()
    for obj in objects:
        parts = obj['Key'].split('/')
        if len(parts) > 1:
            directories.add(parts[0])
    return sorted(directories)

# Calculate total size and object count for selected directories

def calculate_directory_sizes(objects, selected_dirs):
    result = {d: {'count': 0, 'size': 0} for d in selected_dirs}
    for obj in objects:
        parts = obj['Key'].split('/')
        if len(parts) > 1:
            directory = parts[0]
            if directory in result:
                result[directory]['count'] += 1
                result[directory]['size'] += obj.get('Size', 0)
    return result

# # Convert byte size 
def format_size(size):
    kb = size / 1000
    mb = kb / 1000
    gb = mb / 1000
    tb = gb / 1000
    if tb >= 1:
        return f"{tb:.2f} TB"
    elif gb >= 1:
        return f"{gb:.2f} GB"
    elif mb >= 1:
        return f"{mb:.2f} MB"
    elif kb >= 1:
        return f"{kb:.2f} KB"
    return f"{size} Bytes"

# binaary to si human read units
def parse_human_size(size_str):
    size_str = size_str.strip().upper()
    if size_str.endswith("TB"):
        return int(float(size_str.replace("TB", "").strip()) * 1_000_000_000_000)
    elif size_str.endswith("GB"):
        return int(float(size_str.replace("GB", "").strip()) * 1_000_000_000)
    elif size_str.endswith("MB"):
        return int(float(size_str.replace("MB", "").strip()) * 1_000_000)
    elif size_str.endswith("KB"):
        return int(float(size_str.replace("KB", "").strip()) * 1_000)
    else:
        return int(float(size_str))


#  Fetch and optionally cache S3 bucket objects dump pickle history cache
def fetch_objects_for_bucket(s3_client, bucket_name, cached_objects, cache_file, save_cache):
    if bucket_name in cached_objects:
        print(f"[bug CACHE] {bucket_name}")
        return bucket_name, cached_objects[bucket_name]
    else:
        all_objects = list(get_bucket_objects(s3_client, bucket_name))
        cached_objects[bucket_name] = all_objects
        if save_cache:
            with open(cache_file, "wb") as f:
                pickle.dump(cached_objects, f)
        print(f"[beg FETCHED] {bucket_name}")
        return bucket_name, all_objects

def main():
    parser = argparse.ArgumentParser(description="S3 Directory Size Reporter")
    parser.add_argument('--skip', action='store_true', help='Skip tenant selection and summarize entire tenant usage')
    parser.add_argument('--all', action='store_true', help='Calculate all directories in each bucket')
    parser.add_argument('--all-buckets', action='store_true', help='Calculate all buckets without prompting')
    parser.add_argument('--no-cache', action='store_true', help='Do not save fetched data to cache')
    args = parser.parse_args()

    while True:
        ans = input("Show total object count? (y / n): ").strip().lower()
        if ans in ['y', 'n']:
            show_total_objects = (ans == 'y')
            break
    while True:
        ans = input("Show total file count? (y / n): ").strip().lower()
        if ans in ['y', 'n']:
            show_total_files = (ans == 'y')
            break
    while True:
        ans = input("Send results to Discord? (y / n): ").strip().lower()
        if ans in ['y', 'n']:
            send_to_discord = (ans == 'y')
            break
    if args.no_cache:
        save_cache = False
    else:
        while True:
            cache_choice = input("Save results to cache? (y / n): ").strip().lower()
            if cache_choice in ['y', 'n']:
                break
        save_cache = (cache_choice == 'y')

    zone_envs = ["PRO", "UAT", "DEV"]
    all_tenants = []
    for zone in zone_envs:
        i = 1
        while True:
            ak = os.getenv(f"S3_{zone}_TENANT{i}_ACCESS_KEY")
            sk = os.getenv(f"S3_{zone}_TENANT{i}_SECRET_KEY")
            if ak and sk:
                label = f"{zone}_TENANT{i}"
                tenant_no = os.getenv(f"S3_{zone}_TENANT{i}_NO", "")
                all_tenants.append((zone, i, label, tenant_no))
                i += 1
            else:
                break

    if not all_tenants:
        print("❌ No tenants found in .env")
        return

    print("Select tenant:")
    for idx, (_, _, label, tenant_no) in enumerate(all_tenants, 1):
        print(f"{idx}. {label} ({tenant_no})")

    tenant_input = get_valid_input(f"Enter tenant number (1-{len(all_tenants)}): ", [str(i) for i in range(1, len(all_tenants)+1)])
    if tenant_input == 'back':
        return

    selected_zone, selected_tenant_num, tenant_label, tenant_no = all_tenants[int(tenant_input)-1]
    s3_client = setup_s3_client(selected_zone, selected_tenant_num)

    try:
        buckets = [b['Name'] for b in s3_client.list_buckets().get('Buckets', [])]
    except Exception as e:
        print(f"Error listing buckets: {e}")
        return

    cache_file = f"s3_cache_{tenant_label}.pkl"
    if os.path.exists(cache_file) and os.path.getsize(cache_file) > 0:
        with open(cache_file, "rb") as f:
            cached_objects = pickle.load(f)
            print("[debugg] Cache loaded")
    else:
        cached_objects = {}

    if args.all_buckets or args.skip:
        selected_buckets = buckets
    else:
        print("Available buckets:")
        for i, b in enumerate(buckets, 1):
            print(f"{i}. {b}")
        bucket_input = get_valid_input("Select bucket (1,2,.. or '.' for all, 'q' to quit): ",
            [str(i) for i in range(1, len(buckets)+1)] + ['q'], allow_multiple=True)
        if bucket_input == 'q':
            return
        selected_buckets = buckets if bucket_input == '.' else [
            buckets[int(i.strip()) - 1] for i in bucket_input.split(',') if i.strip().isdigit()
        ]

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(fetch_objects_for_bucket, s3_client, bucket, cached_objects, cache_file, save_cache)
            for bucket in selected_buckets
        ]
        results = [f.result() for f in futures]

    bucket_objects_map = dict(results)
    grand_total_usage = 0

    if args.all_buckets or args.skip:
        start_time = time.time()
        all_objects = []
        for bucket in selected_buckets:
            all_objects.extend(bucket_objects_map[bucket])
        directories = list_directories(all_objects)
        selected_dirs = directories
        sizes = calculate_directory_sizes(all_objects, selected_dirs)
        raw_total = sum(d['size'] for d in sizes.values())
        total_files = sum(d['count'] for d in sizes.values())
        grand_total_usage = raw_total

        # ตรวจสอบ quota และคำนวณพื้นที่ที่เหลือ ถ้ามี
        quota_str = os.getenv(f"S3_{selected_zone}_TENANT{selected_tenant_num}_QUOTA")

        summary_embed = [
            f"📦 Total Buckets: {len(selected_buckets)}"
        ]
        if show_total_files:
            summary_embed.append(f"📄 Total Files: {total_files}")
        if show_total_objects:
            summary_embed.append(f"🔢 Total Objects: {total_files}")

        if quota_str:
            try:
                quota = parse_human_size(quota_str)
                remaining = quota - grand_total_usage
                summary_embed.append(f"🧮 Total size: {format_size(raw_total)} ({raw_total} Bytes) / {format_size(quota)}")
                summary_embed.append(f"📉 Remaining Space: {format_size(remaining)}")
            except ValueError:
                summary_embed.append("⚠️ Invalid QUOTA value in .env")
        else:
            summary_embed.append(f"🧮 Total size: {format_size(raw_total)} ({raw_total} Bytes) / unlimited")

        output_text = "\n".join(summary_embed)
        print(output_text)

        if send_to_discord:
            duration = str(datetime.fromtimestamp(time.time() - start_time, tz=timezone.utc).time())
            send_to_discord_webhook(output_text, f"{tenant_label} #{tenant_no}", duration)
        return

    for bucket in selected_buckets:
        start_time = time.time()
        print(f"📦 Bucket: {bucket}")
        objects = bucket_objects_map[bucket]
        directories = list_directories(objects)
        if not directories:
            print("No directories found in this bucket")
            continue
        for idx, d in enumerate(directories, 1):
            print(f"{idx}. {d}")

        if args.all_buckets or args.all or args.skip:
            selected_dirs = directories
        else:
            dir_input = get_valid_input("Select directories (1,2,.. or '.' for all, 'b' to go back): ",
                [str(i) for i in range(1, len(directories)+1)] + ['b'], allow_multiple=True)
            if dir_input == 'back':
                continue
            selected_dirs = directories if dir_input == '.' else [
                directories[int(i.strip()) - 1] for i in dir_input.split(',') if i.strip().isdigit()
            ]
            if not selected_dirs:
                print("No valid directories selected")
                continue

        sizes = calculate_directory_sizes(objects, selected_dirs)
        raw_total = sum(d['size'] for d in sizes.values())
        if args.all_buckets:
            grand_total_usage += raw_total
        total_files = sum(d['count'] for d in sizes.values())

        output_lines = [f"📦 Bucket: {bucket}"]
        for d, info in sizes.items():
            output_lines.append(f"Directory: {d}")
            if show_total_files:
                output_lines.append(f"  Files: {info['count']}")
            output_lines.append(f"  Total size: {format_size(info['size'])} ({info['size']} Bytes)")
            if show_total_objects:
                output_lines.append(f"  Total objects: {info['count']}")

        output_lines.append(f"Total size: {format_size(raw_total)} ({raw_total} Bytes)")
        if show_total_files:
            output_lines.append(f"Total Files: {total_files}")
        if show_total_objects:
            output_lines.append(f"Total objects: {total_files}")

        output_text = "\n".join(output_lines)
        print(output_text)

        if send_to_discord:
            duration = str(datetime.fromtimestamp(time.time() - start_time, tz=timezone.utc).time())
            send_to_discord_webhook(output_text, f"{tenant_label} #{tenant_no}", duration)

        if args.all_buckets or args.skip:
            summary_text = f"S3 {tenant_label} total usage = {format_size(grand_total_usage)} ({grand_total_usage} Bytes)"
            print(summary_text)
            
            if send_to_discord:
                summary_embed = [
                    f"📦 Total Buckets: {len(selected_buckets)}"
                ]
                if show_total_files:
                    summary_embed.append(f"📄 Total Files: {total_files}")
                if show_total_objects:
                    summary_embed.append(f"🔢 Total Objects: {total_files}")
                summary_embed.append(f"🧮 Total Size: {format_size(grand_total_usage)} ({grand_total_usage} Bytes)")
                embed_text = "\n".join(summary_embed)
                duration = str(datetime.fromtimestamp(time.time() - start_time, tz=timezone.utc).time())
                send_to_discord_webhook(embed_text, f"{tenant_label} #{tenant_no}", duration)

if __name__ == "__main__":
    main()