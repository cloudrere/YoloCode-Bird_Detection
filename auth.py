# auth.py
"""
================================================================================
用户认证模块
================================================================================
提供以下功能：
1. SQLite 本地数据库 —— 存储用户名、密码哈希值和盐值
2. SHA-256 + 随机盐值加密 —— 杜绝明文存储，防范彩虹表攻击
3. 登录界面 _LoginPage —— 用户名/密码输入、错误提示
4. 注册界面 _RegisterPage —— 含客户端校验（长度、一致性）
5. AuthDialog —— 统一认证窗口，内含 QStackedWidget 切换登录/注册页

数据库文件：项目根目录下的 users.db（首次运行自动创建）
密码安全：密码 = SHA-256(明文 + 16字节随机盐值)，数据库中永不存储明文密码
================================================================================
"""
import os
import sqlite3
import hashlib
import secrets
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QMessageBox,
    QStackedWidget, QGraphicsDropShadowEffect,
)

# 数据库文件路径 —— 与 auth.py 同目录
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db')


# ============================== 数据库操作 ==============================

def _connect():
    """建立数据库连接（每次操作后自动关闭，避免锁竞争）"""
    return sqlite3.connect(DB_PATH)


def init_db():
    """
    初始化数据库：创建 users 表（如果不存在）
    - id:        自增主键
    - username:  用户名（UNIQUE 约束，不允许重复）
    - password:  SHA-256 哈希值（64位十六进制字符串）
    - salt:      随机盐值（32位十六进制字符串）
    - created_at: 账号创建时间
    """
    with _connect() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            salt       TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime(\'now\',\'localtime\'))
        )''')
        conn.commit()


def _hash_password(password, salt=None):
    """
    对密码执行 SHA-256 哈希 + 盐值加密
    - 如果未提供盐值，自动生成 16 字节随机盐值（用于注册）
    - 如果提供了盐值，用同样盐值计算哈希（用于登录验证）
    - 返回值：(哈希字符串, 盐值字符串)
    """
    if salt is None:
        salt = secrets.token_hex(16)  # 生成 32 字符的随机十六进制盐值
    h = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return h, salt


def register_user(username, password):
    """
    注册新用户
    - 对密码进行加盐哈希后存储
    - 返回 True 表示注册成功
    - 返回 False 表示用户名已存在（SQLite IntegrityError）
    """
    h, salt = _hash_password(password)
    with _connect() as conn:
        try:
            conn.execute('INSERT INTO users (username, password, salt) VALUES (?,?,?)',
                         (username, h, salt))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # 用户名重复，违反 UNIQUE 约束
            return False


def verify_login(username, password):
    """
    验证登录
    - 从数据库取出该用户的哈希值和盐值
    - 用同样的盐值对输入密码做哈希
    - 比较两次哈希是否一致
    - 返回 True/False
    - 用户不存在时返回 False（不区分"用户不存在"和"密码错误"，防止用户名枚举攻击）
    """
    with _connect() as conn:
        row = conn.execute(
            'SELECT password, salt FROM users WHERE username=?', (username,)
        ).fetchone()
    if row is None:
        return False
    h, _ = _hash_password(password, row[1])
    return h == row[0]


# ============================== 全局样式表 ==============================
# 绿松石色系（teal）为品牌色，浅色渐变背景，圆角卡片布局
_AUTH_QSS = """
QDialog {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ECFDF5, stop:0.4 #F0FDFA, stop:0.7 #F8FAFC, stop:1 #F1F5F9);
}
QFrame#authCard {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 20px;
}
QLabel#birdIcon {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #14B8A6, stop:1 #0F766E);
    color: #FFFFFF;
    font-size: 34px;
    border-radius: 40px;
    min-width: 80px;
    max-width: 80px;
    min-height: 80px;
    max-height: 80px;
    qproperty-alignment: AlignCenter;
}
QLabel#authTitle {
    color: #0F172A;
    font-size: 20px;
    font-weight: bold;
    letter-spacing: 1px;
}
QLabel#authSubtitle {
    color: #94A3B8;
    font-size: 13px;
}
QLineEdit {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 12px 16px;
    color: #1E293B;
    font-size: 13px;
    min-height: 22px;
}
QLineEdit:focus {
    background: #FFFFFF;
    border: 2px solid #14B8A6;
    padding: 11px 15px;
}
QPushButton#authBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #14B8A6, stop:1 #0D9488);
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 12px 0px;
    font-size: 15px;
    font-weight: bold;
    min-height: 44px;
    letter-spacing: 2px;
}
QPushButton#authBtn:hover { background-color: #0F766E; }
QPushButton#authBtn:pressed { background-color: #115E59; }
QPushButton#linkBtn {
    background: transparent;
    color: #0D9488;
    border: none;
    font-size: 12px;
    padding: 4px 0px;
    min-height: 20px;
}
QPushButton#linkBtn:hover { color: #0F766E; }
QLabel#errorLabel {
    color: #DC2626;
    font-size: 12px;
}
"""


# ============================== 登录页面 ==============================
class _LoginPage(QWidget):
    """
    登录页面组件
    - 包含 🦅 图标、标题、用户名/密码输入框、登录按钮、注册跳转链接
    - 回车键在密码框中可直接触发登录
    - 登录验证通过后调用 on_login 回调
    """
    def __init__(self, on_login, on_goto_register, parent=None):
        super().__init__(parent)
        self._on_login = on_login
        self._on_goto_register = on_goto_register

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch(1)

        # 🦅 品牌图标
        icon = QLabel('\U0001F985')
        icon.setObjectName('birdIcon')
        layout.addWidget(icon, 0, Qt.AlignCenter)
        layout.addSpacing(16)

        # 系统标题
        title = QLabel('鸟类智能检测系统')
        title.setObjectName('authTitle')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 副标题
        subtitle = QLabel('基于 YOLOv8 深度学习')
        subtitle.setObjectName('authSubtitle')
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        layout.addSpacing(24)

        # 用户名输入框
        self.ed_user = QLineEdit()
        self.ed_user.setPlaceholderText('用户名')
        layout.addWidget(self.ed_user)
        layout.addSpacing(10)

        # 密码输入框（掩码显示，回车触发登录）
        self.ed_pass = QLineEdit()
        self.ed_pass.setPlaceholderText('密码')
        self.ed_pass.setEchoMode(QLineEdit.Password)
        self.ed_pass.returnPressed.connect(self._handle_login)
        layout.addWidget(self.ed_pass)
        layout.addSpacing(8)

        # 错误提示标签（初始隐藏，仅登录失败时显示）
        self.lb_error = QLabel('')
        self.lb_error.setObjectName('errorLabel')
        self.lb_error.setAlignment(Qt.AlignCenter)
        self.lb_error.setMinimumHeight(20)
        layout.addWidget(self.lb_error)
        layout.addSpacing(4)

        # 登录按钮
        btn_login = QPushButton('登 录')
        btn_login.setObjectName('authBtn')
        btn_login.clicked.connect(self._handle_login)
        layout.addWidget(btn_login)
        layout.addSpacing(16)

        # 切换到注册页的链接
        btn_reg = QPushButton('没有账号？立即注册')
        btn_reg.setObjectName('linkBtn')
        btn_reg.clicked.connect(self._on_goto_register)
        layout.addWidget(btn_reg, 0, Qt.AlignCenter)

        layout.addStretch(1)

    def _handle_login(self):
        """处理登录：校验输入 → 数据库验证 → 回调或显示错误"""
        username = self.ed_user.text().strip()
        password = self.ed_pass.text()
        if not username or not password:
            self.lb_error.setText('请输入用户名和密码')
            return
        if verify_login(username, password):
            self.lb_error.setText('')
            self._on_login(username)
        else:
            self.lb_error.setText('用户名或密码错误')

    def clear_fields(self):
        """清空所有输入字段（切换到注册页后回调）"""
        self.ed_user.clear()
        self.ed_pass.clear()
        self.lb_error.setText('')


# ============================== 注册页面 ==============================
class _RegisterPage(QWidget):
    """
    注册页面组件
    - 含用户名、密码、确认密码三个输入框
    - 客户端校验：用户名 3-20 字符、密码 ≥6 位、两次密码一致
    - 注册成功后弹出提示并自动跳转回登录页
    """
    def __init__(self, on_register, on_goto_login, parent=None):
        super().__init__(parent)
        self._on_register = on_register
        self._on_goto_login = on_goto_login

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch(1)

        icon = QLabel('\U0001F985')
        icon.setObjectName('birdIcon')
        layout.addWidget(icon, 0, Qt.AlignCenter)
        layout.addSpacing(16)

        title = QLabel('创建账号')
        title.setObjectName('authTitle')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel('加入鸟类智能检测系统')
        subtitle.setObjectName('authSubtitle')
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        layout.addSpacing(24)

        # 用户名（提示长度限制）
        self.ed_user = QLineEdit()
        self.ed_user.setPlaceholderText('用户名（3-20个字符）')
        layout.addWidget(self.ed_user)
        layout.addSpacing(10)

        # 密码（提示最小长度）
        self.ed_pass = QLineEdit()
        self.ed_pass.setPlaceholderText('密码（至少6位）')
        self.ed_pass.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.ed_pass)
        layout.addSpacing(10)

        # 确认密码
        self.ed_confirm = QLineEdit()
        self.ed_confirm.setPlaceholderText('确认密码')
        self.ed_confirm.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.ed_confirm)
        layout.addSpacing(8)

        self.lb_error = QLabel('')
        self.lb_error.setObjectName('errorLabel')
        self.lb_error.setAlignment(Qt.AlignCenter)
        self.lb_error.setMinimumHeight(20)
        layout.addWidget(self.lb_error)
        layout.addSpacing(4)

        btn_reg = QPushButton('注 册')
        btn_reg.setObjectName('authBtn')
        btn_reg.clicked.connect(self._handle_register)
        layout.addWidget(btn_reg)
        layout.addSpacing(16)

        # 返回登录页链接
        btn_back = QPushButton('已有账号？返回登录')
        btn_back.setObjectName('linkBtn')
        btn_back.clicked.connect(self._on_goto_login)
        layout.addWidget(btn_back, 0, Qt.AlignCenter)

        layout.addStretch(1)

    def _handle_register(self):
        """处理注册：多层校验 → 数据库写入 → 跳转登录"""
        username = self.ed_user.text().strip()
        password = self.ed_pass.text()
        confirm = self.ed_confirm.text()

        # 客户端逐层校验，优先显示最具体的错误信息
        if not username or not password:
            self.lb_error.setText('请填写所有字段')
            return
        if len(username) < 3 or len(username) > 20:
            self.lb_error.setText('用户名需 3-20 个字符')
            return
        if len(password) < 6:
            self.lb_error.setText('密码至少 6 位')
            return
        if password != confirm:
            self.lb_error.setText('两次密码不一致')
            return

        if register_user(username, password):
            QMessageBox.information(self, '注册成功', '账号已创建，请返回登录')
            self._on_register()
        else:
            self.lb_error.setText('用户名已存在，请换一个')

    def clear_fields(self):
        """清空所有输入字段（切换到登录页后回调）"""
        self.ed_user.clear()
        self.ed_pass.clear()
        self.ed_confirm.clear()
        self.lb_error.setText('')


# ============================== 认证窗口（外壳） ==============================
class AuthDialog(QDialog):
    """
    统一的登录/注册对话框
    - 内含 QStackedWidget，第 0 页 = 登录，第 1 页 = 注册
    - 卡片式布局 + 轻微阴影效果
    - 登录成功后通过 accept() 关闭对话框，用户名通过 username() 方法获取
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('登录 — 鸟类智能检测系统')
        self.setFixedSize(420, 530)
        self.setStyleSheet(_AUTH_QSS)
        self._username = None  # 登录成功后设置

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        # 白色卡片容器
        card = QFrame()
        card.setObjectName('authCard')
        cv = QVBoxLayout(card)
        cv.setContentsMargins(36, 24, 36, 24)

        # 页面堆栈：0=登录, 1=注册
        self.stack = QStackedWidget()

        self.login_page = _LoginPage(
            on_login=self._on_login,
            on_goto_register=lambda: self.stack.setCurrentIndex(1),
        )
        self.register_page = _RegisterPage(
            on_register=lambda: (
                self.login_page.clear_fields(),
                self.stack.setCurrentIndex(0),
            ),
            on_goto_login=lambda: (
                self.register_page.clear_fields(),
                self.stack.setCurrentIndex(0),
            ),
        )

        self.stack.addWidget(self.login_page)     # index 0
        self.stack.addWidget(self.register_page)  # index 1
        cv.addWidget(self.stack, 1)
        layout.addWidget(card, 1)

        # 轻微阴影效果（增强层级感）
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 15))
        card.setGraphicsEffect(shadow)

    def _on_login(self, username):
        """登录成功回调：保存用户名并关闭对话框（返回 QDialog.Accepted）"""
        self._username = username
        self.accept()

    def username(self):
        """获取登录成功后的用户名（对话框关闭后由 main.py 调用）"""
        return self._username
