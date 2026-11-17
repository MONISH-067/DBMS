"""Vercel entry point for the Marketplace Operations Dashboard."""

from http.server import BaseHTTPRequestHandler

from marketplace.server import handle_vercel_request


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, headers, body = handle_vercel_request(self)
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)
