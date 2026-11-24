import asyncio, json
from typing import List

class WSManager:
    def __init__(self):
        self.connections: List = []
        self.loop = None

    def set_loop(self, loop):
        self.loop = loop

    async def connect(self, ws):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws):
        if ws in self.connections:
            self.connections.remove(ws)

    def broadcast(self, data):
        if self.loop is None:
            return
        msg=json.dumps(data)
        async def _send():
            dead=[]
            for ws in list(self.connections):
                try:
                    await ws.send_text(msg)
                except Exception:
                    dead.append(ws)
            for d in dead:
                self.disconnect(d)
        asyncio.run_coroutine_threadsafe(_send(), self.loop)
