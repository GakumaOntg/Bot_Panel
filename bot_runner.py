import os
import sys
import subprocess
import time

def log(message):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)

if __name__ == "__main__":
    log("Bot Runner Initializing...")
    bot_to_run = os.getenv("BOT_TO_RUN")

    if not bot_to_run:
        log("FATAL: 'BOT_TO_RUN' environment variable is not set. Worker will not start.")
        sys.exit(1)

    log(f"Target bot selected: {bot_to_run}")

    bot_folder = os.path.join("bots", bot_to_run)
    bot_script_path = os.path.join(bot_folder, "bot.py")
    requirements_path = os.path.join(bot_folder, "requirements.txt")

    if not os.path.isdir(bot_folder) or not os.path.exists(bot_script_path):
        log(f"FATAL: Bot folder '{bot_folder}' or script '{bot_script_path}' not found.")
        sys.exit(1)

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

    log(f"Changing directory to {bot_folder} and starting bot...")
    os.chdir(bot_folder)
    subprocess.run([sys.executable, "bot.py"])

    log("Bot Runner Finished.")
