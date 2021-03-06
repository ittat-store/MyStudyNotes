import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import Widget
import subprocess
import re
import time
import asyncio
import typing
import os

class PyWinDesign:
    #由于点击事件的交互逻辑,依赖界面,也依赖逻辑,不能在界面类里面写死实现,要作为接口对外暴露,像安卓一样
    class click_interface:#按键接口
        def button1_click(self,button_state):
            pass

        def onClick(self,event):
            pass
        
        def winColse(self):
            pass

    def __init__(self, 启动窗口,click_interface):
        self.click_interface_new=click_interface
        self.启动窗口 = 启动窗口
        self.启动窗口.title('')
        self.启动窗口.resizable(width=False, height=False)
        screenwidth = self.启动窗口.winfo_screenwidth()
        screenheight = self.启动窗口.winfo_screenheight()
        size = '%dx%d+%d+%d' % (272, 121, (screenwidth - 272) / 2, (screenheight - 121) / 2)
        self.启动窗口.geometry(size)
        self.启动窗口.protocol('WM_DELETE_WINDOW', lambda : (self.click_interface_new.winColse(),self.启动窗口.destroy()))#修改窗口的关闭事件,lambda的多行语句
        
        self.组合框1 = ttk.Combobox(self.启动窗口,values=(), state='readonly')
        self.组合框1.bind('<Enter>',self.click_interface_new.onClick)
        self.组合框1.place(x=16,y=25,width=109,height=20)
        
        self.按钮1_标题 = tk.StringVar()
        self.按钮1_标题.set('抓log')
        self.按钮1_状态 = 0
        self.按钮1 = tk.Button(self.启动窗口,textvariable=self.按钮1_标题,command=self.log_click)
        self.按钮1.place(x=172,y=21,width=80,height=32)
        
        self.按钮2_标题 = tk.StringVar()
        self.按钮2_标题.set('打开交互窗口')
        self.按钮2_状态 = 0
        self.按钮2 = tk.Button(self.启动窗口,textvariable=self.按钮2_标题)
        self.按钮2.bind('<Button-1>',self.click_interface_new.onClick)
        self.按钮2.place(x=30,y=69,width=225,height=33)
    
    def setComboboxValue(self,数组):
        self.组合框1['value']=数组

    def getComboboxValue(self):
        return self.组合框1.get()

    def log_click(self):    #抓日志按钮  
        if(self.按钮1_状态==0): #开始抓
            self.按钮1_状态 = 1
            self.按钮1_标题.set('结束log')
            self.click_interface_new.button1_click(0)
        else:#结束抓
            self.按钮1_状态 = 0
            self.按钮1_标题.set('抓log')
            self.click_interface_new.button1_click(1)
        

class Logic:
    def reg_out(self,text):#正则处理命令运行返回的结果,获得各种设备
        regular=r'\w+(?!\W+devices)(?=\W+device)'
        return_var=re.findall(regular,text)
        return return_var
    
    def getDevices(self):#使用adb devices获得连接设备  
        (status, output)=subprocess.getstatusoutput('adb devices')
        return output

    def cmd_logcat(self,device_name):
        return "adb -s "+device_name+" logcat -v time"

    def getSaveFile(self,device_name):
        return open("C:/Users/panjunlong/Desktop/log/"+device_name+"_"+time.strftime("%Y_%m_%d_%H%M%S", time.localtime())+".txt", 'w')

    def addCmd(self,cmd_text,out_saveFile):
        print(cmd_text)
        p=subprocess.Popen(cmd_text, stdin=subprocess.PIPE,stdout=self.getSaveFile(out_saveFile), stderr=subprocess.PIPE,shell=False, close_fds=False)
        return p.pid

    def stopCmd(self,pid):
        subprocess.Popen("taskkill /F /T /PID " + str(pid) , shell=True)#使用 taskkill 来结束pid有效
    
    #新开cmd窗口执行命令按钮
    def cmd_click(self,cmd_text,out_saveFile):
        cmd="adb -s "+cmd_text+" shell\n"
        os.system("start cmd /k "+cmd)
        
    # def button1_click(self,button_state):#button的状态,不应该由logic类来处理,这样的依赖,是不必要的,单纯的logic类,不需要依赖界面类


class Platform:#委托模式,处理界面类和logic的交互.
    popen_list={}#保存新建的命令popen,这个也应该是平台的事
    #由平台来实现点击事件接口click_interface,因为点击事件的交互逻辑,依赖界面,也依赖逻辑,这两个依赖,导致点击事件放在界面或逻辑中,都违背了单向依赖的原则
    class click_interface_new(PyWinDesign.click_interface):
        def button1_click(self,button_state):
            device=Platform.mwin.getComboboxValue()
            if(button_state==0):                
                pid=Platform.mlogic.addCmd(Platform.mlogic.cmd_logcat(device),device)
                Platform.popen_list[device]=pid
            else:
                Platform.mlogic.stopCmd(Platform.popen_list[device])
                Platform.popen_list.pop(device)
            

        def onClick(self,event):
            if(event.widget.winfo_id()==Platform.mwin.组合框1.winfo_id()):#注意此时不能写self.mwin
                Platform.mwin.组合框1['values']=Platform.mlogic.reg_out(Platform.mlogic.getDevices())
            if(event.widget.winfo_id()==Platform.mwin.按钮2.winfo_id()):#注意此时不能写self.mwin
                device=Platform.mwin.getComboboxValue()
                Platform.mlogic.cmd_click(device,Platform.mlogic.getSaveFile(device))
                # asyncio.run(Platform.mlogic.cmd_click(device,Platform.mlogic.getSaveFile(device)))

        def winColse(self):            
            print("close all")
            Platform.stopAllCmd(Platform)
            
           
    def __init__(self, win,logic):
        Platform.mwin=win
        Platform.mlogic=logic

     #停止所有日志
    def stopAllCmd(self):
        if(len(self.popen_list)>0):
            for i in range(len(self.popen_list)):
                print(""+str(self.popen_list[i])+" stop")
                # popen_list[i].terminate()#实验证明是无效的
                # popen_list[i].kill()#实验证明是无效的
                Platform.mlogic.stopCmd(str(self.popen_list[i]))

if __name__ == '__main__':
    root = tk.Tk()
    click=Platform.click_interface_new()
    logic=Logic()
    app=PyWinDesign(root,click)
    platform=Platform(app,logic)


    root.mainloop()