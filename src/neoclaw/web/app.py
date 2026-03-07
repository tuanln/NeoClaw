"""FastAPI application for NeoClaw web dashboard."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the FastAPI application."""
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    from neoclaw.web.routes import analytics, control, device, education

    app = FastAPI(
        title="NeoClaw Dashboard",
        description="Agentic Robot Education Platform",
        version="0.1.0",
    )

    app.include_router(device.router, prefix="/api/device", tags=["device"])
    app.include_router(control.router, prefix="/api/control", tags=["control"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
    app.include_router(education.router, prefix="/api/education", tags=["education"])

    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        return """<!DOCTYPE html>
<html>
<head><title>NeoClaw Dashboard</title>
<style>
    body { font-family: system-ui, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; background: #1a1a2e; color: #e0e0e0; }
    h1 { color: #00d4ff; }
    .card { background: #16213e; border-radius: 12px; padding: 20px; margin: 15px 0; border: 1px solid #0f3460; }
    .btn { background: #00d4ff; color: #1a1a2e; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; margin: 5px; font-weight: bold; }
    .btn:hover { background: #00b4d8; }
    .status { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
    .online { background: #00ff88; }
    .offline { background: #ff4444; }
    #log { background: #0d1b2a; padding: 15px; border-radius: 8px; font-family: monospace; max-height: 300px; overflow-y: auto; }
</style>
</head>
<body>
    <h1>NeoClaw Dashboard</h1>
    <div class="card">
        <h2>Claw Control</h2>
        <button class="btn" onclick="send('move_left')">Left</button>
        <button class="btn" onclick="send('move_right')">Right</button>
        <button class="btn" onclick="send('move_forward')">Forward</button>
        <button class="btn" onclick="send('move_backward')">Back</button>
        <button class="btn" onclick="send('move_up')">Up</button>
        <button class="btn" onclick="send('move_down')">Down</button>
        <button class="btn" onclick="send('grab')">Grab</button>
        <button class="btn" onclick="send('release')">Release</button>
    </div>
    <div class="card">
        <h2>Status</h2>
        <div id="status">Loading...</div>
    </div>
    <div class="card">
        <h2>Log</h2>
        <div id="log"></div>
    </div>
    <script>
        async function send(cmd) {
            const r = await fetch('/api/control/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: cmd, kwargs: {duration: 0.5}})
            });
            const data = await r.json();
            log(cmd + ': ' + JSON.stringify(data));
        }
        function log(msg) {
            const el = document.getElementById('log');
            el.innerHTML += new Date().toLocaleTimeString() + ' ' + msg + '<br>';
            el.scrollTop = el.scrollHeight;
        }
        async function updateStatus() {
            try {
                const r = await fetch('/api/device/status');
                const data = await r.json();
                document.getElementById('status').innerHTML =
                    '<span class="status online"></span>Connected | ' + JSON.stringify(data);
            } catch(e) {
                document.getElementById('status').innerHTML = '<span class="status offline"></span>Disconnected';
            }
        }
        updateStatus();
        setInterval(updateStatus, 5000);
    </script>
</body>
</html>"""

    return app


def run_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    """Run the FastAPI server."""
    import uvicorn
    app = create_app()
    uvicorn.run(app, host=host, port=port)
