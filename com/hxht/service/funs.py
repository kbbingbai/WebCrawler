#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time   :2019/6/17 9:58
# @Author :zhai shuai
"""
 作用
     一： 辅助工具类，
     二： 功能函数都是写在这个文本里面

 难点

 注意点
"""

import configparser, os, requests, json,re,time
from bs4 import BeautifulSoup
from operator import itemgetter
from elasticsearch import helpers
import string
from urllib.request import *
import http.cookiejar, urllib.parse

from ReadConfig import ReadConfig


def unsubscribeArticles(readerPanelListSorted) :
    """
        取消文章的订阅
        :param readerPanelListSorted: 传入的list，格式是  [{id:文章的url},{id:文章的url},.....]
        :return:
    """
    cf = readConfig("requestHeader.ini", False)

    mainUrl = cf.get("main-url","main-url")
    url = mainUrl

    headerJson = dict(cf.items("request-header"))

    articleIds = []
    for temp in readerPanelListSorted :
        articleIds.append(temp["id"])

    articleIds = "[\"" + "\",\"".join(articleIds) + "\"]"
    mydata = {
        'xjxfun': 'read_article',
        'xjxargs[]': articleIds
    }

    requests.post(url, data=mydata, headers=headerJson)


# def getKeyWord():
#     """
#         得到匹配的关键字并返回这样的形式,{"CommonKW":{"adware","Worm"...}....}
#     """
#     res = es.search(index="crawlerkeyword", body={'query': {'match_all': {}}},params={"size":500})
#     newDict = {}
#     for temp in res['hits']['hits']:
#         typeValue = temp['_source']['type']
#         valueValue = temp['_source']['value']
#         if typeValue in newDict:
#             newDict[typeValue].append(valueValue)
#         else:
#             subList = []
#             subList.append(valueValue)
#             newDict[typeValue]=subList
#     return newDict



# def articleContentRegularMatch(articlesLoadedListSorted):
#     """
#     对文章的内容进行正则的匹配，如果一篇文章的content，匹配了相关的关键字，就打相关的标签
#     :param articlesLoadedListSorted:
#     :return:
#     """
#     keyWordMap = getKeyWord()
#
#     for singleArticle in articlesLoadedListSorted:
#         #取出文章的content
#         articleContent = singleArticle["content"]
#         tags = []
#         for keyWord in keyWordMap:
#             singleGroupListReg = "|".join(keyWordMap[keyWord])
#             isMatch = re.findall(singleGroupListReg,articleContent) #是否匹配到
#             if isMatch: #表示匹配了上
#                 tags.append(keyWord)
#         singleArticle.update({"tags":"|".join(tags)})



"""
    ###################CrawlArticle####存的下需要的函数###############################################
"""


def readConfig(config, section):
    """
        读取配置文件的信息
        :param config: 哪个配置文件
        :param section: 配置文件的section
        :return:
    """
    configDir = "/config/"
    """
        :param section:  想要获取哪个文件的配置信息
        :param section:  想要获取某个配置文件的哪部分的配置信息，如果mysql,es等配置信息
        :return: 返回该配置的字典
    """
    root_dir = os.path.dirname(os.path.abspath('.'))  # 获取当前文件所在目录的上一级目录
    cf = configparser.ConfigParser()
    cf.read(root_dir + configDir + config)  # 拼接得到requestHeader.ini文件的路径，直接使用
    if section != False:
        options = cf.items(section)  # 获取某个section名为Mysql-Database所对应的键
        return dict(options)  # 转成dict
    else:
        return cf

def updateCookieInfo():
    """"
        更新cookie信息
    """
    # # 以指定文件创建CookieJar对象，对象将可以把cookie保存在文件中
    cookie_jar = http.cookiejar.MozillaCookieJar('../config/cookie.txt')
    # # 创建HTTPCookieProcessor对象
    cookie_processor = HTTPCookieProcessor(cookie_jar)
    # # 创建OpenerDirector对象
    opener = build_opener(cookie_processor)
    # 创建一个配置对象
    config = ReadConfig()
    # 定义模拟Chrome浏览器的user_agent
    user_agent = config.getValueByKey("login-user-info","user-agent")

    # 定义请求头
    headers = {'User-Agent': user_agent, 'Connection': 'keep-alive'}
    # 定义请求参数
    username = config.getValueByKey("login-user-info", "username")
    password = config.getValueByKey("login-user-info", "password")
    warp_action = config.getValueByKey("login-user-info", "warp_action")
    remember_me = config.getValueByKey("login-user-info", "remember_me")
    loginUrl = config.getValueByKey("login-user-info", "url")
    params = {
        "username": username,
        "password": password,
        "warp_action": warp_action,
        "remember_me": remember_me
    }
    postdata = urllib.parse.urlencode(params).encode()
    # 创建向登录页面发送POST请求的Request
    request = Request(loginUrl,data = postdata, headers = headers)
    # 使用OpenerDirector发送POST请求
    response = opener.open(request)
    # 将cookie信息写入磁盘文件
    cookie_jar.save(ignore_discard=True, ignore_expires=True)
    cookie_jar.load("../config/cookie.txt",ignore_discard=True,ignore_expires=True)

    cookieInfo = ""
    for item in cookie_jar:
        cookieInfo += item.name+"="+item.value+";"

    config.cf.set("request-header","cookie",cookieInfo)

    with open("../config/requestHeader.ini","w+") as f:
        config.cf.write(f)

def getBuiltTreeJsonData():
    """
        返回 构建树的信息（订阅信息）
        注意：返回的对象实际上是json信息，里面含有构建树的信息
    """
    cf = readConfig("requestHeader.ini", False)
    headerJson = dict(cf.items("request-header"))
    mainUrl = cf.get("main-url", "main-url")
    mydata = {
        'xjxfun': 'build_tree'
    }
    myheader = headerJson
    myresponse = requests.post(mainUrl, data=mydata, headers=myheader)
    if "Invalid function request received" in myresponse.text:   #如果出现了这种情况，这说明获取数据没有获取成功，就需要更新cookie信息
        updateCookieInfo() #更新cookie信息，下面的代码是更新完cookie信息后再进行登陆

        cf = readConfig("requestHeader.ini", False)
        headerJson = dict(cf.items("request-header"))
        mainUrl = cf.get("main-url", "main-url")
        mydata = {
            'xjxfun': 'build_tree'
        }
        myheader = headerJson
        myresponse = requests.post(mainUrl, data=mydata, headers=myheader)
    return myresponse

def createArticleStoreLocalDir(articleStoreDir):
    """
        得到存储文章的本地目录
    """
    cf = readConfig("requestHeader.ini", False)
    articleStoreLocalDir = mainUrl = cf.get("article-storelocaldir", "articlestorelocaldir")

    localDir = articleStoreLocalDir+articleStoreDir+"/"
    if not os.path.exists(localDir):
        os.makedirs(localDir)
    return localDir;

def analyseTreeBuiltJsonData(builtTreeJson):
    """
        解析出订阅信息，
            （1）如果没有订阅，则json.loads(jsonStr.content).get('xjxobj')[1]['data'] 的返回值是：<span></span>
            （2）如果有订阅，则返回的数据要远大于这些字符串
        :param jsonStr: 浏览器返回的信息
        :return:
    """
    channelInfo = json.loads(builtTreeJson.content).get('xjxobj')[1]['data']
    return True if len(channelInfo) > 20 else False



def getPrintArticlesJsonData():
    """
        返回 未读文章信息（订阅频道的未读文章）
        注意：返回的对象实际上是json信息，里面含有未读文章信息
    """
    cf = readConfig("requestHeader.ini", False)
    headerJson = dict(cf.items("request-header"))
    mainUrl = cf.get("main-url", "main-url")
    mydata = {
        'xjxfun': 'print_articles'
    }
    myheader = headerJson
    myresponse = requests.post(mainUrl, data=mydata, headers=myheader)
    return myresponse

def  analyseReaderPanel(printArticlesHtml) :
    """
        得到文章的url信息和文章的id,把它组成一个list,组成一个[{id:文章的url},{id:文章的url},.....]的形式
        :return:
    """
    articleUrlPrefixItem = readConfig("requestHeader.ini", 'article-url-prefix')
    articleUrlPrefix = articleUrlPrefixItem.get("article-url-prefix")#文章url的前缀  比如一个文章的url是 https://www.inoreader.com/article/3a9c6e7972bfb2cf-  那articleUrlPrefix就是https://www.inoreader.com/article/

    soup = BeautifulSoup(printArticlesHtml, 'lxml')
    readerPanels = soup.select('div[data-oid]')

    listTotal = []
    for temp in readerPanels :
        singleMap = {"id":temp['data-aid'],"url":articleUrlPrefix+temp['data-oid']}
        listTotal.append(singleMap)
    return listTotal


def analyseArticlesLoaded(articlesLoadedHtml) :
    """
        用于解析文章,它的解析
        得到文章的url信息和文章的id, 把它组成一个list, 组成一个[{"id":id的值，"htmltext":"文章html的内容"}, {"id":id的值，"htmltext":"文章html的内容"},.....]
        :param articlesLoadedHtml:
        :return:
    """
    listTotal = []
    articleContent = articlesLoadedHtml[0]
    for temp in articleContent.items():  # 转成元组, temp的组成是这样的，('20563836790', 'elementHtml')
        #文章的id
        id = temp[0]
        htmltext = temp[1]
        singleMap = {"id": id, "htmltext":htmltext}
        listTotal.append(singleMap)
    return listTotal

def storeFileToLocal(articlesLoadedListSorted,articleStoreLocalDir):
    # 把文章列表存入本地
    for temp in articlesLoadedListSorted:
        htmltext = temp['htmltext']
        url = temp['url']
        id = temp['id']
        f = open(articleStoreLocalDir + id + ".html", "w", encoding="utf-8")
        f.write(str(htmltext))

# def storeFileToMysql(articles24LoadedListSorted,articleStoreLocalDir,mysqlConn):
        """
           把数据插入到mysql数据库中，这个是方法没有验证数据的重复性
        """
#     cur = mysqlConn.cursor();
#     usersvalues = []
#     for temp in articles24LoadedListSorted:
#         usersvalues.append((temp['url'],articleStoreLocalDir+temp['id']+".html"))
#     # 批量插入数据
#     cur.executemany('insert into webcrawlerfilelist(articleurl,articledir) value(%s,%s)', usersvalues)
#     mysqlConn.commit()#没有提交的话，无法完成插入

def storeFileToMysqlVerifyDuplicate(articles24LoadedListSorted,articleStoreLocalDir,mysqlConn):
    """
        把数据插入到mysql数据库中，这个是方法验证了数据的重复性
    """
    cur = mysqlConn.cursor();
    insertSql = "insert into webcrawlerfilelist(articleurl,articledir) values(%s,%s)"
    querySql = "select count(id) from webcrawlerfilelist where articleurl=(%s)"
    for temp in articles24LoadedListSorted:
        cur.execute(querySql,(temp['url']))
        queryResultRowNum =cur.fetchone()[0]
        if not queryResultRowNum:
            cur.execute(insertSql, (temp['url'],articleStoreLocalDir+temp['id']+".html"))
    # 进行提交，批量插入数据，没有提交的话，无法完成插入
    mysqlConn.commit()

def analyseNewArticles(articleStoreDir):
    """
        查看是否有新的文章,如果有新文章就返回Ture，如果没有新的文章就返回False
        :param printArticleJson:
        :return:
    """
    printArticleInfo = getPrintArticlesJsonData() #得到全部PrintArticles信息
    printArticleInfo = json.loads(printArticleInfo.content).get('xjxobj')

    readerPaneHtml = ''                           #得到{cmd: "as", id: "reader_pane", prop: "innerHTML",…} 这一项的信息
    articlesLoadedHtml = ''                       #得到{cmd: "jc", func: "articles_loaded",…} 这一项的信息

    for tempNum in range(len(printArticleInfo)) :
        if articlesLoadedHtml != '' and readerPaneHtml != '' :
            break
        if 'func' in printArticleInfo[tempNum] :
            if 'check_older_articles_hint' == printArticleInfo[tempNum]['func'] :  #如果有这个方法名，则表明所有的频道下面没有最新的文章
                return False
            if 'articles_loaded' == printArticleInfo[tempNum]['func'] :
                articlesLoadedHtml = printArticleInfo[tempNum]['data']

        if "id" in printArticleInfo[tempNum] :
            if 'as' == printArticleInfo[tempNum]['cmd'] and 'reader_pane' == printArticleInfo[tempNum]['id'] :
                readerPaneHtml = printArticleInfo[tempNum]['data']

    readerPanelList = analyseReaderPanel(readerPaneHtml) #返回[{id:文章的url},{id:文章的url},.....]的形式
    articlesLoadedList = analyseArticlesLoaded(articlesLoadedHtml) #返回[{"id":id的值，"htmltext":"文章html的内容"}, {"id":id的值，"htmltext":"文章html的内容"},.....]的形式

    readerPanelListSorted = sorted(readerPanelList, key=itemgetter('id'), reverse=True)
    articlesLoadedListSorted = sorted(articlesLoadedList, key=itemgetter('id'), reverse=True)

    for tempNum in range(len(articlesLoadedListSorted)) : #把文章的url加入到articlesLoadedListSorted里面去
       articlesLoadedListSorted[tempNum].update({"url":readerPanelListSorted[tempNum]['url']})

    return articlesLoadedListSorted



"""
    ###################AnalyseArticle####存的下需要的函数###############################################
"""

def analyseSingleArticlePublicDate(soupObj) :
    """
        解析文章发表时间  日期有两种格式，
            一个是   %a %b %d, %Y %H:%M   接收日期: Thu Jun 13, 2019 16:32 发布日期: Sun Jun 02, 2019 16:12
            一个是：%H:%M                 接收日期: 09:17 发布日期: 09:09
        :param soupObj:
        :return:
    """
    articleTime = soupObj.find("div", attrs={"class": "header_date"}).attrs['title']
    searchObj = articleTime.split(": ")
    publicDate = searchObj[2]
    if (re.search(r'^\d{2}:\d{2}', publicDate)):
        strTime = time.strftime("%Y-%m-%d ") + publicDate
    else:
        timeStruct = time.strptime(publicDate, "%a %b %d, %Y %H:%M")
        strTime = time.strftime("%Y-%m-%d %H:%M", timeStruct)

    return strTime

def queryAnalyseData(mysqlConn):
    # 使用cursor()方法获取操作游标
    cursor = mysqlConn.cursor()

    # SQL 查询语句
    sql = "select id,articleurl,articledir,updatetime from webcrawlerfilelist where articleflag=-3"
    usersvalues = []
    try:
       # 执行SQL语句
       cursor.execute(sql)
       # 获取所有记录列表
       results = cursor.fetchall()

       #把results这些数据的articleflag=-2表明它正在处理
       for temp in range(0, len(results)):
           usersvalues.append((-2, results[temp][0]))
       cursor.executemany('update webcrawlerfilelist set articleflag =%s where id =%s',usersvalues)
       mysqlConn.commit()  # 没有提交的话，无法完成插入
    except:
       print ("Error: unable to fecth data")
    return results

def analyseSingleArticleAuthor(soup):
    author = soup.find("span", attrs={"class": "article_author"}).text
    author = author.replace(" ", "").replace("\n", "").replace("\t", "")

    author = re.findall(r"(.*)由(.*)新增规则", author)
    if author:
        author = author[0][1]
    else:
        author = ""
    return author

def analyseArticleDate(fetchAll):
    """
    分析文章
    :param fetchAll:
    :return:
    """
    dataList = [];
    insertTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    for row in fetchAll:
        id = row[0]
        articleurl = row[1]
        articledir = row[2]
        singleMap = analyseSingleArticle(articledir,articleurl,id,insertTime)
        dataList.append(singleMap)
    return dataList


def analyseSingleArticle(articledir,articleurl,id,insertTime):
    """
        分析一篇文章的内容，分析出 id,title,content,url,
        :param articledir: 传入该篇文章的本地存储目录
        :return: 
    """""
    f = open(articledir, "r", encoding="utf-8")
    articleContent = f.read()
    soup = BeautifulSoup(articleContent, 'lxml')
    # 文章的id
    title = soup.select(".article_title_link")[0].text.strip()
    publicDate = analyseSingleArticlePublicDate(soup)
    content = soup.find("div", attrs={"class": "article_content"}).text
    #解析作者
    author = analyseSingleArticleAuthor(soup)

    singleMap = {"id": id, "title": title,"author": author,"url": articleurl,"articledir": articledir,"publicDate": publicDate,"insertDate": insertTime,
                 "analyseFlag": "false","content": content}

    return singleMap

def importDataToEs(esConn,articleListData,fetchAll,mysqlConn):
    actions = [
        {
            "_index": "crawler_index",
            "_type": "crawler_type",
            '_source': d
        }
        for d in articleListData
    ]
    # 批量插入
    helpers.bulk(esConn, actions)

    # 把results这些数据的articleflag=-1表明它正在处理
    usersvalues = []
    for temp in range(0, len(fetchAll)):
        usersvalues.append((-1, fetchAll[temp][0]))
    mysqlConn.cursor().executemany('update webcrawlerfilelist set articleflag =%s where id =%s', usersvalues)
    mysqlConn.commit()  # 没有提交的话，无法完成插入