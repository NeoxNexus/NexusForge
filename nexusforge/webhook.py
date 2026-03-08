from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from nexusforge.capture import capture_idea_message
from nexusforge.config import Config


def start_server(config: Config, host: str = "127.0.0.1", port: int = 8765) -> None:
    handler = make_handler(config)
    server = ThreadingHTTPServer((host, port), handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def make_handler(config: Config):
    class NexusForgeHandler(BaseHTTPRequestHandler):
        server_version = "NexusForge/0.1"

        def do_GET(self) -> None:
            if self.path != "/health":
                self._send_json(404, {"error": "Not found"})
                return
            self._send_json(200, {"status": "ok"})

        def do_POST(self) -> None:
            source = source_from_path(self.path)
            if not source:
                self._send_json(404, {"error": "Unsupported endpoint"})
                return

            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self._send_json(400, {"error": "Invalid JSON payload"})
                return

            text = extract_message_text(payload, source)
            if not text:
                self._send_json(400, {"error": "No message text found"})
                return

            try:
                idea, path = capture_idea_message(text, config, source=source)
            except ValueError as error:
                self._send_json(422, {"error": str(error)})
                return

            self._send_json(
                200,
                {
                    "status": "captured",
                    "message": f"Idea captured! Stored as {idea.title}.",
                    "path": path,
                    "slug": idea.slug,
                },
            )

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_json(self, status_code: int, payload: dict[str, object]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return NexusForgeHandler


def source_from_path(path: str) -> str | None:
    if path == "/capture":
        return "capture"
    if path == "/telegram":
        return "telegram"
    if path == "/discord":
        return "discord"
    return None


def extract_message_text(payload: dict[str, object], source: str) -> str:
    if source == "capture":
        value = payload.get("text", "")
        return str(value).strip()
    if source == "telegram":
        message = payload.get("message") or payload.get("edited_message") or {}
        if isinstance(message, dict):
            return str(message.get("text", "")).strip()
        return ""
    if source == "discord":
        return str(payload.get("content", "")).strip()
    return ""
