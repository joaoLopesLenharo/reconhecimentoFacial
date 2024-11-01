# app.py
from PyQt5.QtWidgets import QApplication
from interface import MainWindow  # Altere para a classe que inicia sua interface
from database import Database

def main():
    app = QApplication([])
    db = Database()  # Inicie o banco de dados aqui
    main_window = MainWindow(db)  # Altere para usar MainWindow
    main_window.show()
    app.exec_()

if __name__ == "__main__":
    main()
