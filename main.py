import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def run_api():
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.app:app", "--reload"],
        cwd=BASE_DIR,
    )


def run_bot():
    return subprocess.Popen(
        [sys.executable, "-m", "bot.bot"]
    )


if __name__ == "__main__":
    print("Запуск проекта...")

    api = run_api()
    bot = run_bot()

    try:
        api.wait()
        bot.wait()
    except KeyboardInterrupt:
        print("Остановка...")
        api.terminate()
        bot.terminate()
