import os
from dotenv import load_dotenv

ENV_FILE = ".env"


def read_env():
    if not os.path.exists(ENV_FILE):
        open(ENV_FILE, "w").close()
    with open(ENV_FILE, "r") as f:
        lines = [line.strip() for line in f if "=" in line and not line.startswith("#")]
        for i, line in enumerate(lines, 1):
            print(f"{i}. {line}")
    print()


def set_env(key, value):
    lines = []
    found = False
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            lines = f.readlines()

    with open(ENV_FILE, "w") as f:
        for line in lines:
            if line.startswith(f"{key}="):
                f.write(f"{key}={value}\n")
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f"{key}={value}\n")

    print(f"✅ Set {key}={value}")


def cli():
    while True:
        print("\n🔧 .env Editor")
        print("1. View .env")
        print("2. Set or Update Variable")
        print("3. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            read_env()
        elif choice == "2":
            key = input("Key: ").strip()
            value = input("Value: ").strip()
            set_env(key, value)
        elif choice == "3":
            break
        else:
            print("Invalid option.")


if __name__ == "__main__":
    load_dotenv()
    cli()
