爬虫多次访问同一个网站一段时间后会出现错误 HTTPConnectionPool（host:XX）Max retries exceeded with url
'<requests.packages.urllib3.connection.HTTPConnection object at XXXX>: Failed to establish a new connection:
[Errno 99] Cannot assign requested address'是因为在每次数据传输前客户端要和服务器建立TCP连接，为节省传输消耗，默认为keep-alive，
即连接一次，传输多次，然而在多次访问后不能结束并回到连接池中，导致不能产生新的连接headers中的Connection默认为keep-alive，
将header中的Connection一项置为close

headers = { 'Connection': 'close',}
r = requests.get(url, headers=headers)
