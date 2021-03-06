# !/usr/bin/env python3
# @Time    : 2020/7/31
# @Author  : caicai
# @File    : mysql_brute.py


'''
pymysql.err.OperationalError: (1045, "Access denied for user 'root'@'localhost' (using password: YES)")
pymysql.err.OperationalError: (1130, "xx.xx.x.x' is not allowed to connect to this MySQL server")

'''


from myscan.lib.hostscan.pocbase import PocBase
from myscan.lib.core.data import paths, cmd_line_options, logger
from myscan.lib.hostscan.common import get_data_from_file
from myscan.lib.core.threads import mythread
import os, pymysql


class POC(PocBase):
    def __init__(self, workdata):
        self.dictdata = workdata.get("dictdata")  # python的dict数据，详见 Class3-hostscan开发指南.md
        self.result = []  # 此result保存dict数据，dict需包含name,url,level,detail字段，detail字段值必须为dict。如下self.result.append代码
        self.addr = self.dictdata.get("addr")  # type:str
        self.port = self.dictdata.get("port")  # type:int
        # 以下根据实际情况填写
        self.name = "mysql_brute"
        self.vulmsg = "mysql weak pass"
        self.level = 2  # 0:Low  1:Medium 2:High
        self.require = {
            "service": ["mysql"],  # nmap本身识别为ms-sql-s ,为了以后扩展自己识别脚本,多个mssql
            "type": "tcp"
        }
        # 自定义
        self.right_pwd = None
        self.allow_connect = True

    def verify(self):
        if not self.check_rule(self.dictdata, self.require):  # 检查是否满足测试条件
            return
        pwdfile = os.path.join("brute", "mysql_pass")
        userfile = os.path.join("brute", "mysql_user")
        pwds = [""]
        pwds += get_data_from_file(os.path.join(paths.MYSCAN_DATA_PATH, pwdfile))
        users = get_data_from_file(os.path.join(paths.MYSCAN_DATA_PATH, userfile))
        userpass = []
        for user in users:
            for pwd in pwds:
                userpass.append((user, pwd))
        mythread(self.crack_mysql, userpass, cmd_line_options.threads)
        if self.right_pwd is not None:
            self.result.append({
                "name": self.name,
                "url": "tcp://{}:{}".format(self.addr, self.port),
                "level": self.level,  # 0:Low  1:Medium 2:High
                "detail": {
                    "vulmsg": self.vulmsg,
                    "user/pwd": "/".join(self.right_pwd)
                }
            })

    def crack_mysql(self, userpwd):
        user, pass_ = userpwd
        if self.right_pwd is None and self.allow_connect:
            logger.debug("test mysql_brute userpwd:{}".format(userpwd))
            try:
                pymysql.connect(self.addr, user, pass_, port=self.port)
                self.right_pwd = userpwd
            except Exception as e:
                if "not allowed to connect to" in str(e):
                    self.allow_connect = False
