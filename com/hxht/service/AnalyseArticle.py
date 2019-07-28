#!/user/bin/env python3
# -*- coding: utf-8 -*-
# @Time   :2019/6/25 11:47
# @Author :zhai shuai
"""
 作用
    一：进行文章的解析
 难点
    
 注意点
    
"""
from ReadConfig import ReadConfig
from funs import *

if __name__ == "__main__" :


    # log对象
    logger = createLog()
    logger.info("=====AnalyseArticle开始=====")

    # 配置对象
    config = ReadConfig()
    # 得到es的连接对象
    esConn = config.buildEsConnection()

    #准备es索引
    indexPrefix = config.getValueByKey("es","index_prefix")
    es_type = config.getValueByKey("es", "type")
    currentDate = time.strftime('%Y%m%d', time.localtime(time.time()));
    es_index = indexPrefix+currentDate

    logger.info("=====连接elasticsearch成功=====")
    # 得到mysql的连接对象
    mysqlConn = config.buildMysqlConnection()
    logger.info("=====连接mysql成功=====")

    logger.info("=====开始从mysql数据库中查询待处理的数据=====")
    #从数据库中查询待处理的数据
    fetchAll = queryAnalyseData(mysqlConn)

    logger.info("=====开始解析从mysql数据库中查询到的数据=====")
    #数据的解析
    articleListData = analyseArticleDate(fetchAll)

    logger.info("=====录入到es格式化后的数据=====")
    #入es数据
    importDataToEs(esConn,articleListData,fetchAll,mysqlConn,es_index,es_type)

    #关闭相应的连接
    mysqlConn.close()

    logger.info("=====AnalyseArticle结束=====")
