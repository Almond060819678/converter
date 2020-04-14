import threading
import unittest
import urllib.request
import urllib.error
import urllib.parse
import json

from server import ThreadHTTPServer, ConverterHandler


class TestRequests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.url = "http://127.0.0.1:8000/"
        cls.valid_requests = [{"usd_quantity": 5}, {"usd_quantity": "3"}, {"usd_quantity": 6.2}]
        cls.invalid_requests = [{"no_usd_quantity_key": "value"}, {"usd_quantity": "string"}, {"usd_quantity": -2}]
        port = 8000
        server_address = ('', port)
        httpd = ThreadHTTPServer(server_address, ConverterHandler)
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.setDaemon(True)
        server_thread.start()

    def test_valid_requests(self):
        for valid_request in self.valid_requests:
            with self.subTest(case=valid_request):
                data = json.dumps(valid_request).encode("utf-8")
                request = urllib.request.Request(self.url)
                request.add_header('Content-Type', 'application/json; charset=utf-8')
                request.add_header('Content-Length', len(data))
                response = urllib.request.urlopen(request, data)
                self.assertEqual(response.status, 200)

    def test_invalid_requests(self):
        for invalid_request in self.invalid_requests:
            with self.subTest(case=invalid_request):
                data = json.dumps(invalid_request).encode("utf-8")
                request = urllib.request.Request(self.url)
                request.add_header('Content-Type', 'application/json; charset=utf-8')
                request.add_header('Content-Length', len(data))
                try:
                    urllib.request.urlopen(request, data)
                    self.assertTrue(False)
                except urllib.error.HTTPError:
                    self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
