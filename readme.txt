爬虫多次访问同一个网站一段时间后会出现错误 HTTPConnectionPool（host:XX）Max retries exceeded with url
'<requests.packages.urllib3.connection.HTTPConnection object at XXXX>: Failed to establish a new connection:
[Errno 99] Cannot assign requested address'是因为在每次数据传输前客户端要和服务器建立TCP连接，为节省传输消耗，默认为keep-alive，
即连接一次，传输多次，然而在多次访问后不能结束并回到连接池中，导致不能产生新的连接headers中的Connection默认为keep-alive，
将header中的Connection一项置为close

headers = { 'Connection': 'close',}
r = requests.get(url, headers=headers)

--------------------------

查询索引存在不存在


----------------------------


注意在 Commits on Jul 19, 2019  提交的代码，是可部署的，后来发现真正的文章内容，取的不对。是要跳到另一个url进行获取文章的内容。

在Commits on Jul 19, 2019以后的程序是修改围绕这个问题进行的修改。
----------------------------
有的网站爬取不下来，用这个header是可以的
 headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/537.36 LBBROWSER'
        }
 response = requests.get(results[temp][0],timeout=10, headers=headers)
 ------------------------------