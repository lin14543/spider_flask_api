# 本项目简单介绍
这个是我的毕业设计分布式爬虫调度以及数据管理系统的三部分之一。主要实现了以下功能的API
- 添加某爬虫任务
- 暂停某爬虫任务
- 删除某爬虫任务
- 恢复某爬虫任务
- 获取某爬虫任务
- 获取所有爬虫任务状态
- 爬虫心跳接口
- 对某主机添加执行命令
- 获取某主机的所有命令
# 安装运行
我电脑上的这个项目是在ubuntu上用python2编写的。ubuntu的安装运行方法如下。windos和mac与下面的流程一样，但具体方法请自行Google
## 安装python2
ubuntu自带，不用考虑
## 安装Redis
参考https://www.cnblogs.com/wangchunniu1314/p/6339416.html
## 创建并激活虚拟环境
```shell
pip install virtualenv
virtualenv py2[环境名]
source py2/bin/activate
```
## 克隆本项目并安装该项目需要的包
```shell
git clone https://github.com/lin14543/spider_flask_api
cd spider_flask_api
pip install -r requirements.txt
```
## 运行本项目
```shell
python views.py
```
