# -*- coding: utf-8 -*-
"""
作用：职教云网课系统课程自动评价
时间：2022-01-09
作者：LittleBlackMouse
"""
import os
import pprint
import requests


class studentStudy:
    def __init__(self, name, password):
        self.name = name
        self.password = password
        self.s = requests.session()

    def log(self, url, headers):
        try:
            respones = self.s.get(url=url, headers=headers)
            cookie = ''
            for name, value in respones.cookies.items():
                cookie += f'{name}={value};'
            with open('Picture/verifyCode.png', 'wb') as f:
                f.write(respones.content)
            verifycode = input('输入验证码：')
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
                'Cookie': cookie
            }
            self.data = {
                'schoolId': 'jlo8aeoo9qfccim7vetc-w',
                'userName': self.name,
                'userPwd': self.password,
                'verifyCode': verifycode
            }
            self.logsys(url='https://zjy2.icve.com.cn/dzx/portalApi/portallogin/login')
        except Exception as ec:
            print(ec)

    def logsys(self, url):
        try:
            respones = self.s.post(url=url, headers=self.headers, data=self.data)
            cookies = respones.cookies
            cookie = ''
            for name, value in cookies.items():
                cookie += f'{name}={value};'
            cookie = self.headers.get('Cookie') + cookie
            Cookie = {'Cookie': cookie}
            self.headers.update(Cookie)
            print(f"{respones.json()['displayName']} 登录成功！")
            self.logcourselist(url='https://zjy2.icve.com.cn/api/student/learning/getLearnningCourseList')
        except Exception as ec:
            print(ec)

    def logcourselist(self, url):
        try:
            response = self.s.post(url=url, headers=self.headers)
            print('课程清单：')
            courselist = dict()
            for classid, classname in zip(range(1, len(response.json()['courseList'])+1),
                                          response.json()['courseList']):
                courselist.update(
                    {classid: {'courseOpenId': classname['courseOpenId'], 'openClassId': classname['openClassId']}})
                print(f"{classid}、{classname['courseName']}")
            classnum = int(input('请选择课程(课程前的编号)：'))
            self.courseOpenId = courselist[classnum]['courseOpenId']
            self.openClassId = courselist[classnum]['openClassId']
            data = {
                'courseOpenId': self.courseOpenId,
                'openClassId': self.openClassId
            }
            self.logclasslist(url='https://zjy2.icve.com.cn/api/study/process/getProcessList', data=data)
        except Exception as ec:
            print(ec)

    def logclasslist(self, url, data):
        try:
            response = self.s.post(url=url, headers=self.headers, data=data)
            print('所选课程章节清单：')
            classlist = dict()
            for moduleid, modulename in zip(range(1, len(response.json()['progress']['moduleList'])+1),
                                            response.json()['progress']['moduleList']):
                classlist.update(
                    {moduleid: {'moduleId': modulename['id']}})
                print(f"{moduleid}、{modulename['name']}")
            modulenum = int(input('请选择章节(章节前的编号,如全选则为0)：'))
            if modulenum == 0:
                content = input('请输入评论语：')
                activityType = input('请输入评论类型（1、评价 2、笔记 3、问答 4、纠错）：')
                for i in classlist.values():
                    self.moduleId = i['moduleId']
                    data = {
                        'courseOpenId': self.courseOpenId,
                        'moduleId': self.moduleId
                    }
                    response = self.s.post(url='https://zjy2.icve.com.cn/api/study/process/getTopicByModuleId',
                                           headers=self.headers, data=data)
                    topicList = []
                    for topic in response.json()['topicList']:
                        topicList.append(topic['id'])
                    for topicId in topicList:
                        data = {
                            'courseOpenId': self.courseOpenId,
                            'openClassId': self.openClassId,
                            'topicId': topicId
                        }
                        response = self.s.post(url='https://zjy2.icve.com.cn/api/study/process/getCellByTopicId',
                                               headers=self.headers, data=data)
                        topicIDs = [Id['Id'] for Id in response.json()['cellList']]
                        topicTypes = [Type['categoryName'] for Type in response.json()['cellList']]
                        topicNames = [Name['cellName'] for Name in response.json()['cellList']]
                        topicLists = [List['childNodeList'] for List in response.json()['cellList']]
                        rtopicIDs = []
                        rtopicNames = []
                        for topicID, topicType, topicName, topicList in zip(topicIDs, topicTypes, topicNames,
                                                                            topicLists):
                            if len(topicList) == 0:
                                rtopicIDs.append(topicID)
                                rtopicNames.append(topicName)
                            else:
                                for i in topicList:
                                    rtopicIDs.append(i['Id'])
                                    rtopicNames.append(i['cellName'])
                        for cellId, cellName in zip(rtopicIDs, rtopicNames):
                            self.post_eluvation(url='https://zjy2.icve.com.cn/api/common/Directory/addCellActivity',
                                                cellId=cellId,
                                                cellName=cellName, content=content, activityType=activityType)
            else:
                content = input('请输入评论语：')
                activityType = input('请输入评论类型（1、评价 2、笔记 3、问答 4、纠错）：')
                self.moduleId = classlist[modulenum]['moduleId']
                data = {
                    'courseOpenId': self.courseOpenId,
                    'moduleId': self.moduleId
                }
                response = self.s.post(url='https://zjy2.icve.com.cn/api/study/process/getTopicByModuleId',
                                       headers=self.headers, data=data)
                topicList = []
                for topic in response.json()['topicList']:
                    topicList.append(topic['id'])
                for topicId in topicList:
                    data = {
                        'courseOpenId': self.courseOpenId,
                        'openClassId': self.openClassId,
                        'topicId': topicId
                    }
                    response = self.s.post(url='https://zjy2.icve.com.cn/api/study/process/getCellByTopicId',
                                           headers=self.headers, data=data)
                    topicIDs = [Id['Id'] for Id in response.json()['cellList']]
                    topicTypes = [Type['categoryName'] for Type in response.json()['cellList']]
                    topicNames = [Name['cellName'] for Name in response.json()['cellList']]
                    topicLists = [List['childNodeList'] for List in response.json()['cellList']]
                    rtopicIDs = []
                    rtopicNames = []
                    for topicID, topicType, topicName, topicList in zip(topicIDs, topicTypes, topicNames, topicLists):
                        if len(topicList) == 0:
                            rtopicIDs.append(topicID)
                            rtopicNames.append(topicName)
                        elif len(topicList) > 0:
                            for i in topicList:
                                rtopicIDs.append(i['Id'])
                                rtopicNames.append(i['cellName'])
                    for cellId, cellName in zip(rtopicIDs, rtopicNames):
                        self.post_eluvation(url='https://zjy2.icve.com.cn/api/common/Directory/addCellActivity',
                                            cellId=cellId,
                                            cellName=cellName, content=content, activityType=activityType)
        except Exception as ec:
            print(ec)

    def post_eluvation(self, url, cellId, cellName, content, activityType):
        eluvationData = {
            'courseOpenId': self.courseOpenId,
            'openClassId': self.openClassId,
            'cellId': cellId,
            'content': content,
            'docJson': '',
            'star': 5,
            'activityType': activityType
        }
        response = requests.post(url=url, headers=self.headers, data=eluvationData)
        if response.status_code == 200:
            print(f'{cellName}\t评价成功！')
        else:
            print(f'{cellName}\t评价失败！')


if __name__ == '__main__':
    i = 'N'
    userlog = studentStudy(name=input('输入账号：'), password=input('输入密码：'))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    }
    userlog.log(url='https://zjy2.icve.com.cn/common/VerifyCode/index', headers=headers)
    print('------------------------程序运行完成！--------------------------')
    i = input('是否退出程序（Y/N）：')
    while i != 'Y':
        i = input('请输入Y退出程序：')
    os.close()
