import os, sys, subprocess, platform, fileinput, json, argparse

DEBUG = False


class Utils:
    columns = 100
    row = 1000

    def __init__(self):
        if (platform.system() != 'Windows'):
            try:
                rows, columns = os.popen('stty size', 'r').read().split()
                self.columns = int(columns)
            except:
                self.columns = 100
                if DEBUG:
                    print("Could not get terminal size")

    def printFullTerm(self, color, string):
        value = int(self.columns / 2 - len(string) / 2)
        self.printColor(color, "-" * value, eol='')
        self.printColor(color, string, eol='')
        value += len(string)
        self.printColor(color, "-" * (self.columns - value))
        return 0

    def changeDirectory(self, path):
        if DEBUG:
            print("Moving to : " + path)
        os.chdir(path)
        if DEBUG:
            print("Current directory : " + str(os.getcwd()))
        return 0

    def replacePatternInFile(self, pattern, replace, file_path):
        try:
            with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
                for line in file:
                    print(line.replace(pattern, replace), end='')
        except:
            return 1
        return 0

    def printColor(self, color, message, file=sys.stdout, eol=os.linesep):
        if (self.system == 'Windows'):
            print(message, file=file, end=eol)
        else:
            print(color + message + Colors.ENDC, file=file, end=eol)
        return 0

'''
    Python installer class
'''


class Installer(Utils):
    path = os.path.realpath(__file__)
    path_dir = os.path.dirname(os.path.realpath(__file__)) + os.sep
    python_path = sys.executable
    python_version = sys.version_info
    system = platform.system()

    commands = []
    commandMatcher = {}
    bin_dir = ""
    venv_pip = ""
    venv_bin = ""
    venv = ""
    requirements = ""

    current_command = "default"
    yes_no_questions = {}
    commands_list = []
    to_print = []
    executed = {}
    errors = {}

    def __init__(self, config):
        super(Installer, self).__init__()
        self.config = config
        self.commands = self.config.getCommandList()
        self.venv = self.config.getPath() + os.sep + self.config.getEnv()
        self.requirements = self.config.getReq()
        self.adaptInstaller()
        os.chdir(self.path_dir)

    def adaptInstaller(self):
        self.commandMatcher = self.config.getCommands()
        config = self.config.getConfig()
        if self.system == 'Windows':
            self.bin_dir = "Scripts"
        else:
            self.bin_dir = "bin"
        self.venv_pip = config["path"] + os.sep + config["env"] + os.sep + self.bin_dir + os.sep + "pip.exe"
        self.venv_bin = config["path"] + os.sep + config["env"] + os.sep + self.bin_dir + os.sep + "python.exe"

    '''
        Functions parameters
    '''
    def createConfig(self):
        configuration = self.config.createConfigFile()
        try:
            with open(self.config.getConfigFile(), "w") as f:
                f.write(json.dumps(configuration, sort_keys=True, indent=4))
        except Exception as e:
            print(e, file=sys.stderr)
            self.errors[self.current_command] = []
            return 1
        self.executed[self.current_command] = []
        return 0

    # def install(self):
    #     if (self.execProcess("pip install --upgrade pip")):
    #         return 1
    #     if (self.execProcess("pip install virtualenv --upgrade")):
    #         return 1
    #     self.changeDirectory("..")
    #     if (not os.path.isdir("venv")):
    #         self.execProcess("virtualenv venv" + " -p " + self.python_path)
    #     else:
    #         self.printFullTerm(Colors.WARNING, "Virtual environment already exist")
    #     self.changeDirectory(self.path_dir)
    #     ret = self.installDatabase()
    #     if (ret):
    #         return ret
    #     return self.update()
    #
    # def update(self):
    #     if (self.execProcessFromVenv(self.venv_pip + " install --upgrade pip") or
    #         self.execProcessFromVenv(self.venv_pip + " install --upgrade wheel") or
    #         self.execProcessFromVenv(self.venv_pip + " install -r " + self.requirements)):
    #         return 1
    #     return self.updateDatabase()
    #
    # def installDatabase(self):
    #     return 0
    #
    # def updateDatabase(self):
    #     context = os.getcwd()
    #     self.changeDirectory("../src/")
    #     if (self.execProcessFromVenv(self.venv_bin + self.manage + " makemigrations") or
    #         self.execProcessFromVenv(self.venv_bin + self.manage + " migrate") or
    #         self.execProcessFromVenv(self.venv_bin + self.manage + " loaddata misc/fixtures/initial_content.json")):
    #         return 1
    #     self.changeDirectory(context)
    #     return 0

    '''
        UTILS FUNCTIONS
    '''
    def setConfig(self, config):
        self.config = config

    def execProcess(self, command):
        self.printFullTerm(Colors.BLUE, "Executing command [" + command + "]")
        process = subprocess.Popen(command, shell=True)
        process.wait()
        if process.returncode == 0:
            self.printFullTerm(Colors.GREEN, "Process executed successfully")
            if (self.current_command in self.executed):
                self.executed[self.current_command].append(command)
            else:
                self.executed[self.current_command] = [command]
        else:
            self.printFullTerm(Colors.WARNING, "Process execution failed")
            if (self.current_command in self.errors):
                self.errors[self.current_command].append(command)
            else:
                self.errors[self.current_command] = [command]
        return process.returncode

    def execProcessFromVenv(self, command):
        args = command.split()
        self.printFullTerm(Colors.BLUE, "Executing command from venv [" + str(' '.join(args[1:])) + "]")
        process = subprocess.Popen(args)
        process.wait()
        if process.returncode == 0:
            self.printFullTerm(Colors.GREEN, "Process executed successfully")
            if (self.current_command in self.executed):
                self.executed[self.current_command].append(str(' '.join(args[1:])))
            else:
                self.executed[self.current_command] = [str(' '.join(args[1:]))]
        else:
            self.printFullTerm(Colors.WARNING, "Process execution failed")
            if (self.current_command in self.errors):
                self.errors[self.current_command].append(str(' '.join(args[1:])))
            else:
                self.errors[self.current_command] = [str(' '.join(args[1:]))]
        return process.returncode

    def askYesNoQuestion(self,  message, question_tag, default=True):
        print(os.linesep * 2)
        self.printColor(Colors.BLUE, message + ": ", eol='')
        self.printColor(Colors.WARNING, "(default: " + ("Yes" if default else "No") + ") (Y/N)")
        self.printColor(Colors.BOLD, "Answer : ", eol='')
        sys.stdout.flush()
        answer = sys.stdin.readline().replace(os.linesep, '')
        if answer == "Y":
            self.yes_no_questions[question_tag] = True
            return True
        if (answer == ""):
            self.yes_no_questions[question_tag] = default
            return default
        self.yes_no_questions[question_tag] = False
        return False

    def askQuestion(self, message, default = ""):
        self.printColor(Colors.BLUE, message)
        self.printColor(Colors.BOLD, "Answer (default="+default+"): ", eol='')
        sys.stdout.flush()
        ret = sys.stdin.readline().replace(os.linesep, '')
        if ret == "":
            return default
        return ret

    def addToPrint(self, message):
        self.to_print.append(message)
        return 0



    '''
        CORE
    '''
    def feed(self, array):
        self.commands_list = self.commands_list + array
        return 0

    def parse(self):
        try:
            for command in self.commands_list:
                if not isinstance(command, str):
                    raise Exception("Invalid parameter + " + str(command))
                self.commands.append(command)
        except Exception as e:
            self.logError("An exception has been raised : " + str(e))
            return 1
        return 0

    def end(self):
        count = 0

        self.printFullTerm(Colors.WARNING, "Summary")
        self.printColor(Colors.GREEN, "Success : ")
        for command, valid in self.executed.items():
            if not valid:
                self.printColor(Colors.BLUE, "\t- Command : " + command + " successfully executed !")
            else:
                self.printColor(Colors.WARNING, "\t- In commmand : " + command)
                for exe in valid:
                    self.printColor(Colors.GREEN, "\t\t - Command : " + exe + " successfully executed ! ")
        self.printColor(Colors.FAIL, "Errors : ")
        for command, items in self.errors.items():
            count += 1
            if (not items):
                self.printColor(Colors.FAIL, "Command : " + command + " failed !")
            else:
                self.printColor(Colors.WARNING, "\t- In commmand : " + command)
                for exe in items:
                    self.printColor(Colors.FAIL, "\t\t - Command : " + exe + " failed.")
        for message in self.to_print:
            self.printColor(Colors.BOLD, message)
        return count

    def execCommand(self, command):
        for cmd in self.commandMatcher[command]:
            if "normal" == cmd:
                for c in self.commandMatcher[command]["normal"]:
                    if self.execProcess(c):
                        return 1
            elif "env_pip" == cmd:
                for c in self.commandMatcher[command]["env_pip"]:
                    if c != "" and c:
                        if self.execProcessFromVenv(self.venv_pip + " " + c):
                            return 1
            elif "env_bin" == cmd:
                for c in self.commandMatcher[command]["env_bin"]:
                    if c != "" and c:
                        if self.execProcessFromVenv(self.venv_bin + " " + c):
                            return 1
            elif "special" == cmd:
                for c in self.commandMatcher[command]["special"]:
                    if c == "requirements":
                        if self.execProcessFromVenv(self.venv_pip + " install -r " + self.requirements):
                            return 1
                    elif c == "create":
                        if (not os.path.isdir(self.venv)):
                            if self.execProcess("virtualenv " + self.venv + " -p " + self.python_path):
                                return 1
                        else:
                            self.printFullTerm(Colors.WARNING, "Virtual environment already exist")
            elif "link":
                for link in self.commandMatcher[command]["link"]:
                    if (link in self.commandMatcher and link != self.current_command):
                        temp = self.current_command
                        self.current_command = link
                        if self.execCommand(link):
                            return 1
                        self.current_command = temp
        return 0

    def exec(self):
        if (not self.commands):
            return 0
        for command in self.commands:
            self.current_command = command
            if command == "init":
                self.createConfig()
            elif command in self.commandMatcher:
                if self.execCommand(command):
                    break
            else:
                self.logError("Invalid command : " + str(command))
                self.errors[command] = []
        return self.end()

    def logError(self, message):
        self.printColor(Colors.FAIL, "Installer : An error occurred [" + message + "]", file=sys.stderr)
        return 0

'''
    Config Class
'''


class Config:
    __parser = argparse.ArgumentParser("Installer parser")
    __config_file = "install.json"
    __content = {
        "config_file": "install.json",
        "requirements": "REQUIREMENTS.txt",
        "path": "..",
        "name": "default",
        "env": "venv"
    }
    __commands = {"install": {
        "env_bin": [],
        "env_pip": [],
        "normal": [
            "pip install --upgrade pip",
            "pip install virtualenv --upgrade"
        ],
        "special": ["create"],
        "link": ["update"]
    }, "update": {
        "env_bin": [],
        "env_pip": [
            "install --upgrade pip",
            "install --upgrade wheel",
            ""
        ],
        "normal": [],
        "special": ["requirements"]
    }}
    usage = ""
    __command_list = []

    def __init__(self):
        self.__parser.add_argument("command", help="The command you want to execute")
        self.__parser.add_argument("--conf", help="Configuration file (.json)")
        self.__parser.add_argument("--path", help="Path where the virtual env will be created")
        self.__parser.add_argument("--name", help="Your configuration name")
        self.__parser.add_argument("--env", help="Your environment directory name")
        self.__parser.add_argument("--req", help="Your requirements file")
        self.usage = self.__parser.format_usage()

    def createConfigFile(self):
        configuration = {}
        configuration["Configuration"] = self.__content
        configuration["install"] = self.__commands["install"]
        configuration["update"] = self.__commands["update"]
        return configuration

    def parse(self):
        try:
            res = self.__parser.parse_args(), self.__parser.format_usage()
            return (res)
        except SystemExit:
            sys.exit(1)

    def parseConf(self):
        res, usage = self.parse()
        try:
            if (res.conf):
                self.__content["config_file"] = res.config
                if self.loadConfig():
                    return 1
            if (res.path):
                self.__content["path"] = res.path
            if (res.req):
                self.__content["requirements"] = res.req
            if (res.name):
                self.__content["name"] = res.name
            if (res.env):
                self.__content["env"] = res.env
            self.__command_list.append(res.command)
            return 0
        except:
            return 1

    def getReq(self):
        return self.__content["requirements"]

    def getPath(self):
        return self.__content["path"]

    def getEnv(self):
        return self.__content["env"]

    def loadConfig(self):
        try:
            with open(self.__content["config_file"]) as data_file:
                data = json.load(data_file)
                for key, content in data:
                    if key == "Configuration":
                        for k, v in content:
                            self.__content[k] = v
                    else:
                        self.__commands[key] = {}
                        with self.__commands[key] as command:
                            for k, v in content:
                                command[k].append(v)
                return 0
        except Exception as e:
            print(e, file=sys.stderr)
            return 1

    def getCommandList(self):
        return self.__command_list

    def getConfigFile(self):
        return self.__content["config_file"]

    def getCommands(self):
        return self.__commands

    def printUsage(self):
        print(self.usage, file=sys.stderr)

    def addConf(self, key, value):
        if isinstance(key, str) and isinstance(value, str):
            self.__content[key] = value
            return 0
        return 1

    def feed(self, param):
        self.__parameters.append(param)
        return 0

    def setConfigFile(self, conf_file):
        if os.path.isfile(conf_file):
            self.__content["config_file"] = conf_file
            return 0
        return 1

    def setPath(self, path):
        if (os.path.isdir(path)):
            self.__content["path"] = path
            return 0
        return 1

    def setEnvName(self, name):
        self.__content["env"] = name
        return 0

    def setRequirements(self, req):
        if (os.path.isfile(req)):
            self.__content["requirements"] = req
            return 0
        return 1

    def setConfName(self, name):
        self.__content["name"] = name
        return 0

    def getConfig(self):
        return self.__content


'''
    Color class
'''


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

if __name__ == "__main__":
    conf = Config()
    if conf.parseConf():
        sys.exit(1)
    installer = Installer(conf)
    sys.exit(installer.exec())