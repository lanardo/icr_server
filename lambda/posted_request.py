import requests

src_bucket = "prod.pdf.ecofact.ai"
# path = "5b047ec345e74750135550fe/2018/May/Garant+Bygg+%26+Bad+AB/Credit/201604050021008.TIF.PDF"
path = "5b047ec345e74750135550fe/2018/May/Garant Bygg & Bad AB/Credit/1527067362975-Testfaktura-312111.pdf"

content = {
    "bucket": src_bucket,
    "path": path
}

# 'http://localhost:5000/api/trigger/12345'
res = requests.post('http://localhost:5000/api/trigger/12345', json=content)
# res = requests.post('http://httpbin.org/post', json=content)

if res.ok:
    print(res.json())
