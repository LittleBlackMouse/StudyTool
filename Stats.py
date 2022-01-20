# -*- coding: utf-8 -*-
"""

tool name：网络课刷评价工具
author：LittleBlackMouse

"""
import sys
import requests
from PySide2 import QtGui
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication, QTextBrowser, QLineEdit
from PySide2.QtUiTools import QUiLoader
from threading import Thread
from PySide2.QtCore import Signal, QObject, QThread


# 自定义信号源对象类型，一定要继承自QObject
class MySignals(QObject):
    """
    定义一种信号，两个参数 类分别是： QTextBrowser 和 字符串
    """
    picture_show = Signal(QTextBrowser, str)
    text_print = Signal(QTextBrowser, str)
    plan_print = Signal(QTextBrowser, int)


class MyThread(QThread):
    """
    子线程执行耗时任务
    """
    evaluate_signal = Signal(QTextBrowser, str)
    plan_speed_signal = Signal(QTextBrowser, int)

    def __init__(self):
        super(MyThread, self).__init__()

    def run(self):
        """
        执行评价
        :return:
        """
        if self.evaluate_type == '':
            self.evaluate_signal.emit(self.slot, f"请选择评价类型\n")
        elif self.evaluate_text == '':
            self.evaluate_signal.emit(self.slot, f"请输入评价内容\n")
        elif self.process_name == '':
            self.evaluate_signal.emit(self.slot, f"请选择章节\n")
        elif self.class_name == '':
            self.evaluate_signal.emit(self.slot, f"请选择课程或先登录\n")
        else:
            self.evaluate_signal.emit(self.slot, f"评价中...\n请耐性等待...\n")
            # 1、评价 2、笔记 3、问答 4、纠错
            trunslate = {'评价': '1', '笔记': '2', '问答': '3', '纠错': '4'}
            evaluate_type = trunslate[self.evaluate_type]
            topicList = getTopicByModuleId(self.process_name, self.class_name)
            rtopicIDs, rtopicNames = getCellByTopicId(topicList, self.class_name)
            self.value.setRange(0, len(rtopicIDs))
            for cellId, cellName, index in zip(rtopicIDs, rtopicNames, range(1, len(rtopicIDs) + 1)):
                result = addCellActivity(class_name=self.class_name, cellId=cellId, cellName=cellName,
                                         content=self.evaluate_text,
                                         activityType=evaluate_type)
                self.evaluate_signal.emit(self.slot, f"{result}\n")
                self.plan_speed_signal.emit(self.value, index)
            self.evaluate_signal.emit(self.slot, f"评价完成！\n")


def getVerifyCode():
    """
    获取验证码
    :return:
    """
    url = 'https://zjy2.icve.com.cn/common/VerifyCode/index'
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    }
    respones = requests.get(url=url, headers=header)
    cookie = ''
    for name, value in respones.cookies.items():
        cookie += f'{name}={value};'
    with open('Picture/verifyCode.png', 'wb') as f:
        f.write(respones.content)
    return cookie


def loginMS(data, header):
    """
    登陆信息
    :param username:
    :param password:
    :param verifycode:
    :return:
    """
    try:
        respones = requests.post(url='https://zjy2.icve.com.cn/dzx/portalApi/portallogin/login', headers=header,
                                 data=data)
        if 'displayName' in respones.json():
            cookies = respones.cookies
            cookie = ''
            for name, value in cookies.items():
                cookie += f'{name}={value};'
            cookie = global_header.get('Cookie') + cookie
            Cookie = {'Cookie': cookie}
            global_header.update(Cookie)
            message = f"{respones.json()['displayName']} 登录成功！\n"
        elif 'msg' in respones.json():
            message = f"登录失败！：{respones.json()['msg']}\n"
        else:
            message = "登录失败！：未知异常\n"
        return message
    except:
        message = "登录失败！：网络异常\n"
        return message


def getLearnningCourseList(header):
    """
    获取登录账号下的课程清单
    :return:
    """
    respones = requests.post(url='https://zjy2.icve.com.cn/api/student/learning/getLearnningCourseList', headers=header)
    global courselist
    courselist = dict()
    for classname in respones.json()['courseList']:
        courselist.update({classname['courseName']: {'courseOpenId': classname['courseOpenId'],
                                                     'openClassId': classname['openClassId']}})
    return courselist


def getProcessList(data):
    """
    获取所选课程下的章节
    :param data:
    :return:
    """
    respones = requests.post(url='https://zjy2.icve.com.cn/api/study/process/getProcessList', headers=global_header,
                             data=data)
    global process_list
    process_list = dict()
    for modulename in respones.json()['progress']['moduleList']:
        process_list.update({modulename['name']: {'moduleId': modulename['id']}})
    return process_list


def getTopicByModuleId(process_name, class_name):
    """
    获取详细评价科目
    :return:
    """

    if process_name == 'ALL':
        topicList = []
        for i in process_list.values():
            moduleId = i['moduleId']
            data = {
                'courseOpenId': courselist[class_name]['courseOpenId'],
                'moduleId': moduleId
            }
            response = requests.post(url='https://zjy2.icve.com.cn/api/study/process/getTopicByModuleId',
                                     headers=global_header, data=data)
            for topic in response.json()['topicList']:
                topicList.append(topic['id'])
        return topicList
    else:
        moduleId = process_list[process_name]['moduleId']
        data = {
            'courseOpenId': courselist[class_name]['courseOpenId'],
            'moduleId': moduleId
        }
        response = requests.post(url='https://zjy2.icve.com.cn/api/study/process/getTopicByModuleId',
                                 headers=global_header, data=data)
        topicList = []
        for topic in response.json()['topicList']:
            topicList.append(topic['id'])
        return topicList


def getCellByTopicId(topicList, class_name):
    """
    :param topicList:
    :param class_name:
    :return:
    """
    rtopicIDs = []
    rtopicNames = []
    for topicId in topicList:
        data = {
            'courseOpenId': courselist[class_name]['courseOpenId'],
            'openClassId': courselist[class_name]['openClassId'],
            'topicId': topicId
        }
        response = requests.post(url='https://zjy2.icve.com.cn/api/study/process/getCellByTopicId',
                                 headers=global_header, data=data)
        topicIDs = [Id['Id'] for Id in response.json()['cellList']]
        topicTypes = [Type['categoryName'] for Type in response.json()['cellList']]
        topicNames = [Name['cellName'] for Name in response.json()['cellList']]
        topicLists = [List['childNodeList'] for List in response.json()['cellList']]
        for topicID, topicType, topicName, topicList in zip(topicIDs, topicTypes, topicNames, topicLists):
            if len(topicList) == 0:
                rtopicIDs.append(topicID)
                rtopicNames.append(topicName)
            elif len(topicList) > 0:
                for i in topicList:
                    rtopicIDs.append(i['Id'])
                    rtopicNames.append(i['cellName'])
    return rtopicIDs, rtopicNames


def addCellActivity(class_name, cellId, cellName, content, activityType):
    """
    对选择的科目进行评价
    :param class_name:
    :param cellId:
    :param cellName:
    :param content:
    :param activityType:
    :return:
    """
    data = {
        'courseOpenId': courselist[class_name]['courseOpenId'],
        'openClassId': courselist[class_name]['openClassId'],
        'cellId': cellId,
        'content': content,
        'docJson': '',
        'star': 5,
        'activityType': activityType
    }
    response = requests.post(url='https://zjy2.icve.com.cn/api/common/Directory/addCellActivity', headers=global_header,
                             data=data)
    if response.status_code == 200:
        result = f'{cellName}\t评价成功！'
        return result
    else:
        result = f'{cellName}\t评价失败！'
        return result


class Stats:
    def __init__(self):
        """
        从文件中加载UI定义
        从UI定义中动态创建一个相应的窗口对象
        注意：里面的控件对象也成为窗口对象的属性了
        """
        self.ui = QUiLoader().load('./Ui/Stats.ui')
        self.ui.lineEdit_2.setEchoMode(QLineEdit.Password)
        self.ui.pushButton_2.clicked.connect(self.verifyCode)
        self.ui.pushButton.clicked.connect(self.login)
        self.ui.pushButton_3.clicked.connect(self.evaluate_to_thread)
        self.ui.comboBox_3.addItems(['评价', '笔记', '问答', '纠错'])
        self.ui.comboBox_2.currentIndexChanged.connect(self.selectCourse)
        self.ui.comboBox.currentIndexChanged.connect(self.selectProcess)
        self.ui.comboBox_3.currentIndexChanged.connect(self.selectEvaluate)
        self.my_thread = MyThread()
        self.my_thread.evaluate_signal.connect(self.loginMessage)
        self.my_thread.plan_speed_signal.connect(self.planSpeed)
        self.ms = MySignals()
        self.ms.picture_show.connect(self.showVerifyCode)
        self.ms.text_print.connect(self.loginMessage)
        self.ms.plan_print.connect(self.planSpeed)

    def showVerifyCode(self, fb, path):
        """
        显示验证码图片
        :param fb:
        :param path:
        :return:
        """
        pig = QtGui.QPixmap(path)
        fb.setPixmap(pig)
        fb.setScaledContents(True)

    def verifyCode(self):
        """
        更新验证码
        :return:
        """

        def threadFunc():
            cookie = getVerifyCode()
            global global_header
            global_header = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
                'Cookie': cookie
            }
            path = './Picture/verifyCode.png'
            self.ms.picture_show.emit(self.ui.label, f"{path}")

        thread = Thread(target=threadFunc())
        thread.start()

    def login(self):
        """
        获取填写信息并登陆
        :return:
        """
        self.password = self.ui.lineEdit_2.text()
        self.username = self.ui.lineEdit.text()
        self.verify_code = self.ui.lineEdit_3.text()
        self.message()

    def loginMessage(self, fb, text):
        """
        打印登陆及执行信息
        :param fb:
        :param text:
        :return:
        """
        fb.append(str(text))
        fb.ensureCursorVisible()

    def planSpeed(self, fb, value):
        """
        刷新进度条
        :return:
        """
        fb.setValue(int(value))

    def message(self):
        """
        登陆及执行信息
        :return:
        """

        def threadFunc2():
            data = {
                'schoolId': 'jlo8aeoo9qfccim7vetc-w',
                'userName': self.username,
                'userPwd': self.password,
                'verifyCode': self.verify_code
            }
            text = loginMS(data=data, header=global_header)
            self.ms.text_print.emit(self.ui.textBrowser, f"{text}")
            self.ui.comboBox_2.clear()
            self.ui.comboBox_2.addItem('')
            if '登录成功' in text:
                courselist = getLearnningCourseList(header=global_header)
                for class_name in courselist.keys():
                    self.ui.comboBox_2.addItem(class_name)

        thread = Thread(target=threadFunc2())
        thread.start()

    def selectCourse(self):
        """
        选择课程触发器
        :return:
        """

        def threadFunc3():
            class_name = self.ui.comboBox_2.currentText()
            if class_name != '':
                self.ms.text_print.emit(self.ui.textBrowser, f"已选择课程：{class_name}\n")
                self.ui.comboBox.clear()
                self.ui.comboBox.addItem('')
                courseOpenId = courselist[class_name]['courseOpenId']
                openClassId = courselist[class_name]['openClassId']
                data = {
                    'courseOpenId': courseOpenId,
                    'openClassId': openClassId
                }
                process_list = getProcessList(data=data)
                self.ui.comboBox.addItem('ALL')
                for process_name in process_list.keys():
                    self.ui.comboBox.addItem(process_name)

        thread = Thread(target=threadFunc3())
        thread.start()

    def selectProcess(self):
        """
        选择章节触发器
        :return:
        """

        def threadFunc4():
            process_name = self.ui.comboBox.currentText()
            if process_name != '':
                self.ms.text_print.emit(self.ui.textBrowser, f"已选章节：{process_name}\n")

        thread = Thread(target=threadFunc4())
        thread.start()

    def selectEvaluate(self):
        """
        选择评价类型触发器
        :return:
        """

        def threadFunc5():
            evaluate_type = self.ui.comboBox_3.currentText()
            if evaluate_type != '':
                self.ms.text_print.emit(self.ui.textBrowser, f"已选评价类型：{evaluate_type}\n")

        thread = Thread(target=threadFunc5())
        thread.start()

    def evaluate_to_thread(self):
        """
        执行评价
        :return:
        """
        self.my_thread.process_name = self.ui.comboBox.currentText()
        self.my_thread.class_name = self.ui.comboBox_2.currentText()
        self.my_thread.evaluate_type = self.ui.comboBox_3.currentText()
        self.my_thread.evaluate_text = self.ui.lineEdit_4.text()
        self.my_thread.slot = self.ui.textBrowser
        self.my_thread.value = self.ui.progressBar
        self.my_thread.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('./Picture/Stats.ico'))
    stats = Stats()
    stats.ui.show()
    sys.exit(app.exec_())
