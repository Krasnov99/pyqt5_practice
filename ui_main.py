from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLineEdit, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QSplitter, QCalendarWidget, QTimeEdit, QComboBox
)
from PyQt5.QtCore import Qt, QDate, QTime
from PyQt5.QtGui import QPixmap, QImage, QColor
from PIL import Image
import database

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Календарь событий (PyQt5 Practice)")
        self.resize(1100, 700)
        self.setMinimumSize(900, 600)
        
        self.db = database.DatabaseManager()
        self.db.init_db()
        self.current_image_path = ""
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self._setup_ui()
        self._bind_signals()
        
        # Установка текущей даты
        self.calendar.setSelectedDate(QDate.currentDate())
        self._refresh_table()

    def _setup_ui(self):
        main_layout = QHBoxLayout()
        self.centralWidget().setLayout(main_layout)

        # === ЛЕВАЯ ПАНЕЛЬ: Календарь и Таблица ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        left_layout.addWidget(self.calendar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Время", "Название", "Тип", "Заметки"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        left_layout.addWidget(self.table)

        # === ПРАВАЯ ПАНЕЛЬ: Форма ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        self.le_title = QLineEdit()
        self.te_time = QTimeEdit()
        self.te_time.setDisplayFormat("HH:mm")
        
        self.cb_type = QComboBox()
        self.cb_type.addItems(["Встреча", "Праздник", "Дедлайн", "Личное"])
        
        self.le_notes = QLineEdit()
        
        form_layout.addRow("Название:", self.le_title)
        form_layout.addRow("Время:", self.te_time)
        form_layout.addRow("Тип:", self.cb_type)
        form_layout.addRow("Заметки:", self.le_notes)
        right_layout.addWidget(form_widget)
        
        self.lbl_image = QLabel("Фото мероприятия")
        self.lbl_image.setAlignment(Qt.AlignCenter)
        self.lbl_image.setMinimumHeight(200)
        self.lbl_image.setStyleSheet("background-color: #f5f5f5; border: 2px dashed #bbb; border-radius: 8px;")
        right_layout.addWidget(self.lbl_image)
        
        self.btn_load_img = QPushButton("Загрузить фото")
        right_layout.addWidget(self.btn_load_img)
        
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Добавить")
        self.btn_edit = QPushButton("Изменить")
        self.btn_delete = QPushButton("Удалить")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        right_layout.addLayout(btn_layout)
        
        right_layout.addStretch()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 400])
        main_layout.addWidget(splitter)

    def _bind_signals(self):
        self.calendar.selectionChanged.connect(self._refresh_table)
        self.btn_add.clicked.connect(self._on_add)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_load_img.clicked.connect(self._on_load_image)
        self.table.itemSelectionChanged.connect(self._on_select_row)

    def _validate_input(self, event_id=None):
        """Валидация полей и проверка пересечений"""
        if not self.le_title.text().strip():
            QMessageBox.warning(self, "Ошибка", "Поле 'Название' обязательно.")
            return False
            
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        selected_time = self.te_time.time().toString("HH:mm")
        
        # Проверка пересечений
        if self.db.check_overlap(selected_date, selected_time, event_id):
            QMessageBox.warning(self, "Ошибка", "На это время уже назначено событие!")
            return False
            
        return True

    def _on_add(self):
        if not self._validate_input():
            return
            
        data = {
            "date": self.calendar.selectedDate().toString("yyyy-MM-dd"),
            "title": self.le_title.text().strip(),
            "time": self.te_time.time().toString("HH:mm"),
            "type": self.cb_type.currentText(),
            "notes": self.le_notes.text().strip(),
            "image_path": self.current_image_path
        }
        self.db.insert_record(data)
        self._refresh_table()
        self._clear_fields()

    def _on_edit(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return
            
        row = selected[0].row()
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        
        if not self._validate_input(event_id=item_id):
            return
            
        data = {
            "id": item_id,
            "date": self.calendar.selectedDate().toString("yyyy-MM-dd"),
            "title": self.le_title.text().strip(),
            "time": self.te_time.time().toString("HH:mm"),
            "type": self.cb_type.currentText(),
            "notes": self.le_notes.text().strip(),
            "image_path": self.current_image_path
        }
        self.db.update_record(data)
        self._refresh_table()

    def _on_delete(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return
            
        if QMessageBox.question(self, "Подтверждение", "Удалить событие?") == QMessageBox.Yes:
            row = selected[0].row()
            item_id = self.table.item(row, 0).data(Qt.UserRole)
            self.db.delete_record(item_id)
            self._refresh_table()
            self._clear_fields()

    def _on_select_row(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            self._clear_fields()
            return
            
        row = selected[0].row()
        self.te_time.setTime(QTime.fromString(self.table.item(row, 0).text(), "HH:mm"))
        self.le_title.setText(self.table.item(row, 1).text())
        self.cb_type.setCurrentText(self.table.item(row, 2).text())
        self.le_notes.setText(self.table.item(row, 3).text())
        
        # Извлечение пути к фото (сохранен в UserRole колонки 1)
        img_path = self.table.item(row, 1).data(Qt.UserRole)
        self._display_image(img_path)

    def _on_load_image(self):
        """Интеграция Pillow: Загрузка и ресайз изображения"""
        path, _ = QFileDialog.getOpenFileName(self, "Выберите фото", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        self.current_image_path = path
        self._display_image(path)

    def _display_image(self, path):
        if not path:
            self.lbl_image.setText("Фото мероприятия")
            self.lbl_image.setPixmap(QPixmap())
            return
            
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((300, 200), Image.LANCZOS)
            qt_img = QImage(img.tobytes(), img.width, img.height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qt_img)
            self.lbl_image.setPixmap(pixmap)
        except Exception as e:
            pass

    def _refresh_table(self):
        """Обновление таблицы и применение цветовой маркировки"""
        self.table.setRowCount(0)
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        records = self.db.get_events_by_date(selected_date)
        
        type_colors = {
            "Встреча": QColor("#e3f2fd"),   # Голубой
            "Праздник": QColor("#fce4ec"),  # Розовый
            "Дедлайн": QColor("#ffebee"),   # Красный
            "Личное": QColor("#f1f8e9")     # Зеленый
        }
        
        for i, rec in enumerate(records):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(rec["time"]))
            self.table.setItem(i, 1, QTableWidgetItem(rec["title"]))
            self.table.setItem(i, 2, QTableWidgetItem(rec["type"]))
            self.table.setItem(i, 3, QTableWidgetItem(rec["notes"]))
            
            # Цветовая маркировка строк
            row_color = type_colors.get(rec["type"], QColor("#ffffff"))
            for j in range(4):
                self.table.item(i, j).setBackground(row_color)
            
            # Сохранение метаданных
            self.table.item(i, 0).setData(Qt.UserRole, rec["id"])
            self.table.item(i, 1).setData(Qt.UserRole, rec["image_path"])

    def _clear_fields(self):
        self.le_title.clear()
        self.le_notes.clear()
        self.te_time.setTime(QTime.currentTime())
        self.current_image_path = ""
        self.lbl_image.clear()
        self.lbl_image.setText("Фото мероприятия")

    def closeEvent(self, event):
        """Обязательное переопределение закрытия окна"""
        reply = QMessageBox.question(self, "Выход", "Вы уверены, что хотите выйти?", 
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.close()
            event.accept()
        else:
            event.ignore()
