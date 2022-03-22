from datetime import datetime
from getpass import getuser

class Log:
    def __init__(self, path, project):
        self.project = project
        self.path = path
        self.errors_no = 0
        self.id = f'#{datetime.now().strftime("%y%m%d%H%M%S")}'
    def addLog(self, type, message, critical = False):
        self.string = f'{self.id},{datetime.now().strftime("%Y-%m-%d %H:%M:%S")},{type},{getuser()},{message},{self.project}'
        self.logUpdater()
        self.errors_no += 1
        if "ERROR" in self.string:
            if critical:
                exit()
    def logUpdater(self):
        with open(self.path, "a+") as logFile:
            logFile.write(f"{self.string}\n")