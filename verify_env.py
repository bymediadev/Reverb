from dotenv import load_dotenv
import os


def check_env():
    load_dotenv()

    print("🔍 Verifying environment variables...\n")

    openai_key = os.getenv("OPENAI_API_KEY")
    email = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")
    recipients = os.getenv("EMAIL_RECIPIENTS")

    if openai_key:
        print("✅ OPENAI_API_KEY loaded successfully.")
    else:
        print("❌ OPENAI_API_KEY is missing.")

    if email:
        print(f"✅ EMAIL_ADDRESS: {email}")
    else:
        print("❌ EMAIL_ADDRESS is missing.")

    if password:
        print("✅ EMAIL_PASSWORD loaded.")
    else:
        print("❌ EMAIL_PASSWORD is missing.")

    if recipients:
        print(f"✅ EMAIL_RECIPIENTS: {recipients}")
    else:
        print("❌ EMAIL_RECIPIENTS is missing.")


if __name__ == "__main__":
    check_env()
