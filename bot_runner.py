import os
import sys
import subprocess
import time

def log(message):
    """Prints a message with a timestamp."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)

if __name__ == "__main__":
    log("Bot Runner Initializing on Free Tier...")

    # This variable will be set in the Render Dashboard by the Admin
    bot_to_run = os.getenv("BOT_TO_RUN")

    if not bot_to_run:
        log("FATAL: 'BOT_TO_RUN' environment variable is not set. Worker will not start.")
        log("Please set it in the Render dashboard to the name of a folder in /bots (e.g., 'client_a').")
        sys.exit(1)

    log(f"Target bot selected: {bot_to_run}")

    bot_folder = os.path.join("bots", bot_to_run)
    bot_script_path = os.path.join(bot_folder, "bot.py")
    requirements_path = os.path.join(bot_folder, "requirements.txt")

    if not os.path.isdir(bot_folder) or not os.path.exists(bot_script_path):
        log(f"FATAL: Bot folder '{bot_folder}' or script '{bot_script_path}' not found.")
        sys.exit(1)

    # Step 1: Install client's dependencies
    if os.path.exists(requirements_path):
        log(f"Installing dependencies from {requirements_path}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", requirements_path],
                check=True, capture_output=True, text=True
            )
            log("Dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            log(f"--- PIP INSTALL FAILED ---\n{e.stderr}\n--------------------------")
            sys.exit(1)

    # Step 2: Run the client's bot script
    log(f"Starting bot script: {bot_script_path}")
    os.chdir(bot_folder) # Change directory so the bot can find its database file
    subprocess.run([sys.executable, "bot.py"])

    log("Bot Runner Finished.")