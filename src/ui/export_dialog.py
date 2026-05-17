from src.utils.qt_compat import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QGroupBox, QFormLayout, QDialogButtonBox,
    QFileDialog, QMessageBox, QPushButton, QApplication,
    QPrinter, QPrintDialog,
)
from src.utils.font import get_font


class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出")
        self.setMinimumSize(400, 300)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["HTML", "Plain Text", "Markdown"])
        self.format_combo.setFont(get_font(10))
        form_layout.addRow("导出格式:", self.format_combo)

        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["当前词语", "收藏词汇", "单词本", "搜索历史"])
        self.scope_combo.setFont(get_font(10))
        form_layout.addRow("导出范围:", self.scope_combo)

        layout.addLayout(form_layout)

        include_group = QGroupBox("包含内容")
        include_group.setFont(get_font(10))
        include_layout = QVBoxLayout(include_group)

        self.include_pinyin = QCheckBox("拼音")
        self.include_pinyin.setChecked(True)
        self.include_pinyin.setFont(get_font(10))
        include_layout.addWidget(self.include_pinyin)

        self.include_definition = QCheckBox("释义")
        self.include_definition.setChecked(True)
        self.include_definition.setFont(get_font(10))
        include_layout.addWidget(self.include_definition)

        self.include_examples = QCheckBox("例句")
        self.include_examples.setChecked(False)
        self.include_examples.setFont(get_font(10))
        include_layout.addWidget(self.include_examples)

        layout.addWidget(include_group)

        layout.addStretch()

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.setFont(get_font(10))
        layout.addWidget(self.button_box)

    def get_export_config(self):
        return {
            "format": self.format_combo.currentText(),
            "scope": self.scope_combo.currentText(),
            "include_pinyin": self.include_pinyin.isChecked(),
            "include_definition": self.include_definition.isChecked(),
            "include_examples": self.include_examples.isChecked(),
        }


class ExportManager:
    def __init__(self, db, parent=None):
        self.db = db
        self.parent = parent

    def show_export_dialog(self):
        dialog = ExportDialog(self.parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_export_config()
            self._do_export(config)

    def _do_export(self, config):
        fmt = config["format"]
        scope = config["scope"]
        include_pinyin = config["include_pinyin"]
        include_definition = config["include_definition"]
        include_examples = config["include_examples"]

        words = self._get_words_for_scope(scope)
        if not words:
            QMessageBox.information(self.parent, "导出", "没有可导出的内容")
            return

        if fmt == "HTML":
            content = self._generate_html(words, include_pinyin, include_definition, include_examples)
            default_ext = ".html"
            file_filter = "HTML Files (*.html);;All Files (*)"
        elif fmt == "Plain Text":
            content = self._generate_text(words, include_pinyin, include_definition, include_examples)
            default_ext = ".txt"
            file_filter = "Text Files (*.txt);;All Files (*)"
        else:
            content = self._generate_markdown(words, include_pinyin, include_definition, include_examples)
            default_ext = ".md"
            file_filter = "Markdown Files (*.md);;All Files (*)"

        file_path, _ = QFileDialog.getSaveFileName(
            self.parent, "保存导出文件", f"export{default_ext}", file_filter
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self.parent, "导出", f"已成功导出到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self.parent, "导出失败", str(e))

    def _get_words_for_scope(self, scope):
        if scope == "当前词语":
            mw = self.parent
            if hasattr(mw, "_current_word") and mw._current_word:
                result = self.db.search_exact(mw._current_word)
                return [result] if result else []
            return []
        elif scope == "收藏词汇":
            return self.db.get_favorites(limit=500)
        elif scope == "单词本":
            return self.db.get_word_book_words(limit=500)
        elif scope == "搜索历史":
            history = self.db.get_search_history(limit=100)
            words = []
            for word in history:
                result = self.db.search_exact(word)
                if result:
                    words.append(result)
            return words
        return []

    def _generate_html(self, words, include_pinyin, include_definition, include_examples):
        lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '  <meta charset="UTF-8">',
            "  <title>词典导出</title>",
            "  <style>",
            "    body { font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; background: #f5f5f5; }",
            "    .word-card { background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
            "    .word-title { font-size: 24px; font-weight: bold; color: #1976d2; margin-bottom: 8px; }",
            "    .pinyin { font-size: 16px; color: #666; margin-bottom: 12px; }",
            "    .section { margin-bottom: 12px; }",
            "    .section-title { font-size: 14px; font-weight: bold; color: #333; margin-bottom: 6px; }",
            "    .section-content { font-size: 14px; line-height: 1.8; color: #555; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <h1 style='text-align:center;color:#333;'>词典导出</h1>",
        ]
        for w in words:
            lines.append('  <div class="word-card">')
            lines.append(f'    <div class="word-title">{self._escape_html(w.get("simplified", ""))}</div>')
            if include_pinyin and w.get("pinyin"):
                lines.append(f'    <div class="pinyin">{self._escape_html(w["pinyin"])}</div>')
            if include_definition:
                if w.get("definition_cn"):
                    lines.append('    <div class="section">')
                    lines.append('      <div class="section-title">中文释义</div>')
                    lines.append(f'      <div class="section-content">{self._escape_html(w["definition_cn"]).replace(chr(10), "<br>")}</div>')
                    lines.append('    </div>')
                if w.get("definition"):
                    lines.append('    <div class="section">')
                    lines.append('      <div class="section-title">英文释义</div>')
                    lines.append(f'      <div class="section-content">{self._escape_html(w["definition"]).replace(";", "<br>")}</div>')
                    lines.append('    </div>')
            if include_examples and w.get("examples"):
                lines.append('    <div class="section">')
                lines.append('      <div class="section-title">例句</div>')
                lines.append(f'      <div class="section-content">{self._escape_html(w["examples"]).replace(chr(10), "<br>")}</div>')
                lines.append('    </div>')
            lines.append('  </div>')
        lines.append("</body>")
        lines.append("</html>")
        return "\n".join(lines)

    def _generate_text(self, words, include_pinyin, include_definition, include_examples):
        lines = []
        lines.append("=" * 40)
        lines.append("词典导出")
        lines.append("=" * 40)
        lines.append("")
        for w in words:
            lines.append(f"词语: {w.get('simplified', '')}")
            if include_pinyin and w.get("pinyin"):
                lines.append(f"拼音: {w['pinyin']}")
            if include_definition:
                if w.get("definition_cn"):
                    lines.append("中文释义:")
                    for line in w["definition_cn"].split("\n"):
                        lines.append(f"  {line}")
                if w.get("definition"):
                    lines.append("英文释义:")
                    for line in w["definition"].split(";"):
                        lines.append(f"  {line.strip()}")
            if include_examples and w.get("examples"):
                lines.append("例句:")
                for line in w["examples"].split("\n"):
                    lines.append(f"  {line}")
            lines.append("-" * 40)
            lines.append("")
        return "\n".join(lines)

    def _generate_markdown(self, words, include_pinyin, include_definition, include_examples):
        lines = []
        lines.append("# 词典导出")
        lines.append("")
        for w in words:
            lines.append(f"## {w.get('simplified', '')}")
            lines.append("")
            if include_pinyin and w.get("pinyin"):
                lines.append(f"**拼音:** {w['pinyin']}")
                lines.append("")
            if include_definition:
                if w.get("definition_cn"):
                    lines.append("### 中文释义")
                    lines.append("")
                    for line in w["definition_cn"].split("\n"):
                        lines.append(f"- {line}")
                    lines.append("")
                if w.get("definition"):
                    lines.append("### 英文释义")
                    lines.append("")
                    for line in w["definition"].split(";"):
                        lines.append(f"- {line.strip()}")
                    lines.append("")
            if include_examples and w.get("examples"):
                lines.append("### 例句")
                lines.append("")
                for line in w["examples"].split("\n"):
                    lines.append(f"> {line}")
                lines.append("")
            lines.append("---")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _escape_html(text):
        if not text:
            return ""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))

    def print_current(self, word, pinyin, definition, definition_cn):
        printer = QPrinter()
        dialog = QPrintDialog(printer, self.parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        document = self._generate_print_html(word, pinyin, definition, definition_cn)
        text_edit = self.parent.search_result_view if hasattr(self.parent, "search_result_view") else None
        if text_edit:
            text_edit.print(printer)
        else:
            from src.utils.qt_compat import QTextEdit
            te = QTextEdit()
            te.setHtml(document)
            te.print(printer)

    @staticmethod
    def _generate_print_html(word, pinyin, definition, definition_cn):
        sections = ""
        if definition_cn:
            sections += f"""
            <div style="margin-bottom: 16px;">
                <h3 style="color: #1976d2; font-size: 16px; margin: 0 0 8px 0; padding: 4px 8px; background-color: #e3f2fd; border-radius: 4px;">中文释义</h3>
                <p style="font-size: 14px; line-height: 1.8; color: #333; margin: 0; padding-left: 8px;">
                    {definition_cn.replace(chr(10), '<br/>')}
                </p>
            </div>
            """
        if definition:
            sections += f"""
            <div style="margin-bottom: 16px;">
                <h3 style="color: #6a1b9a; font-size: 16px; margin: 0 0 8px 0; padding: 4px 8px; background-color: #f3e5f5; border-radius: 4px;">英文释义</h3>
                <p style="font-size: 14px; line-height: 1.8; color: #333; margin: 0; padding-left: 8px;">
                    {definition.replace(';', '<br/>• ')}
                </p>
            </div>
            """
        if not sections:
            sections = '<p style="font-size: 14px; color: #666;">暂无释义</p>'

        pinyin_html = f' <span style="font-size: 16px; color: #666;">{pinyin}</span>' if pinyin else ""
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>{word}</title></head>
        <body style="font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; padding: 20px;">
            <h2 style="color: #1976d2; margin: 0;">{word}{pinyin_html}</h2>
            <hr style="border: none; border-top: 2px solid #dee2e6; margin: 12px 0;">
            {sections}
        </body>
        </html>
        """
