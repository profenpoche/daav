echo "Checking if python virtual environment exists"
# check if env exists
if [ -f "./.venv/bin/activate" ]; then
    echo "Environment exists"
else
#   if not exists, create it
    echo "Environment doesn't exist"
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Virtual environment created !"
fi
# use the env
echo "Activating virtual environment..."
sh .venv/bin/activate
echo "Virtual environment activated !"

echo "Installing backend dependencies..."
.venv/bin/pip install -q -r requirements.txt
echo "Backend dependencies installed !"

echo "Starting backend..."

.venv/bin/uvicorn app.main:app
echo "Backend started !"