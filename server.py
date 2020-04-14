import http.server
import urllib.request
import json
import os

from socketserver import ThreadingMixIn


class ThreadHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    ...


class ConverterHandler(http.server.BaseHTTPRequestHandler):
    exchange_rates_api_url = "https://api.exchangeratesapi.io/latest?base=USD&symbols=RUB"

    def handle_response(self, code: int, body: dict):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_POST(self):
        body: dict = self.get_validated_body()
        if body:
            usd_rate: float = self.get_usd_rate()
            usd_quantity: float = body["usd_quantity"]
            rub_quantity: float = usd_quantity * usd_rate
            response = {
                "usd_quantity": usd_quantity,
                "rub_quantity": rub_quantity,
                "usd_rate": usd_rate
            }
            self.handle_response(200, response)

    def get_validated_body(self):
        length = int(self.headers.get('Content-length', 0))
        body = self.rfile.read(length).decode()
        if not body:
            response = {"error": "request body is expected"}
            return self.handle_response(400, response)
        body: dict = json.loads(body)
        return self.validate_request_body(body)

    def validate_request_body(self, body: dict):
        usd_quantity = body.get("usd_quantity")
        if not usd_quantity:
            response = {"error": "usd_quantity must be specified"}
            return self.handle_response(400, response)
        try:
            usd_quantity = float(usd_quantity)
        except ValueError:
            response = {"error": "usd_quantity must be a positive number"}
            return self.handle_response(400, response)
        if usd_quantity < 0:
            response = {"error": "usd_quantity must be a positive number"}
            return self.handle_response(400, response)
        validated_data = {"usd_quantity": usd_quantity}
        return validated_data

    def get_usd_rate(self) -> float:
        rates = urllib.request.urlopen(self.exchange_rates_api_url)
        rates = rates.read()
        rates = json.loads(rates)
        usd_rate = rates["rates"]["RUB"]
        return usd_rate


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8000'))
    server_address = ('', port)
    httpd = ThreadHTTPServer(server_address, ConverterHandler)
    httpd.serve_forever()
