#!/usr/bin/env python
#-------------------------------------------------------------------------------
#    FILE: mypipe.py
# PURPOSE: pipe wrapper
#
#  AUTHOR: Jason G Yates
#    DATE: 21-Apr-2018
#
# MODIFICATIONS:
#-------------------------------------------------------------------------------

import os, sys, time, json, threading
import mythread, mycommon

#------------ MyPipe class -----------------------------------------------------
class MyPipe(mycommon.MyCommon):
    #------------ MyPipe::init--------------------------------------------------
    def __init__(self, name, callback = None, Reuse = False, log = None, simulation = False):
        super(MyPipe, self).__init__()
        self.log = log
        self.BasePipeName = name
        self.Simulation = simulation

        if self.Simulation:
            return

        self.ThreadName = "ReadPipeThread" + self.BasePipeName
        self.Callback = callback

        self.FileAccessLock = threading.RLock()

        self.FileName = os.path.dirname(os.path.realpath(__file__)) + "/" + self.BasePipeName + "_dat"

        try:
            if not Reuse:
                try:
                    os.remove(self.FileName)
                except:
                    pass
                with open(self.FileName, 'w') as f: # create empty file
                    f.write("")

        except Exception as e1:
            self.LogErrorLine("Error in MyPipe:__init__: " + str(e1))

        if not self.Callback == None:
            self.Threads[self.ThreadName] = mythread.MyThread(self.ReadPipeThread, Name = self.ThreadName)


    #------------ MyPipe::Write-------------------------------------------------
    def WriteFile(self, data):
        try:
            with self.FileAccessLock:
                with open(self.FileName, 'a') as f:
                    f.write(data + "\n")
                    f.flush()

        except Exception as e1:
            self.LogErrorLine("Error in Pipe WriteFile: " + str(e1))

    #------------ MyPipe::ReadLines---------------------------------------------
    def ReadLines(self):

        try:
            with self.FileAccessLock:
                with open(self.FileName, 'rw+') as f:
                    lines = f.readlines()
                open(self.FileName, 'w').close()
            return lines
        except Exception as e1:
            self.LogErrorLine("Error in mypipe::ReadLines: " + str(e1))
            return []

    #------------ MyPipe::ReadPipeThread----------------------------------------
    def ReadPipeThread(self):

        while True:
            try:
                time.sleep(0.5)
                if self.Threads[self.ThreadName].StopSignaled():
                    return
                # since realines is blocking, check if the file is non zero before we attempt to read
                if not os.path.getsize(self.FileName):
                    continue
                ValueList = self.ReadLines()
                if len(ValueList):
                    for Value in ValueList:
                        if len(Value):
                            self.Callback(Value)
            except Exception as e1:
                self.LogErrorLine("Error in ReadPipeThread: " + str(e1))

    #----------------MyPipe::SendFeedback---------------------------------------
    def SendFeedback(self,Reason, Always = False, Message = None, FullLogs = False, NoCheck = False):

        if self.Simulation:
            return

        try:
            FeedbackDict = {}
            FeedbackDict["Reason"] = Reason
            FeedbackDict["Always"] = Always
            FeedbackDict["Message"] = Message
            FeedbackDict["FullLogs"] = FullLogs
            FeedbackDict["NoCheck"] = NoCheck

            data = json.dumps(FeedbackDict, sort_keys=False)
            self.WriteFile(data)
        except Exception as e1:
            self.LogErrorLine("Error in SendFeedback: " + str(e1))

    #----------------MyPipe::SendMessage----------------------------------------
    def SendMessage(self,subjectstr, msgstr, recipient = None, files = None, deletefile = False, msgtype = "error"):

        if self.Simulation:
            return
        try:
            MessageDict = {}
            MessageDict["subjectstr"] = subjectstr
            MessageDict["msgstr"] = msgstr
            MessageDict["recipient"] = recipient
            MessageDict["files"] = files
            MessageDict["deletefile"] = deletefile
            MessageDict["msgtype"] = msgtype

            data = json.dumps(MessageDict, sort_keys=False)
            self.WriteFile(data)
        except Exception as e1:
            self.LogErrorLine("Error in SendMessage: " + str(e1))

    #------------ MyPipe::Close-------------------------------------------------
    def Close(self):

        if self.Simulation:
            return

        if not self.Callback == None:
            if self.Threads[self.ThreadName].IsAlive():
                self.Threads[self.ThreadName].Stop()
                self.Threads[self.ThreadName].WaitForThreadToEnd()
                del self.Threads[self.ThreadName]
