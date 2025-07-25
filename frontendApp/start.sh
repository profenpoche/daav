echo "Installing frontend dependencies..."
npm i --silent
echo "Frontend dependencies installed !"

echo "Builing frontend..."
npm run build
echo "Build finished !"

echo "Starting frontend..."
npm run start
echo "Frontend started !"