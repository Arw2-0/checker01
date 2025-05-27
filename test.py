import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# Set up the webhook URLs (keep them as environment variables)
os.environ["DISCORD_FINAL_WEBHOOK_URL"] = "https://discord.com/api/webhooks/1376640623297433671/s_W7LeSd-v9B-FWVD5GEHUArryJUy24T0ZCg4buAv3DbuQo60Rd7Ss9wks_osEzd8gO1"
os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/1373286716504277002/3a8I20YEVadrZXGK_W3AcPB4v01d5walWIIySGwl6Xf-rdnpTm52XKNE3sr7HmfOY6OF"

# Define your list of proxies (replace with your actual proxies)
proxies_list = [
    "https://34.102.48.89:8080",
    "https://200.174.198.86:8888",
    "https://45.12.150.82:8080",
    "https://47.236.224.32:8080",
    "https://45.140.143.77:18080"
]

def get_random_proxy():
    """Return a random proxy from the list."""
    return {"http": random.choice(proxies_list), "https": random.choice(proxies_list)}

def read_usernames_from_file(filename):
    usernames = []
    with open(filename, "r", encoding="utf-8") as f:
        usernames = [line.strip() for line in f if line.strip()]
    return usernames

def check_username(username):
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={username}"
    try:
        proxy = get_random_proxy()  # Get a random proxy
        response = requests.get(url, proxies=proxy, timeout=5)
        if response.status_code == 500:
            print(f"Server error while checking {username}, assuming name is free.")
            return username  # Free name found
    except requests.RequestException as e:
        print(f"Error checking {username}: {e}")
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
    input_file = "99.txt"  # Change this to your txt filename
    all_usernames = read_usernames_from_file(input_file)
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    batch_size = 99
    total = len(all_usernames)
    all_free_names = []

    for batch_num, start_idx in enumerate(range(0, total, batch_size), start=1):
        batch_usernames = all_usernames[start_idx:start_idx + batch_size]
        print(f"\nProcessing batch {batch_num} with {len(batch_usernames)} usernames...")
        
        free_names = check_usernames_concurrently(batch_usernames)
        if free_names:
            all_free_names.extend(free_names)

        send_discord_notification(free_names, webhook_url, batch_num)

        # If not the last batch, wait 1 minute before next batch
        if start_idx + batch_size < total:
            print("Waiting 1 minute before next batch to avoid hitting API rate limits...\n")
            time.sleep(60)

    print("\n=== All batches processed ===")
    print(f"Total free usernames found: {len(all_free_names)}")
    if all_free_names:
        print("All free usernames:")
        for name in all_free_names:
            print(f"- {name}")

if __name__ == "__main__":
    main()
