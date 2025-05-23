import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def read_usernames_from_file(filename):
    usernames = []
    with open(filename, "r", encoding="utf-8") as f:
        usernames = [line.strip() for line in f if line.strip()]
    return usernames

def check_username(username):
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={username}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 500:
            return username  # Free name found
    except requests.RequestException:
        pass
    return None

def check_usernames_concurrently(usernames, max_workers=10):
    total = len(usernames)
    free_names = []

    print(f"Checking {total} usernames with {max_workers} threads...\n")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_username = {executor.submit(check_username, name): name for name in usernames}

        for i, future in enumerate(as_completed(future_to_username), start=1):
            username = future_to_username[future]
            progress = (i / total) * 100
            print(f"[{i}/{total}] ({progress:.2f}%) Checked: {username}", end='\r')

            result = future.result()
            if result:
                free_names.append(result)

    print()
    return free_names

def send_discord_notification(free_names, webhook_url, batch_number):
    if not free_names or not webhook_url:
        return

    message = f"**🚨 @everyone Free Usernames Found (Batch {batch_number})!**\n" + "\n".join(f"- `{name}`" for name in free_names)
    payload = {"content": message}

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print(f"Discord notification for batch {batch_number} sent successfully.")
        else:
            print(f"Failed to send Discord notification for batch {batch_number}: HTTP {response.status_code}")
    except requests.RequestException as e:
        print(f"Error sending Discord notification for batch {batch_number}: {e}")

def main():
    input_file = "chcene.txt"  # <--- Change this to your txt filename
    all_usernames = read_usernames_from_file(input_file)
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    batch_size = 600
    total = len(all_usernames)
    all_free_names = []

    for batch_num, start_idx in enumerate(range(0, total, batch_size  ), start=1):
        batch_usernames = all_usernames[start_idx:start_idx + batch_size]
        print(f"\nProcessing batch {batch_num} with {len(batch_usernames)} usernames...")

        free_names = check_usernames_concurrently(batch_usernames)
        if free_names:
            all_free_names.extend(free_names)

        send_discord_notification(free_names, webhook_url, batch_num)

        # If not the last batch, wait 2 minutes before next batch
        if start_idx + batch_size < total:
            print("Waiting 2 minutes before next batch to avoid hitting API rate limits...\n")
            time.sleep(300)

    print("\n=== All batches processed ===")
    print(f"Total free usernames found: {len(all_free_names)}")
    if all_free_names:
        print("All free usernames:")
        for name in all_free_names:
            print(f"- {name}")

if __name__ == "__main__":
    main()
