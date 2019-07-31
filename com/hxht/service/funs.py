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
import configparser, os, requests, json,re,time,logging,datetime,shutil
from bs4 import BeautifulSoup
from elasticsearch import helpers
import uuid

def unsubscribeArticles(readerPanelListSorted,sess,websiteurl) :
    """
        取消文章的订阅
        :param readerPanelListSorted: 传入的list，格式是  [{id:文章的url},{id:文章的url},.....]
        :return:
    """
    articleIds = []
    for temp in readerPanelListSorted :
        articleIds.append(temp["id"])
    articleIds = "[\"" + "\",\"".join(articleIds) + "\"]"
    mydata = {
        'xjxfun': 'read_article',
        'xjxargs[]': articleIds
    }

    requests.post(websiteurl, data=mydata,cookies=sess.cookies)

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

def getBuiltTreeJsonData(sess,username,password,websiteurl):
    cf = readConfig("requestHeader.ini", False)
    headerJson = {
        "referer":str(websiteurl)+"/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
    }

    loginUrl = str(websiteurl)+"/login"

    warp_action = cf.get("login-user-info", "warp_action")
    remember_me = cf.get("login-user-info", "remember_me")
    params = {
        "username": username,
        "password": password,
        "warp_action": warp_action,
        "remember_me": remember_me
    }
    # 创建向登录页面发送POST请求的Request
    sess.post(loginUrl, data=params, headers=headerJson)

    mydata = {
                'xjxfun': 'build_tree'
            }

    myresponse = requests.post(websiteurl, data=mydata, cookies=sess.cookies)
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
    return localDir

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



def getPrintArticlesJsonData(sess,websiteurl):
    """
        返回 未读文章信息（订阅频道的未读文章）
        注意：返回的对象实际上是json信息，里面含有未读文章信息
    """
    cf = readConfig("requestHeader.ini", False)
    mydata = {
        'xjxfun': 'print_articles'
    }
    myresponse = requests.post(websiteurl, data=mydata, cookies=sess.cookies)
    return myresponse

def  analyseReaderPanel(printArticlesHtml,websiteurl) :
    """
        得到文章的url信息和文章的id,把它组成一个list,组成一个[{id:文章的url},{id:文章的url},.....]的形式
        :return:
    """
    articleUrlPrefix = str(websiteurl)+"/article/"
    soup = BeautifulSoup(printArticlesHtml, 'lxml')
    readerPanels = soup.select('div[data-oid]')

    listTotal = []
    for temp in readerPanels :
        singleMap = {"id":temp['data-aid'],"url":articleUrlPrefix+temp['data-oid']}
        listTotal.append(singleMap)
    return listTotal


def analyseArticlesLoaded(articlesLoadedHtml,username) :
    """
        用于解析文章,它的解析
        得到文章的url信息和文章的id, 把它组成一个list, 组成一个[{"id":id的值，"htmltext":"文章html的内容"}, {"id":id的值，"htmltext":"文章html的内容"},.....]
        :param articlesLoadedHtml:
        :return:
    """
    listTotal = []
    articleContent = articlesLoadedHtml[0]
    for temp in articleContent.items():
        id = temp[0]
        htmltext = temp[1]
        soup = BeautifulSoup(htmltext, 'lxml')
        articleUrl = soup.find("div", attrs={"class": "header_buttons"}).find("a")["href"]
        articleTitle = soup.select(".article_title_link")[0].text.strip()
        articlePublicDate = analyseSingleArticlePublicDate(soup)
        articleAuthor = analyseSingleArticleAuthor(soup)
        articleChannel = analyseSingleArticleChannel(soup)
        articleId = str(uuid.uuid1())
        singleMap = {
            "articleUrl":articleUrl,
            "articleTitle":articleTitle,
            "articlePublicDate":articlePublicDate,
            "articleAuthor":articleAuthor,
            "articleId":articleId,
            "username":username,
            "articlechannel":articleChannel,
            "id":id
        }
        listTotal.append(singleMap)
    return listTotal


def storeFileToLocal(articlesLoadedListSorted,articleStoreLocalDir):
    # 把每篇文章写入本地目录文件
    for temp in articlesLoadedListSorted:
        if "articleContent" in temp: #判断本篇文章是否取到了内容，如果没有取得内容，就不存入本地目录
            articleContent = temp['articleContent']
            articleId = temp['articleId']
            f = open(articleStoreLocalDir + articleId + ".html", "w", encoding="utf-8")
            f.write(str(articleContent))
            f.close()


def storeFileToMysqlVerifyDuplicate(articles24LoadedListSorted,articleStoreLocalDir,mysqlConn):
    """
        把数据插入到mysql数据库中，这个是方法验证了数据的重复性
    """
    cur = mysqlConn.cursor();
    insertSql = "insert into webcrawlerfilelist(id,articleurl,articledir,articletitle,articleauthor,publicdate,iscrawler,username,articlechannel)" \
                " values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    querySql = "select count(id) from webcrawlerfilelist where articleurl=(%s)"
    for temp in articles24LoadedListSorted:
        articleLocalDir = articleStoreLocalDir + temp['articleId'] + ".html" if "articleContent" in temp else ""
        cur.execute(querySql,(temp['articleUrl']))
        queryResultRowNum =cur.fetchone()[0]
        if not queryResultRowNum:
            cur.execute(
                insertSql,
                (temp['articleId'],temp['articleUrl'],articleLocalDir,temp['articleTitle'],
                 temp['articleAuthor'],temp['articlePublicDate'],temp['isCrawler'],temp['username'],temp['articlechannel'])
            )
    # 进行提交，批量插入数据，没有提交的话，无法完成插入
    mysqlConn.commit()

def analyseNewArticles(sess,websiteurl,username,mysqlConn):
    """
        查看是否有新的文章,如果有新文章就返回[{"id":id的值，"htmltext":"文章html的内容"}]，如果没有新的文章就返回False
        :param printArticleJson:
        :return:
    """
    printArticleInfo = getPrintArticlesJsonData(sess,websiteurl) #得到全部PrintArticles信息
    printArticleInfo = json.loads(printArticleInfo.content).get('xjxobj')

    articlesLoadedHtml = ''                       #得到{cmd: "jc", func: "articles_loaded",…} 这一项的信息

    for tempNum in range(len(printArticleInfo)) :
        if articlesLoadedHtml != '':
            break
        if 'func' in printArticleInfo[tempNum] :
            if 'check_older_articles_hint' == printArticleInfo[tempNum]['func'] :  #如果有这个方法名，则表明所有的频道下面没有最新的文章
                return False
            if 'articles_loaded' == printArticleInfo[tempNum]['func'] :
                articlesLoadedHtml = printArticleInfo[tempNum]['data']
    articlesLoadedList = analyseArticlesLoaded(articlesLoadedHtml,username)
    articlesLoadedList = getArticleContent(articlesLoadedList,mysqlConn);
    return articlesLoadedList

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
    sql = "select id,articleurl,articledir,updatedate,articletitle,articleauthor,publicdate,iscrawler from webcrawlerfilelist where articleflag=-3"
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
    textauthor = soup.find("span", attrs={"class": "article_author"}).text
    textauthor = textauthor.replace(" ", "").replace("\n", "").replace("\t", "")

    author = re.findall(r"(.*)由(.*)新增规则", textauthor)
    if len(author) ==0:
        author = re.findall(r"(.*)by(.*)Createrule", textauthor)
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
        articleurl = row[1]
        articledir = row[2]
        articletitle = row[4]
        articleauthor = row[5]
        publicdate = str(row[6])
        iscrawler = row[7]
        finalEsContent = analyseSingleArticle(articledir,iscrawler)
        if iscrawler != 4:
            singleMap = {"title": articletitle, "author": articleauthor,
                         "url": articleurl, "articledir": articledir,
                         "publicDate": publicdate, "insertDate": insertTime,
                         "analyseFlag": "false", "content": finalEsContent,"iscrawler":iscrawler}
            dataList.append(singleMap)
    return dataList


def analyseSingleArticle(articledir,iscrawler):
    """
          分析一篇文章的内容，这里只分析文章的内容
          :param articledir: 传入该篇文章的本地存储目录,爬虫标识
          :return:
    """
    finalEsContent = ""
    if iscrawler == 1:
        f = open(articledir, "r", encoding="utf-8")
        articleContent = f.read()
        soup = BeautifulSoup(articleContent)
        [s.extract() for s in soup(["script", "img", "style", "input","svg"])]   #去除这些指定的标签，因为对于文章内容来说这些是没有用的
        for child in soup.find_all('body'):
            finalEsContent += str(child)
        f.close()
    return finalEsContent

def importDataToEs(esConn,articleListData,fetchAll,mysqlConn,es_index,es_type):
    actions = [
        {
            "_index": es_index,
            "_type": es_type,
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


def createLog():
    cf = readConfig("requestHeader.ini", False)
    log_path = cf.get("logger", "loggerDir")
    # 第一步，创建一个logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Log等级总开关
    # 第二步，创建一个handler，用于写入日志文件
    rq = time.strftime('%Y%m', time.localtime(time.time()))
    log_name = log_path + rq + '.log'
    logfile = log_name
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    fh = logging.FileHandler(logfile, mode='a', encoding="utf-8")
    fh.setLevel(logging.DEBUG)  # 输出到file的log等级的开关
    # 第三步，定义handler的输出格式
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    # 第四步，将logger添加到handler里面
    logger.addHandler(fh)
    return logger


def queryUsers(mysqlConn):
    """
    获取所有的用户
    :param mysqlConn: mysql连接
    :return:
    """
    cur = mysqlConn.cursor();
    querySql = "select username,password,websiteurl,websitename from webcrawlerusers"
    cur.execute(querySql)
    results = cur.fetchall()
    return results

def deleteMysqlArticle(mysqlConn):
    """
    每天删除mysql三天前已经成功的数据
    :param mysqlConn:
    :return:
    """
    cur = mysqlConn.cursor();
    beforeThreeDay = datetime.date.today() + datetime.timedelta(-6)
    sql = 'delete from webcrawlerfilelist where updatedate < STR_TO_DATE(%s,%s) and articleflag = %s'
    cur.execute(sql,[beforeThreeDay,'%Y-%m-%d',-1])
    mysqlConn.commit()

def deleteLocalDirArticle():
    """
    每天删除本地存储文件当中三天前数据
    :return:
    """
    beforeThreeDay = datetime.date.today() + datetime.timedelta(-7)
    cf = readConfig("requestHeader.ini", False)
    localFileDir = cf.get("article-storelocaldir", "articlestorelocaldir")
    removeDir = localFileDir+str(beforeThreeDay)
    if os.path.exists(removeDir):
        shutil.rmtree(removeDir)

def getArticleContent(articlesLoadedList,mysqlConn):
    """
        该方法是取得每篇文章的文章内容
        :param articlesLoadedList: 这个是一个列表list<dict>
        :return:
    """

    #开启文章的过滤，如果是特定频道（不能抓取的频道，就不让它尝试抓取了）
    excludeChannel = getExcludeChannel(mysqlConn)
    #开启文章的过滤


    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/537.36 LBBROWSER'
    }
    for temp in articlesLoadedList:
        articleUrl = temp["articleUrl"]
        articlechannel = temp["articlechannel"].strip()
        try:
            if articlechannel not in excludeChannel:
                response = requests.get(articleUrl,timeout=80,headers=headers)
                if response.status_code == 200:
                    temp["isCrawler"] = 1
                    temp["articleContent"] = response.text
                else:
                    temp["isCrawler"] = 2
            else:
                temp["isCrawler"] = 4
        except Exception:
            temp["isCrawler"] = 3
    return articlesLoadedList

def analyseSingleArticleChannel(soup):
    """
    分析一篇文章的频道
    :param soup:
    :return:
    """
    channel = ""
    tag = soup.find("a", attrs={"class": "boldlink boldlink ajaxed"})
    if tag:
        channel = tag.text
    return channel

def retryCrawler(mysqlConn,articleStoreLocalDir):
    """
    对于初次不能爬取的文章，我们再去尝试去爬取
    :param mysqlConn:
    :param articleStoreLocalDir:
    :return:
    """
    querySql = "select id,articleurl,iscrawler,articlechannel from webcrawlerfilelist where iscrawler in (2,3) and articleflag=-3"
    cur = mysqlConn.cursor()
    cur.execute(querySql)
    results = cur.fetchall()

    retryList = tupleToList(results)#tuple转成list
    retryList = getArticleContent(retryList,mysqlConn)#再次去请求网络
    retryUpdateArticleContent(mysqlConn,retryList,articleStoreLocalDir)#更新本地文件和数据库


def tupleToList(result):
    """
    把tuple<tuple> 转换成list<dict>
    :param result:
    :return:
    """
    list = []
    for temp in result:
        single = {
            "id":temp[0],
            "articleUrl":temp[1],
            "isCrawler":temp[2],
            "articlechannel":temp[3]
        }
        list.append(single)
    return list

def retryUpdateArticleContent(mysqlConn,retryList,articleStoreLocalDir):
    """
    更新再次请求的数据
    :param retryList:
    :return:
    """
    cur = mysqlConn.cursor()
    updateSql = "update webcrawlerfilelist set articledir=%s,iscrawler=%s where id=%s"
    for temp in retryList:
        if "articleContent" in temp:
            #把文章内容写入文件
            localdir = articleStoreLocalDir + temp["id"] + ".html"
            f = open(localdir, "w", encoding="utf-8")
            f.write(str(temp['articleContent']))
            f.close()
            #更新数据库
            cur.execute(updateSql,(localdir, temp['isCrawler'], temp['id']))
    mysqlConn.commit()


def getExcludeChannel(mysqlConn):
    """
    查询常见的不能抓取的频道名称
    :param mysqlConn:
    :return:
    """
    sql = "select channelname from excludechannel"
    # 执行SQL语句
    cursor = mysqlConn.cursor()
    cursor.execute(sql)
    # 获取所有记录列表
    results = cursor.fetchall()
    #把元组转成list
    resultList = []
    for temp in results:
        resultList.append(temp[0])
    return resultList;

def createEsIndex(esConn,es_index,es_type):
    """
    创建es索引
    :param esConn:
    :param es_index:
    :param es_type:
    :return:
    """
    CREATE_BODY = {
        "settings": {
            "number_of_shards": 5,
            "number_of_replicas": 1
        },
        "mappings": {
            es_type: {
                "properties": {
                    "analyseFlag": {
                        "type": "keyword"
                    },
                    "articledir": {
                        "type": "keyword"
                    },
                    "author": {
                        "type": "text",
                        "analyzer": "ik_max_word",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "ik_max_word",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 80000
                            }
                        }
                    },
                    "insertDate": {
                        "type": "keyword"
                    },
                    "iscrawler": {
                        "type": "long"
                    },
                    "publicDate": {
                        "type": "keyword"
                    },
                    "title": {
                        "type": "text",
                        "analyzer": "ik_max_word",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 500
                            }
                        }
                    },
                    "url": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 500
                            }
                        }
                    }
                }
            }
        }
    }
    esConn.indices.create(index=es_index, body=CREATE_BODY)