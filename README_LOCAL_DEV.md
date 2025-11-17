Local development: backend + frontend

1) Start backend (FastAPI / uvicorn)

- Activate the Python venv (adjust path if you use `.venv311`):

```powershell
& D:\ExplainNet\.venv311\Scripts\Activate.ps1
```

- Set CORS origins and run uvicorn on 0.0.0.0:8000 (allow Angular dev server to reach it):

```powershell
$env:ALLOW_ORIGINS = "http://localhost:4200,http://127.0.0.1:4200"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Notes:
- `ALLOW_ORIGINS` is read by the app to configure CORS. For quick local dev you can use the two localhost origins shown above. For CI or remote servers, set it to the allowed frontend host(s).
- If you still see `ECONNREFUSED` in the browser, ensure uvicorn is running and Windows Firewall is not blocking the port.

2) Start frontend (Angular dev server)

- Install npm deps (first time):

```powershell
cd frontend\explainnet-ui
npm install
```

- Run the dev server (default listens on http://localhost:4200):

```powershell
npm start
# or
ng serve --host 0.0.0.0 --port 4200
```

3) Confirm connectivity

- Open browser to: http://localhost:4200
- The frontend will call the backend at the base URL configured in `src/environments/environment.ts` (defaults to `http://localhost:8000/api`).

4) Production notes

- Set `environment.apiBaseUrl` appropriately in the production build, or configure a reverse proxy so `/api` routes to the FastAPI server.
- For Docker/Heroku deployments, prefer environment variables and set `ALLOW_ORIGINS` to the frontend host(s).
