import urllib.request
import uuid

boundary = '----WebKitFormBoundary' + uuid.uuid4().hex
data_lines = [
    f'--{boundary}',
    'Content-Disposition: form-data; name="file"; filename="test_config.json"',
    'Content-Type: application/json',
    '',
    '{"agent_name": "GAACA", "max_cycles": 15}',
    f'--{boundary}--',
    ''
]
body = '\r\n'.join(data_lines).encode('utf-8')

req = urllib.request.Request(
    'http://127.0.0.1:5000/api/upload',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)
try:
    res = urllib.request.urlopen(req)
    print("STATUS:", res.status)
    print("BODY:", res.read().decode('utf-8'))
except Exception as e:
    print("ERROR:", e)
