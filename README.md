# Execution steps

```
git clone https://github.com/SanthoshRaaj-KR/Smart-Energy-demand-digital-twin
cd Smart-Energy-demand-digital-twin
```

### Terminal 1
```
cd backend
activate your virtual environment using conda or python venv
pip install -r requirements.txt
python main.py
uvicorn server:app --reload --port 8000
```

### Terminal 2
```
cd frontend 
npm install
npm run dev
```
