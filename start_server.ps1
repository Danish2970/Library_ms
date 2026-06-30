# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating new virtual environment..."
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
. .\.venv\Scripts\Activate.ps1

# Install requirements
Write-Host "Installing requirements..."
pip install -r requirements.txt

# Run the Django server
# We use -u and --noreload to prevent output buffering and file-watcher hangs on Windows
Write-Host "Starting Django development server..."
python -u manage.py runserver --noreload
