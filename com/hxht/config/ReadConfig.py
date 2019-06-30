#!/user/bin/env python3
# -*- coding: utf-8 -*-
# @Time   :2019/6/25 8:43
# @Author :zhai shuai
"""
 作用
    一：
 难点
    
 注意点
    
"""
import os,configparser,codecs,pymysql
from elasticsearch import Elasticsearch
configPath = os.path.dirname(__file__)+"/requestHeader.ini"

class ReadConfig:
    def __init__(self):
        self.cf = configparser.ConfigParser()
        self.cf.read(configPath)

    def getValueByKey(self,section,name):
        value = self.cf.get(section, name)
        return value

    def buildMysqlConnection(self):
        """
            返回一个mysql对象连接对象
        """
        self.host = self.getValueByKey("mysql", "host")
        self.port = self.getValueByKey("mysql", "port")
        self.user = self.getValueByKey("mysql", "user")
        self.password = self.getValueByKey("mysql", "password")
        self.database = self.getValueByKey("mysql", "db")
        self.charset = self.getValueByKey("mysql", "charset")
        self.cursorclass = self.getValueByKey("mysql", "cursorclass")
        self.db = pymysql.connect(self.host, self.user, self.password, self.database)
        return self.db

    def buildEsConnection(self):
        """
           返回一个mysql对象连接对象
       """
        self.host = self.getValueByKey("es", "host")
        self.port = self.getValueByKey("es", "port")
        self.timeout = self.getValueByKey("es", "timeout")
        self.es = Elasticsearch([{'host': self.host, 'port': self.port, 'timeout': int(self.timeout)}])
        return self.es
