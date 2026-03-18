import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget

app = QApplication(sys.argv)
ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

print("created:", ocx is not None)
print("OnEventConnect:", hasattr(ocx, "OnEventConnect"))
print("OnReceiveTrData:", hasattr(ocx, "OnReceiveTrData"))