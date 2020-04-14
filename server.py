import http.server
import json
import logging
import os
import sys
import urllib.request
from socketserver import ThreadingMixIn

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class ThreadHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        logging.debug("Server is up and ready to accept connections!")


class ConverterHandler(http.server.BaseHTTPRequestHandler):
    exchange_rates_api_url = "https://api.exchangeratesapi.io/latest?base=USD&symbols=RUB"

    def handle_response(self, code: int, body: dict):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_POST(self):
        if self.path == "/convert/":
            self.handle_convert()
        else:
            response = {"error": "Undefined URL"}
            self.handle_response(404, response)

    def handle_convert(self):
        body: dict = self.get_validated_body()
        if body:
            usd_rate: float = self.get_usd_rate()
            logging.debug("Converting RUB into USD..")
            usd_quantity: float = body["usd_quantity"]
            rub_quantity: float = usd_quantity * usd_rate
            response = {
                "usd_quantity": usd_quantity,
                "rub_quantity": rub_quantity,
                "usd_rate": usd_rate
            }
            logging.debug("..done!")
            self.handle_response(200, response)

    def get_validated_body(self):
        logging.debug("Validating request body..")
        length = int(self.headers.get('Content-length', 0))
        body = self.rfile.read(length).decode()
        if not body:
            logging.debug("..request body is empty.")
            response = {"error": "request body is expected"}
            return self.handle_response(400, response)
        body: dict = json.loads(body)
        return self.validate_request_body(body)

    def validate_request_body(self, body: dict):
        logging.debug("..checking body properties..")
        usd_quantity = body.get("usd_quantity")
        if not usd_quantity:
            logging.debug("..'usd_quantity' is not specified.")
            response = {"error": "usd_quantity must be specified"}
            return self.handle_response(400, response)
        try:
            usd_quantity = float(usd_quantity)
        except ValueError:
            logging.debug("..'usd_quantity' is incorrect.")
            response = {"error": "usd_quantity must be a positive number"}
            return self.handle_response(400, response)
        if usd_quantity < 0:
            logging.debug("..'usd_quantity' is incorrect.")
            response = {"error": "usd_quantity must be a positive number"}
            return self.handle_response(400, response)
        validated_data = {"usd_quantity": usd_quantity}
        logging.debug("..validation is successful.")
        return validated_data

    def get_usd_rate(self) -> float:
        logging.debug("Fetching usd/rub exchange rate..")
        rates = urllib.request.urlopen(self.exchange_rates_api_url)
        rates = rates.read()
        rates = json.loads(rates)
        usd_rate = rates["rates"]["RUB"]
        logging.debug("..fetched!")
        return usd_rate


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8000'))
    server_address = ('', port)
    httpd = ThreadHTTPServer(server_address, ConverterHandler)
    httpd.serve_forever()
