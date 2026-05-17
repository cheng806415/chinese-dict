import random

from src.utils.qt_compat import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, Qt, pyqtSignal,
    QFont, ALIGN_CENTER, FONT_WEIGHT_BOLD
)
from src.utils.font import get_font


class QuizDialog(QDialog):
    quiz_finished = pyqtSignal(int, int)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("测验模式")
        self.setMinimumSize(500, 350)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #333;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #1976d2;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)

        self.questions = []
        self.current_index = 0
        self.score = 0
        self.mode = "word"
        self.current_word = None

        self._setup_ui()
        self._load_questions()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        self.title_label = QLabel("测验模式")
        self.title_label.setFont(get_font(16, FONT_WEIGHT_BOLD))
        self.title_label.setAlignment(ALIGN_CENTER)
        layout.addWidget(self.title_label)

        self.progress_label = QLabel("第 1 / 10 题")
        self.progress_label.setFont(get_font(11))
        self.progress_label.setAlignment(ALIGN_CENTER)
        layout.addWidget(self.progress_label)

        self.score_label = QLabel("得分: 0")
        self.score_label.setFont(get_font(11))
        self.score_label.setAlignment(ALIGN_CENTER)
        layout.addWidget(self.score_label)

        self.question_label = QLabel("题目加载中...")
        self.question_label.setFont(get_font(14))
        self.question_label.setAlignment(ALIGN_CENTER)
        self.question_label.setWordWrap(True)
        layout.addWidget(self.question_label)

        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("请输入答案...")
        self.answer_input.setFont(get_font(13))
        self.answer_input.returnPressed.connect(self._on_submit)
        layout.addWidget(self.answer_input)

        btn_layout = QHBoxLayout()
        self.submit_btn = QPushButton("提交")
        self.submit_btn.clicked.connect(self._on_submit)
        btn_layout.addWidget(self.submit_btn)

        self.skip_btn = QPushButton("跳过")
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        self.skip_btn.clicked.connect(self._on_skip)
        btn_layout.addWidget(self.skip_btn)
        layout.addLayout(btn_layout)

        self.feedback_label = QLabel("")
        self.feedback_label.setFont(get_font(12))
        self.feedback_label.setAlignment(ALIGN_CENTER)
        layout.addWidget(self.feedback_label)

        layout.addStretch()

    def _load_questions(self):
        count = self.db.get_word_count()
        if count == 0:
            QMessageBox.information(self, "测验", "词典暂无数据，无法进行测验")
            self.reject()
            return
        num = min(10, count)
        offsets = random.sample(range(count), num)
        for offset in offsets:
            self.db.cursor.execute("SELECT * FROM words LIMIT 1 OFFSET ?", (offset,))
            row = self.db.cursor.fetchone()
            if row:
                self.questions.append(self.db._format_result(dict(row)))
        if not self.questions:
            QMessageBox.information(self, "测验", "无法加载题目")
            self.reject()
            return
        self._show_question()

    def _show_question(self):
        if self.current_index >= len(self.questions):
            self._finish_quiz()
            return
        self.current_word = self.questions[self.current_index]
        self.mode = random.choice(["word", "pinyin"])
        if self.mode == "word":
            definition = self.current_word.get("definition_cn", "") or self.current_word.get("definition", "")
            self.question_label.setText(f"释义: {definition}\n\n请写出对应的词语:")
        else:
            word = self.current_word.get("simplified", "")
            self.question_label.setText(f"词语: {word}\n\n请写出对应的拼音:")
        self.progress_label.setText(f"第 {self.current_index + 1} / {len(self.questions)} 题")
        self.answer_input.clear()
        self.feedback_label.setText("")
        self.answer_input.setFocus()

    def _on_submit(self):
        answer = self.answer_input.text().strip()
        if not answer:
            self.feedback_label.setText("请输入答案")
            return
        correct = False
        if self.mode == "word":
            correct_word = self.current_word.get("simplified", "")
            correct_trad = self.current_word.get("traditional", "")
            if answer == correct_word or answer == correct_trad:
                correct = True
        else:
            correct_pinyin = self.current_word.get("pinyin", "").replace(" ", "").lower()
            if answer.replace(" ", "").lower() == correct_pinyin:
                correct = True
        if correct:
            self.score += 1
            self.feedback_label.setText("<span style='color:green;'>正确!</span>")
        else:
            correct_answer = self.current_word.get("simplified", "") if self.mode == "word" else self.current_word.get("pinyin", "")
            self.feedback_label.setText(f"<span style='color:red;'>错误! 正确答案是: {correct_answer}</span>")
        self.score_label.setText(f"得分: {self.score}")
        self.current_index += 1
        self._show_question()

    def _on_skip(self):
        correct_answer = self.current_word.get("simplified", "") if self.mode == "word" else self.current_word.get("pinyin", "")
        self.feedback_label.setText(f"跳过! 正确答案是: {correct_answer}")
        self.current_index += 1
        self._show_question()

    def _finish_quiz(self):
        total = len(self.questions)
        self.quiz_finished.emit(self.score, total)
        if total > 0:
            rate = self.score * 100 // total
            QMessageBox.information(
                self, "测验完成",
                f"测验完成!\n得分: {self.score} / {total}\n正确率: {rate}%"
            )
        else:
            QMessageBox.information(self, "测验完成", "测验完成!")
        self.accept()
