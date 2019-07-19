#!/usr/bin/env python3
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
from ReadConfig import ReadConfig
from funs import *
from http.cookiejar import CookieJar

if __name__ == "__main__":

    #创建loger对象
    logger = createLog()

    logger.info("=====CrawlArticle开始=====")
    # 执行该程序，不管订阅的频道下面有多少未读文章也不管，也不管执行该段程序跨天不跨天，读取的文章就保存在该文件夹下
    articleStoreDir = time.strftime('%Y-%m-%d', time.localtime(time.time()));
    # 查看本地目录存在不存在，如果不存在，就创建，如果存在就不用处理了
    articleStoreLocalDir = createArticleStoreLocalDir(articleStoreDir);
    logger.info("=====html存储的本地文目录为%s=====",articleStoreLocalDir)

    # 创建一个mysql的连接对象
    mysqlConn = ReadConfig().buildMysqlConnection()
    logger.info("=====连接mysql成功=====")

    # 删除mysql中三天前的数据
    deleteMysqlArticle(mysqlConn)
    logger.info("=====成功删除mysql中三天前的数据=====")

    # 删除本地文件目录
    deleteLocalDirArticle()
    logger.info("=====成功删除本地文件目录=====")


    #得到所有的用户列表
    allUsers = queryUsers(mysqlConn)
    if not allUsers:
        logger.info("========请添加用户========")
    else:
        for user in allUsers:
            #创建session并初始化cookie
            sess = requests.session()
            sess.cookies = CookieJar()

            logger.info("=====用户名为：%s 开始抓取文章=====",user[0])

            logger.info("=====开始构建 BuiltTreeJsonData=====")
            treeBuiltJsonDataRes = getBuiltTreeJsonData(sess,user[0],user[1],user[2])
            isSubscribe = analyseTreeBuiltJsonData(treeBuiltJsonDataRes)

            if isSubscribe == True : ## 订阅了频道，但是有可能订阅了频道但是没有新的文章，也有可能订阅了频道有新的文章
                #得到24篇文章[{字段：字段值}]
                articles24LoadedListSorted = analyseNewArticles(articleStoreDir,sess,user[2])
                while articles24LoadedListSorted :
                    logger.info("=====得到了%d篇文章=====",len(articles24LoadedListSorted))
                    # 把文章去保存到本地目录
                    storeFileToLocal(articles24LoadedListSorted, articleStoreLocalDir)
                    # 把文章放在mysql里面
                    storeFileToMysqlVerifyDuplicate(articles24LoadedListSorted,articleStoreLocalDir,mysqlConn)
                    # 取消文章的订阅
                    unsubscribeArticles(articles24LoadedListSorted,sess,user[2])
                    #再次执行上面的程序
                    articles24LoadedListSorted = analyseNewArticles(articleStoreDir,sess,user[2])

            sess.close()
            logger.info("=====用户名为：%s 结束抓取文章=====", user[0])

    #关闭数据库的连接
    mysqlConn.close()
    logger.info("=====CrawlArticle结束=====")