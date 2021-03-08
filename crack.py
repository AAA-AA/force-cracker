import zipfile
from concurrent.futures.thread import ThreadPoolExecutor

from rarfile import RarFile
# from unrar import rarfile
import os
import sys
import threading
import argparse
from itertools import product
import time

parser = argparse.ArgumentParser(description='CompressedCrack', epilog='Use the -h for help')
parser.add_argument('-i', '--input', help='Insert the file path of compressed file', required=True)
parser.add_argument('rules', nargs='*', help='<min> <max> <character>')

# Const Character
CHARACTER = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_+=~`[]{}|\\:;\"'<>,.?/"

handle_pool = ThreadPoolExecutor(20)


class Check:
    def __init__(self, Arg):
        self.type = None
        self.rules = False
        self.startLength = None
        self.maxLength = None
        self.character = None
        # Check Rules
        if len(Arg) >= 4:
            self.getData(Arg)
            self.rules = True
        elif len(Arg) == 0 or len(Arg) > 2:
            parser.print_help()
            parser.exit()
        # Check File Exist
        if (self.CheckFileExist(Arg)):
            self.getType(Arg)
        else:
            print('No such file or directory: ', Arg[1])
            parser.exit()

    def CheckFileExist(self, Arg):
        if (os.path.isfile(Arg[1])):
            return True
        else:
            return False

    def getData(self, Arg):
        try:
            self.startLength = int(Arg[2])
            self.maxLength = int(Arg[3])
        except ValueError:
            print('Value Error')
            parser.exit()
        if self.startLength > self.maxLength:
            print('Length Error')
            parser.exit()
        if len(Arg) == 5:
            self.character = Arg[4]

    def getType(self, Arg):
        if os.path.splitext(Arg[1])[1] == ".rar" or os.path.splitext(Arg[1])[1] == ".zip":
            self.type = os.path.splitext(Arg[1])[1]
        else:
            print('Extension Error')
            parser.exit()


class Handler:
    def __init__(self, rules, typeCompress, startLength, maxLength, character):
        self.rules = rules
        self.location = sys.argv[2]
        self.type = typeCompress
        self.startLength = startLength
        self.maxLength = maxLength
        if not character:
            self.character = CHARACTER
        else:
            self.character = character
        self.result = False

        self.GetFile()
        self.CheckRules()

    def GetFile(self):
        # Khai báo file
        if self.type == '.zip':
            self.FileCrack = zipfile.ZipFile(self.location)
        else:
            self.FileCrack = RarFile(self.location)

    def Brute(self, password):
        try:
            if self.type == '.zip':
                tryPass = password.encode()
            else:
                tryPass = password
            print("try %s with thread %s" % (tryPass ,  threading.currentThread().getName()))
            self.FileCrack.extractall(pwd=tryPass)
            print('=========================SUCCESS==========================')
            print('COST TIME:', time.process_time() - self.start_time, 's')
            print('FIND PASSWORD:%s' % password)
            print('==========================================================')
            self.result = True
        except:
            pass

    def CheckRules(self):
        self.start_time = time.process_time()
        print("Check rainbow table first!")
        rainbow_dir = os.getcwd() + os.sep + "rainbow"
        for f in os.listdir(rainbow_dir):
            nThread = threading.Thread(target=self.HandleSingleFile, args=(rainbow_dir + os.sep + f,))
            nThread.start()
            nThread.join()
        if self.result:
            print("*********************Crack Finished!********************")
            return
        else:
            print("force rainbow table collision failed! try Brute next....")
        print('Cracking...')
        if not self.rules:
            length = 1
            while True:
                if length > 15:
                    print("密码超过15位！不进行破解！")
                    break
                else:
                    nThread = threading.Thread(target=self.forceFind, args=(length,))
                    nThread.start()
                    nThread.join()
                length += 1
            if not self.result:
                print('Cannot find password with this rules')
                return
        else:
            for length in range(self.startLength, self.maxLength + 1):
                nThread = threading.Thread(target=self.forceFind, args=(length,))
                nThread.start()
                nThread.join()
            if not self.result:
                print('Cannot find password with this rules')
                return

    def HandleSingleFile(self, filepath):
        with open(filepath) as rb_file:
            for line in rb_file:
                real_line = line.rstrip('\n')
                if not self.rules:
                    self.Brute(real_line)
                    if self.result:
                        return
                else:
                    if len(real_line) in range(self.startLength, self.maxLength):
                        self.Brute(real_line)
                        if self.result:
                            return

    def forceFind(self, pwd_length):
        listPass = product(self.character, repeat=pwd_length)
        for Pass in listPass:
            tryPass = ''.join(Pass)
            handle_pool.submit(self.Brute(tryPass))
            # 任意有一个线程找到了，并修改了值，则跳出
            if self.result:
                break


def main():
    check = Check(sys.argv[1:])
    args = parser.parse_args()
    Handling = Handler(check.rules, check.type, check.startLength, check.maxLength, check.character)


# unrar==0.4
# rarfile==4.0
if __name__ == '__main__':
    main()
