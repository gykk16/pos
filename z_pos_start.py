import configparser
import os
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *
from PyQt5 import uic

from z_pos.command_v5.v5_command import Command
from z_pos.common.SMILECON_CONTS import SmileconConsts
from z_pos.common.SMILECON_URL_CONSTS import SmileconUrlConsts
from z_pos.socket_control.socket_control import SocketControl
from z_pos.vo.pos_front_vo import PosFrontVO

# UI파일 연결
# 단, UI파일은 Python 코드 파일과 같은 디렉토리에 위치해야한다.

# form_class = uic.loadUiType("z_pos_start.ui")[0]
from z_pos.web_pos.web_pos_service import WebPosService

form_class = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'z_pos_start.ui'))[0]


# 화면을 띄우는데 사용되는 Class 선언
class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.POS_MODE = SmileconConsts.PosMode.POS_TCP
        self.SERVICE_MODE = SmileconConsts.ServiceMode.DEV_MODE

        self.DIV_LINE = '=====' * 33

        # config.ini 읽기
        self.basedir = os.path.dirname(__file__)  # 현재 디렉토리
        self.HOST = ''
        self.PORT = ''
        self.VERSION = '0005'
        self.WEB_HOST = ''
        self.WEB_POS_VER = SmileconConsts.ServiceType.WEB_POS_1_42

        # HOST, PORT 세팅
        self.initConfig()
        # ui 세팅
        self.initUI()
        # 버튼 초기화
        self.initButton()

        # 라디오 버트에 기능 연결
        self.radio_tcp.setChecked(True)
        self.radio_tcp.clicked.connect(self.radFunction)
        self.radio_web.clicked.connect(self.radFunction)

        # 버튼에 기능을 연결하는 코드
        self.btn_reset.clicked.connect(self.button1Function)  # 소켓 초기화
        self.btn_connect.clicked.connect(self.button2Function)  # 소켓 연결
        self.btn_disconnect.clicked.connect(self.button3Function)  # 소켓 닫기
        self.btn_cert.clicked.connect(self.button4Function)  # 인증 : 100
        self.btn_approve.clicked.connect(self.button5Function)  # 승인 : 101
        self.btn_cancel.clicked.connect(self.button6Function)  # 취소 : 102
        self.btn_clear.clicked.connect(self.button7Function)  # text browser clear
        self.btn_form_clear.clicked.connect(self.button8Function)  # text form clear

        # 입력창 변경(입력)시 연결하는 코드
        self.line_coupon_num.textChanged.connect(self.lineeditTextFunction)  # 쿠폰번호
        self.line_exchange_id.textChanged.connect(self.lineeditTextFunction)  # 브랜드ID
        self.line_branch_name.textChanged.connect(self.lineeditTextFunction)  # 지점명
        self.line_branch_code.textChanged.connect(self.lineeditTextFunction)  # 지점ID
        self.line_pos_code.textChanged.connect(self.lineeditTextFunction)  # 포스코드
        self.line_coupon_use_amt.textChanged.connect(self.lineeditTextFunction)  # 승인금액
        self.line_admit_num.textChanged.connect(self.lineeditTextFunction)  # 승인번호

        # 연결 상태 초기화
        self.reset_status = 0
        self.connect_status = 0

        self.socket_control = SocketControl()

        # 화면 입력 VO 초기화
        self.pos_front_vo = PosFrontVO()

        self.line_version.setDisabled(True)

    def initConfig(self):
        '''
        HOST , PORT 세팅
        :return:
        '''
        config = configparser.ConfigParser()
        config.read(os.path.join(self.basedir, 'config.ini'))

        self.HOST = config['CONFIG']['HOST']
        self.PORT = int(config['CONFIG']['PORT'])
        self.WEB_POS_VER = config['CONFIG']['WEBPOSVERSION']

        self.line_version.setText(self.VERSION)

    def initUI(self):
        '''
        ui 초기화
        :return:
        '''
        if self.HOST in SmileconConsts.ServiceMode.DEV_HOST:
            self.setWindowTitle('z_pos DEV')
            self.setWindowIcon(QIcon(os.path.join(self.basedir, 'logo_grey.ico')))
            self.service_type_label.setStyleSheet("background-color : #0e82ff")

            self.SERVICE_MODE = SmileconConsts.ServiceMode.DEV_MODE
            self.WEB_HOST = SmileconUrlConsts.DEV_HOST

        elif self.HOST in SmileconConsts.ServiceMode.PROD_HOST:
            self.setWindowTitle('z_pos')
            self.setWindowIcon(QIcon(os.path.join(self.basedir, 'logo.ico')))
            self.service_type_label.setStyleSheet("background-color : #ff557f")

            self.SERVICE_MODE = SmileconConsts.ServiceMode.PROD_MODE
            self.WEB_HOST = SmileconUrlConsts.PROD_HOST

        else:  # 호스트가 즐거운이 아니면 비확성화
            self.setWindowTitle('z_pos v5 DISABLED')
            self.setWindowIcon(QIcon(os.path.join(self.basedir, 'logo_grey.ico')))
            self.service_type_label.setStyleSheet("background-color : black")
            self.btn_reset.setEnabled(False)
            self.btn_clear.setEnabled(False)
            self.btn_form_clear.setEnabled(False)
            self.text_browser.append(f"==> HOST 확인!")

        # HOST , PORT 프린트
        self.text_browser.append(f"==> SERVICE MODE : {self.SERVICE_MODE} | POS MODE : {self.POS_MODE}")
        self.text_browser.append(f"==> HOST : {self.HOST} | PORT : {self.PORT}\n")

    def initButton(self):
        '''
        버튼 초기화
        :return:
        '''
        self.btn_reset.setEnabled(True)  # 연결 초기화
        self.btn_connect.setEnabled(False)  # 연결
        self.btn_disconnect.setEnabled(False)  # 연결 종료
        self.btn_cert.setEnabled(False)  # 인증(100)
        self.btn_approve.setEnabled(False)  # 승인(101)
        self.btn_cancel.setEnabled(False)  # 승인취소(102)
        self.btn_net_cancel.setEnabled(False)  # 승인 망 취소(103) : 사용안함

        if self.POS_MODE == SmileconConsts.PosMode.POS_WEB:
            self.btn_reset.setEnabled(False)
            self.btn_cert.setEnabled(True)

    ######################################################################################
    # 통신 연결
    ######################################################################################

    def button1Function(self):
        '''
        소켓 초기화
        :return:
        '''
        if self.connect_status == 0:
            self.socket_control = SocketControl()
        else:
            self.socket_control.close_socket()
            self.connect_status = 0

            self.socket_control = SocketControl()

        msg = "==> 통신 초기화"
        self.text_browser.append(msg)

        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(True)
        self.btn_cert.setEnabled(False)
        self.btn_approve.setEnabled(False)
        self.btn_cancel.setEnabled(False)

        self.connect_status = 0

    def button2Function(self):
        '''
        소켓 연결
        :return:
        '''
        if self.connect_status == 0:
            msg = self.socket_control.connect_socket(self.text_browser, self.HOST, self.PORT)
            print(msg)
            print(self.socket_control.cli_socket)
            if msg == 0:
                self.btn_cert.setEnabled(True)  # 연결시 인증 버튼 활성화
                self.connect_status = 1
            else:
                print("!!!!!!!")
                self.text_browser.append('==> 연결 실패')

        else:
            self.text_browser.append('==> 이미 연결되었습니다.')

    def button3Function(self):
        '''
        소켓 종료
        :return:
        '''
        self.socket_control.close_socket()
        self.connect_status = 0
        msg = "==> 연결 종료"
        self.text_browser.append(msg)

        self.initButton()

    ######################################################################################
    # 인증, 승인, 승인 취소
    ######################################################################################
    def button4Function(self):
        '''
        인증(100)
        :return:
        '''
        if self.POS_MODE == SmileconConsts.PosMode.POS_TCP:
            self._tcp_cert()
        elif self.POS_MODE == SmileconConsts.PosMode.POS_WEB:
            self.text_browser.append('==> 웹POS 인증')
            self._web_cert()
        else:
            self.text_browser.append('==> 잘못된 POS MODE!!')

    def button5Function(self):
        '''
        승인(101)
        :return:
        '''
        if self.POS_MODE == SmileconConsts.PosMode.POS_TCP:
            self._tcp_aprv()
        elif self.POS_MODE == SmileconConsts.PosMode.POS_WEB:
            self.text_browser.append('==> 웹POS 승인')
            self._web_aprv()
        else:
            self.text_browser.append('==> 잘못된 POS MODE!!')

    def button6Function(self):
        '''
        승인취소(102)
        :return:
        '''
        if self.POS_MODE == SmileconConsts.PosMode.POS_TCP:
            self._tcp_cncl()
        elif self.POS_MODE == SmileconConsts.PosMode.POS_WEB:
            self.text_browser.append('==> 웹POS 승인 취소')
            self._web_cncl()
        else:
            self.text_browser.append('==> 잘못된 POS MODE!!')

    ######################################################################################
    # 기타
    ######################################################################################
    def button7Function(self):
        '''
        로그창 지우기
        :return:
        '''
        if self.POS_MODE == SmileconConsts.PosMode.POS_TCP:
            self.text_browser.clear()
            self.text_browser.append(f"==> SERVICE MODE : {self.SERVICE_MODE} | POS MODE : {self.POS_MODE}")
            self.text_browser.append(f"==> HOST : {self.HOST} | PORT : {self.PORT}\n")
        elif self.POS_MODE == SmileconConsts.PosMode.POS_WEB:
            self.text_browser.clear()
            self.text_browser.append(f"==> SERVICE MODE : {self.SERVICE_MODE} | POS MODE : {self.POS_MODE}")
            self.text_browser.append(f"==> HOST : {self.WEB_HOST} \n")
        else:
            self.text_browser.clear()

    def button8Function(self):
        '''
        입력창 지우기
        :return:
        '''
        self.line_coupon_num.clear()
        self.line_exchange_id.clear()
        self.line_branch_name.clear()
        self.line_branch_code.clear()
        self.line_pos_code.clear()
        self.line_coupon_use_amt.clear()
        self.line_admit_num.clear()

    def lineeditTextFunction(self):
        '''
        입력 받은 값 VO에 담기
        :return:
        '''
        self.pos_front_vo.coupon_num = self.line_coupon_num.text()
        self.pos_front_vo.exchange_id = self.line_exchange_id.text().upper()
        self.pos_front_vo.branch_name = self.line_branch_name.text()
        self.pos_front_vo.branch_code = self.line_branch_code.text()
        self.pos_front_vo.pos_code = self.line_pos_code.text()
        self.pos_front_vo.coupon_use_amt = self.line_coupon_use_amt.text()
        self.pos_front_vo.admit_num = self.line_admit_num.text()

    def radFunction(self):
        '''
        라디오 버튼 클릭시
        :return:
        '''
        if self.radio_tcp.isChecked():
            self.line_pos_code.setEnabled(True)
            self.POS_MODE = SmileconConsts.PosMode.POS_TCP
            self.VERSION = '0005'
            self.line_version.setText(self.VERSION)

            self.text_browser.clear()
            self.text_browser.append(f"==> SERVICE MODE : {self.SERVICE_MODE} | POS MODE : {self.POS_MODE}")
            self.text_browser.append(f"==> HOST : {self.HOST} | PORT : {self.PORT}\n")

            self.initButton()

            print(f"==> POS MODE : TCP/IP")
        elif self.radio_web.isChecked():
            self.line_pos_code.setDisabled(True)
            self.POS_MODE = SmileconConsts.PosMode.POS_WEB
            self.VERSION = self.WEB_POS_VER
            self.line_version.setText(self.VERSION)

            self.text_browser.clear()
            self.text_browser.append(f"==> SERVICE MODE : {self.SERVICE_MODE} | POS MODE : {self.POS_MODE}")
            self.text_browser.append(f"==> HOST : {self.WEB_HOST} \n")

            self.initButton()

            print(f"==> POS MODE : WEB")

    ######################################################################################
    # 서비스
    ######################################################################################
    def _tcp_cert(self):
        print('=' * 100 + '\nSTART 100!!')
        self.text_browser.append(self.DIV_LINE)

        msg = "==> 100 : 인증"
        self.text_browser.append(msg)

        cmd = Command()
        success, parser = cmd.action_100(self.text_browser, self.socket_control, self.pos_front_vo)

        if success > 0:

            if parser.status_code == "001":
                print('STATUS CODE : 001')
                self.text_browser.append(f"==> ERROR_CODE      : {parser.error_code} | ERROR_MESSAGE : {parser.error_message}")
            elif parser.status_code == "000":
                print('STATUS CODE : 000')
                # self.text_browser.append(f"==> STATUS_CODE     : {parser.status_code}")

        else:
            self.text_browser.append(f"==> 오류 발생!!")

        self.text_browser.append(self.DIV_LINE)

        self.btn_approve.setEnabled(True)
        self.btn_cancel.setEnabled(True)

        print('END 100!!\n' + '=' * 100)

    def _tcp_aprv(self):
        print('=' * 100 + '\nSTART 101!!')
        self.text_browser.append(self.DIV_LINE)
        msg = "==> 101 : 승인"
        self.text_browser.append(msg)

        cmd = Command()
        success, parser = cmd.action_101(self.text_browser, self.socket_control, self.pos_front_vo)

        if success > 0:

            if parser.status_code == "001":
                print('STATUS CODE : 001')
                self.text_browser.append(f"==> ERROR_CODE      : {parser.error_code} | ERROR_MESSAGE : {parser.error_message}")
            elif parser.status_code == "000":
                print('STATUS CODE : 000')
                # self.text_browser.append(f"==> STATUS_CODE     : {parser.status_code}")
                # self.text_browser.append(f"==> ADMIT_NUM       : {parser.admit_num}")
                self.line_admit_num.setText(parser.admit_num)

        self.btn_approve.setEnabled(False)
        self.btn_cancel.setEnabled(False)

        self.text_browser.append(self.DIV_LINE)

        print('END 101!!\n' + '=' * 100)

    def _tcp_cncl(self):
        print('=' * 100 + '\nSTART 102!!')
        self.text_browser.append(self.DIV_LINE)
        msg = "==> 102 : 승인취소"
        self.text_browser.append(msg)

        cmd = Command()
        success, parser = cmd.action_102(self.text_browser, self.socket_control, self.pos_front_vo)

        if success > 0:

            if parser.status_code == "001":
                print('STATUS CODE : 001')
                self.text_browser.append(f"==> ERROR_CODE      : {parser.error_code} | ERROR_MESSAGE : {parser.error_message}")
            elif parser.status_code == "000":
                print('STATUS CODE : 000')
                # self.text_browser.append(f"==> STATUS_CODE     : {parser.status_code}")

        self.btn_approve.setEnabled(False)
        self.btn_cancel.setEnabled(False)

        self.text_browser.append(self.DIV_LINE)

        print('END 102!!\n' + '=' * 100)

    def _get_web_params(self):
        p = {}
        return p

    def _web_cert(self):

        print("==> 웹POS 인증")

        cert_data = WebPosService(self.SERVICE_MODE, self.text_browser).web_pos_cert(self._get_web_params())

        self.text_browser.append('')
        self.btn_approve.setEnabled(True)
        self.btn_cancel.setEnabled(True)

    def _web_aprv(self):

        print("==> 웹POS 승인")

        aprv_data = WebPosService(self.SERVICE_MODE, self.text_browser).web_pos_aprv(None, self._get_web_params())

        self.line_admit_num.setText(aprv_data.result_data_vo.exchange_num)

        self.text_browser.append('')
        self.btn_approve.setEnabled(False)
        self.btn_cancel.setEnabled(False)

    def _web_cncl(self):

        print("==> 웹POS 승인취소")

        cncl_data = WebPosService(self.SERVICE_MODE, self.text_browser).web_pos_cncl(None, self._get_web_params())

        self.text_browser.append('')
        self.btn_approve.setEnabled(False)
        self.btn_cancel.setEnabled(False)


if __name__ == "__main__":
    # QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv)

    # WindowClass의 인스턴스 생성
    myWindow = WindowClass()

    # 프로그램 화면을 보여주는 코드
    myWindow.show()

    # 프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()
