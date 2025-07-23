# PowerShell Script: setup_and_run.ps1
# Run this in the project directory

Write-Host "`n--- Setting up podcast feedback tool ---`n"

# 1. Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH."
    exit 1
}

# 2. Create virtual environment (optional)
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "✅ Virtual environment created."
}

# 3. Activate virtual environment
& .\.venv\Scripts\Activate.ps1
Write-Host "✅ Virtual environment activated."

# 4. Install dependencies
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed."
} else {
    Write-Warning "requirements.txt not found. Skipping pip install."
}

# 5. Check for .env and prompt if missing
if (-not (Test-Path ".env")) {
    Write-Host "`n⚠️  .env file not found. Creating a new one..."

    $clientId = Read-Host "Enter your SPOTIFY_CLIENT_ID"
    $clientSecret = Read-Host "Enter your SPOTIFY_CLIENT_SECRET"
    $openaiKey = Read-Host "Enter your OPENAI_API_KEY"

    @"
SPOTIFY_CLIENT_ID=$clientId
SPOTIFY_CLIENT_SECRET=$clientSecret
OPENAI_API_KEY=$openaiKey
"@ | Out-File -Encoding UTF8 .env

    Write-Host "✅ .env file created."
}

# 6. Run the main script
Write-Host "`n🚀 Running podcast feedback script..."
python main.py

Write-Host "`n✅ All done."
