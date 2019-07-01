#!/user/bin/env python3
# -*- coding: utf-8 -*-
# @Time   :2019/6/24 14:58
# @Author :zhai shuai
"""
 作用
    一 爬取https://www.inoreader.com 网站上订阅频道上的文章，并存入数据库
        (1) 存入数据库的样式是
            id  articleurl    articlefilename
        (2) 每一篇文章，就是一个文件，存入到一个文件夹中，文件夹的命名为当前日期如：2019-06-24
            每一篇文章的filname就是这个文章的id
 难点

 注意点

"""
from funs import *
from http.cookiejar import CookieJar

if __name__ == "__main__" :
    sess = requests.session()
    sess.cookies = CookieJar()
    logger = createLog()

    logger.info("=====开始构建 BuiltTreeJsonData=====")
    treeBuiltJsonDataRes = getBuiltTreeJsonData(sess)
    isSubscribe = analyseTreeBuiltJsonData(treeBuiltJsonDataRes)
    #执行该程序，不管订阅的频道下面有多少未读文章也不管，也不管执行该段程序跨天不跨天，读取的文章就保存在该文件夹下
    articleStoreDir = time.strftime('%Y-%m-%d', time.localtime(time.time()));

    #创建一个mysql的连接对象
    mysqlConn = ReadConfig().buildMysqlConnection()
    logger.info("=====连接mysql成功=====")
    # 查看本地目录存在不存在，如果不存在，就创建，如果存在就不用处理了
    articleStoreLocalDir = createArticleStoreLocalDir(articleStoreDir);

    if isSubscribe == True : ## 订阅了频道，但是有可能订阅了频道但是没有新的文章，也有可能订阅了频道有新的文章
        #得到24篇文章[{字段：字段值}]
        articles24LoadedListSorted = analyseNewArticles(articleStoreDir,sess)
        while articles24LoadedListSorted :
            logger.info("=====得到了24篇文章=====")
            # 把文章去保存到本地目录
            storeFileToLocal(articles24LoadedListSorted, articleStoreLocalDir)
            # 把文章放在mysql里面
            storeFileToMysqlVerifyDuplicate(articles24LoadedListSorted,articleStoreLocalDir,mysqlConn)
            # 取消文章的订阅
            unsubscribeArticles(articles24LoadedListSorted,sess)
            #再次执行上面的程序
            articles24LoadedListSorted = analyseNewArticles(articleStoreDir,sess)
    #关闭数据库的连接
    mysqlConn.close()

    sess.close()
    logger.info("=====CrawlArticle结束=====")