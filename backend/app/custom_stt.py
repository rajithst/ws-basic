from enum import Enum
from typing import Callable, Dict
import asyncio

# Mocking Aiola types for the POC
class LiveEvents(Enum):
    Transcript = "transcript"
    Structured = "structured"
    Connect = "connect"
    Disconnect = "disconnect"
    Error = "error"

class MockConnection:
    def __init__(self):
        self.callbacks: Dict[LiveEvents, Callable] = {}
        self.connected = False
        self._byte_count = 0

    def connect(self):
        self.connected = True
        if LiveEvents.Connect in self.callbacks:
            # In a real app, this might be awaited or run in loop
            asyncio.create_task(self._safe_callback(LiveEvents.Connect))
        print("Aiola STT Endpoint Connected (Mock)")

    def on(self, event: LiveEvents):
        def decorator(func: Callable):
            self.callbacks[event] = func
            return func
        return decorator

    async def send(self, pcm_bytes: bytes):
        if not self.connected:
            return
        
        self._byte_count += len(pcm_bytes)
        
        # POC Logic: Simulate a result after receiving ~32KB of audio data
        if self._byte_count > 32000 * 2: 
            self._byte_count = 0
            await self._emit_fake_event()

    async def _emit_fake_event(self):
        # Simulate transcript
        if LiveEvents.Transcript in self.callbacks:
             await self._safe_callback(LiveEvents.Transcript, {"transcript": "I want to go to New York"})

        # Simulate a structured result
        if LiveEvents.Structured in self.callbacks:
            data = {
                "text": "I want to go to New York",
                "entities": [{"name": "destination", "value": "New York"}]
            }
            await self._safe_callback(LiveEvents.Structured, data)

    async def _safe_callback(self, event: LiveEvents, *args):
        if event in self.callbacks:
            cb = self.callbacks[event]
            if asyncio.iscoroutinefunction(cb):
                await cb(*args)
            else:
                cb(*args)

    async def close(self):
        self.connected = False
        if LiveEvents.Disconnect in self.callbacks:
            await self._safe_callback(LiveEvents.Disconnect)

class MockSTTInterface:
    def stream(self, lang_code: str = 'en') -> MockConnection:
        return MockConnection()

class MockToken:
    def __init__(self, access_token: str):
        self.access_token = access_token

class AiolaClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.stt = MockSTTInterface()

    @staticmethod
    def grant_token(api_key: str) -> MockToken:
        # Mock network call
        return MockToken(access_token=f"mock_token_for_{api_key}")
