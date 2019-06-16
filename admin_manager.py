import sys
import threading
from _thread import *
from queue import Queue, Empty
import tkinter
from tkinter import ttk
import datetime
import time
import pickle
import ast
import subprocess
import os
import socket
import ctypes
import psutil

'''

Thread information:
t0 = Initial thread to run program
t1 = Thread used to read log file.
#t2 = Thread used to run the game server. No need for thread, runs external process.
t3 = Run server manager server.
t4 = Run auto restart timer

'''

LARGE_FONT = ("Verdana", 12)
NORM_FONT = ("Verdana", 10)
SMALL_FONT = ("Verdana", 8)

#mb_dir = 'C:/Users/Tim/Desktop/Coding/Python/MB Server Manager/V0.2/mb_warband_dedicated.exe'
#mb_dir = 'C:/Servers/59th/NRP - Backup 07-03-16/mb_warband_dedicated.exe'
mb_dir = str(sys.argv[0])
#print(mb_dir)
mb_dir = ('\\').join(mb_dir.split('\\')[0:-2]) + '\\mb_warband_dedicated.exe'

try:
    programSettings = open('settings.txt', 'r', encoding='utf-8')
    programSettingsLines = programSettings.readlines()
    settings_file = programSettingsLines[0][0:-1]
    port = int(programSettingsLines[1])
except FileNotFoundError:
    print('No settings file. Using defaults.')
    settings_file = 'NRP.txt'
    port = 5555

print_lock = threading.Lock()

##print_lock = threading.Lock()

def quit():
    quit()

def qf(param):
    print(param)

def consoleLog(msg):
    print(msg)

def popupmsg(msg):
    popup = tkinter.Tk()
    print(msg)
    
    popup.wm_title("!")
    label = ttk.Label(popup, text=msg, font=NORM_FONT)
    label.pack()
    button1 = ttk.Button(popup, text="Okay", command = popup.destroy)
    button1.pack()
    popup.mainloop()

class ServerManagerApp(tkinter.Tk):

    def __init__(self, *args, **kwargs):

        tkinter.Tk.__init__(self,*args,**kwargs)
        tkinter.Tk.iconbitmap(self,default="59thicon16x16.ico")
        tkinter.Tk.wm_title(self, "Server Manager: {}".format(str(sys.argv[0])))
        
        container = tkinter.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        container.update_idletasks()
        w = container.winfo_screenwidth()
        h = container.winfo_screenheight()
        print('Width: {}, height: {}'.format(w,h))

        menubar = tkinter.Menu(container)
        filemenu = tkinter.Menu(menubar,tearoff=0)
        filemenu.add_command(label="Save", command = lambda: popupmsg("Not Supported Yet"))
        filemenu.add_command(label="Settings", command = lambda: self.show_frame(ServerSettings))
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=quit)

        guidmenu = tkinter.Menu(menubar,tearoff=0)
        guidmenu.add_command(label="Admins", command = lambda: self.show_frame(PageOne))
        guidmenu.add_command(label="Bans", command = lambda: popupmsg("Not Supported Yet"))
        guidmenu.add_command(label="Donators", command = lambda: popupmsg("Not Supported Yet"))
        guidmenu.add_command(label="Skins", command = lambda: popupmsg("Not Supported Yet"))
        guidmenu.add_separator()
        guidmenu.add_command(label="Online", command = lambda: self.show_frame(OnlinePlayers))
    
        consolemenu = tkinter.Menu(menubar, tearoff=0)
        consolemenu.add_command(label="Server", command = lambda: self.show_frame(ServerConsole))
        consolemenu.add_command(label="Logs", command = lambda: self.show_frame(ServerDetails))

        menubar.add_cascade(label="File", menu=filemenu)
        menubar.add_cascade(label="Players", menu=guidmenu)
        menubar.add_cascade(label="Console", menu=consolemenu)

        tkinter.Tk.config(self, menu=menubar)

        self.frames = {}

        for F in (ServerSettings,PageOne,ServerDetails,ServerConsole,OnlinePlayers):

            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, stick="nsew")

        t0 = threading.Thread(target=self.show_frame(ServerSettings))
        t0.start()
        t0.join()
        #self.show_frame(ServerSettings)

    def show_frame(self,cont):

        frame = self.frames[cont]
        frame.tkraise()

class ServerDetails(tkinter.Frame):

    def __init__(self, parent, controller):
        tkinter.Frame.__init__(self,parent)

        label = tkinter.Label(self, text="Server Log", font=LARGE_FONT)
        label.grid(row=0, column=0, stick="w", padx=10, pady=10, columnspan=1)

        scrollBar = ttk.Scrollbar(self)
        self.console = tkinter.Text(self, width=86, height=16, wrap="word", state='disabled')
        scrollBar.config(command=self.console.yview)
        self.console.config(yscrollcommand=scrollBar.set)
        scrollBar.grid(column=0,row=1, columnspan=6, stick='nse', pady=(0,10))
        self.console.grid(column=0,row=1, columnspan=6, stick="nsew", padx=(10,16), pady=(0,10))

        scrollBar2 = ttk.Scrollbar(self)              
        self.console_formatted = tkinter.Text(self, width=86, height=16, wrap="word", state='disabled')
        scrollBar2.config(command=self.console_formatted.yview)
        self.console_formatted.config(yscrollcommand=scrollBar2.set)
        scrollBar2.grid(column=0,row=3, columnspan=6, stick='nse', pady=(0,10))
        self.console_formatted.grid(column=0,row=3, columnspan=6, stick="nsew", padx=(10,16), pady=(0,10))
        
        t1 = threading.Thread(target=self.readLogs)
        t1.start()
        #t1.join()
        #self.readLogs()

##        self.startButton = ttk.Button(self, text='Start', command= lambda: self.startServer())
##        self.startButton.grid(column=4, row=2, stick="nsew")
##        
##        self.stopButton = ttk.Button(self, text='Stop', command= lambda: self.stopServer())
##        self.stopButton.grid(column=5, row=2, stick="nsew", padx=(0,10))

    def updateConsole(self, msg):
        
        self.console['state'] = 'normal'
        if msg != ' \n' and msg != ' ':
            #print(msg.encode('utf-8'))
            self.console.insert('end', msg)
            #self.console.insert('end', '\n')
            self.console.see(tkinter.END)
        self.console['state'] = 'disabled'

    def updateFormattedConsole(self, msg):

        self.console_formatted['state'] = 'normal'
        self.console_formatted.insert('end', '\n')
        self.console_formatted.insert('end', msg)
        self.console_formatted.see(tkinter.END)
        self.console_formatted['state'] = 'disabled'

    def follow(self, thefile):
        thefile.seek(0,2)
        date = str(datetime.date.today())
        while True:
            try:
                line = thefile.readline()
            except UnicodeDecodeError as e:
                print('### ERROR ####')
                print(str(e))
                print('-------------------------------------------------------------------------------')
                continue
            
            if not line:
                today = str(datetime.date.today())
                #print(today)
                if today != date:
                    print('Changeing script file!')
                    thefile.close()
                    date = today
                    day = today[8:]
                    month = today[5:7]
                    year = today[0:4]
                    logpath = "server_log_{}_{}_{}.txt".format(str(month),str(day),str(year[2:]))
                    while True:
                        try:
                            thefile = open("../logs/{}".format(logpath),"r", encoding='utf8')
                            thefile.seek(0,2)
                            break
                        except:
                            print(str(today) +  ' - No log file!')
                            time.sleep(10)
                time.sleep(0.1)
                continue
            
            self.updateConsole(line)
            yield line

    def openLogFile(self):
        date = str(datetime.date.today())
        day = date[8:]
        month = date[5:7]
        year = date[0:4]
        #print(date)
        logpath = "server_log_{}_{}_{}.txt".format(str(month),str(day),str(year[2:]))
        logfile = open("../logs/{}".format(logpath),"r", encoding='utf8')
        return logfile

    def readLogs(self):

        if __name__ == '__main__':

            seperator = '--------------------------------------------------------------------------------------' # 86
                                
            while True:
                try:
                    logfile = self.openLogFile()
                    with print_lock:
                        print('Log file opened!')
                    break
                except:
                    with print_lock:
                        print("No log file!")
                    time.sleep(10)

        try:
            playersList = pickle.load(open('players/playersList','rb'))
            playersListCopy = playersList[:]
            uniqueIds = []
            for player in playersList:
                # Delete any duplicate entries.
                if player['guid'] not in uniqueIds:
                    uniqueIds.append(int(player['guid']))
                else:
                    del playersListCopy[playersListCopy.index(player)]

            playersList = playersListCopy
            players = playersList
        except:
            players = []
            print('### NO PLAYERSLIST FILE ###')
            self.updateFormattedConsole('### NO PLAYERSLIST FILE ###')

        try:
            with open('players/onlinePlayers','r') as fOnlinePlayers:
                onlinePlayers = fOnlinePlayers.read()
                onlinePlayers = ast.literal_eval(onlinePlayers)
                fOnlinePlayers.close
                
        except:
            self.updateFormattedConsole('No online players file!')
            print('No online players file!')
            onlinePlayers = {}

        self.label1 = tkinter.Label(self, text=(str(len(onlinePlayers)) + '/200'), font=LARGE_FONT)
        self.label1.grid(row=0, column=5, stick="e", padx=10, pady=10)

        def clearOnlinePlayers():
            onlinePlayers = {}
            print('Online Players cleared')
            self.updateFormattedConsole('Online players cleared')

        def clearJoiningPlayers():
            joiningPlayers = {}
            print('Joining Players cleared')
            self.updateFormattedConsole('Joining players cleared')

        # Clear online players list
        button1 = ttk.Button(self, text='Clear Players', command = lambda: clearOnlinePlayers())
        button1.grid(column=0, row=2, stick="nesw", padx=10, pady=(0,10))

        # Clear joining players list
        button2 = ttk.Button(self, text='Clear Joining', command = lambda: clearJoiningPlayers())
        button2.grid(column=1, row=2, stick="nesw", padx=10, pady=(0,10))

        joiningPlayers = {}
        #joiningPlayersMapChange = None
        loglines = self.follow(logfile)
        prevHour = None

        for line in loglines:
            # If a kill takes place
            if '<img=ico_swordone>' in line or '<img=ico_spear>' in line or '<img=ico_' in line:
                player1 = line[11:line.index('<')-1]
                player2 = line[line.index('>')+2:-2]
                
                if player1 != '' and player1 != ' ':
                    
                    if player1[0] == ' ':
                        player1 = player1[1:]
                    if player2[0] == ' ':
                        player2 = player2[1:]

                    #print(player1 + ' has killed ' + player2)
                    self.updateFormattedConsole(str(player1 + ' has killed ' + player2))

                    try:
                        guid1 = onlinePlayers[player1]
                        
                        for user in players:
                            if user['guid'] == guid1:
                                user['kills'] += 1
                                #print(user)
                    except KeyError:
                        #print('Player 1 not online!')
                        self.updateFormattedConsole('Player 1 not online!')

                    try:
                        guid2 = onlinePlayers[player2]
                        
                        for user in players:
                            if user['guid'] == guid2:
                                user['deaths'] += 1
                                #print(user)
                    except KeyError:
                        #print('Player 2 not online!')
                        self.updateFormattedConsole('Player 2 not online!')


                    #print('-----------------------------------------------------------')
                    self.updateFormattedConsole(seperator)
                    
            elif 'SERVER has joined the game with ID: 0' in line:
                onlinePlayers = {}
                #print('Server has started!')
                self.updateFormattedConsole('Server has started!')
                with open('players/onlinePlayers','w') as fonline:
                    fonline.write(str(onlinePlayers))
                    fonline.close
                #print('-------------------------------------------------------------')
                self.updateFormattedConsole(seperator)
                
            elif 'has joined the game with ID:' in line:
                # When a player joins
                player = line[11:line.index(' has ')]
                if player[0] == ' ':
                    player = player[1:]
                guid = line[line.index('ID: ')+4:-2]
                if ' and has administrator rights.' in guid:
                    # If the player is an admin
                    guid = int(guid[0:-30])
                else:
                    guid = int(guid)

                joiningPlayers[player] = guid 
                #print(joiningPlayers)
                self.updateFormattedConsole(str(len(joiningPlayers)) + ' joining players: ' + str(joiningPlayers))
                #print('------------------------------------------------------------')
                self.updateFormattedConsole(seperator)
                    
            elif 'has joined the server.' in line:
                # When a player joins
                player = line[21:line.index(' has ')].split(' ')[-1]
                if player[0] == ' ':
                    player = player[1:]
                if player in joiningPlayers.keys() and player not in onlinePlayers.keys():
                    guid = joiningPlayers[player]

                    exists = False

                    if player in onlinePlayers:
                        #print('Player already online!')
                        self.updateFormattedConsole('Player already online!')
                        exists = True
                    else:
                        onlinePlayers[player] = guid   
                        #print('Player has joined: ' + player + ' with ID: ' + str(guid))
                        self.updateFormattedConsole(str('Player has joined: ' + player + ' with ID: ' + str(guid)))
                        with open('players/onlinePlayers','w') as fonline:
                            fonline.write(str(onlinePlayers))
                            fonline.close
                        self.label1['text'] = str(len(onlinePlayers)) + '/200'

                    for index, user in enumerate(players):
                        if user['guid'] == guid:
                            if user['username'] != player:
                                print('Previously joined as: ' + str(user['username']))
                                players[index]['username'] = str(player)
                                print('Stored name updated to: ' + str(user['username']))
                            exists = True
                            #print('Player {} exists'.format(player))
                            self.updateFormattedConsole(str('Player {} exists'.format(player)))
                            break
                        
                    if exists == False:
                        #print('NEW PLAYER: {}'.format(player))
                        self.updateFormattedConsole(str('NEW PLAYER: {}'.format(player)))
                        players.append({'username': player, 'guid': guid, 'kills': 0, 'deaths': 0})
                        with open('players/playersList','wb') as f:
                            pickle.dump(players,f)
                            f.close
                        with open('players/playersListPure','w') as fpure:
                            fpure.write(str(players))
                            fpure.close

                    del joiningPlayers[player]

                elif player in onlinePlayers.keys():
                    #print("{} already online".format(player))
                    self.updateFormattedConsole(str("{} already online".format(player)))

                else:
                    #print(joiningPlayers)
                    #print("{} NOT IN JOINING PLAYERS".format(player))
                    self.updateFormattedConsole(str("{} NOT IN JOINING PLAYERS".format(player)))

                #print('Players online: ' + str(len(onlinePlayers)))    
                #print('------------------------------------------------------------')
                self.updateFormattedConsole(seperator)

            elif ' Changed the map to ' in line:
                gamemode = line[line.index('gamemode')+9:line.index(' and with the nations')]
                mapname = line[line.index('the map to ')+11:line.index(' with gamemode')]
                nations = line[line.index('nations ')+8:-2]
                nation1 = nations.split(' and ')[0]
                nation2 = nations.split(' and ')[1]
                #print("MAP CHANGED, GAMEMODE: {}, MAP: {}, NATIONS: {} vs {}".format(gamemode, mapname, nation1, nation2))
                self.updateFormattedConsole(str("MAP CHANGED, GAMEMODE: {}, MAP: {}, NATIONS: {} vs {}".format(gamemode, mapname, nation1, nation2)))
                #print("Joining players before: " + str(joiningPlayers))
                #print("Online players before: " + str(onlinePlayers))
                joiningPlayers.update(onlinePlayers)
                #print("Joining players: " + str(joiningPlayers))
                onlinePlayers = {}

            elif 'has left the game with ID:' in line:
                # When a player leaves
                player = line[11:line.index(' has ')]
                if player[0] == ' ':
                    player = player[1:]
                guid = int(line[line.index('ID: ')+4:-2])
                #print('Player has left: ' + player + ' with ID: ' + str(guid))
                self.updateFormattedConsole(str('Player has left: ' + player + ' with ID: ' + str(guid)))
                try:
                    del onlinePlayers[player]
                    self.label1['text'] = str(len(onlinePlayers)) + '/200'
                    with open('players/onlinePlayers','w') as fonline:
                        fonline.write(str(onlinePlayers))
                        fonline.close
                except KeyError:
                    #print("Player {} with GUID: {}, not in list".format(player, guid))
                    self.updateFormattedConsole(str("Player {} with GUID: {}, not in list".format(player, guid)))

                #print('Players list: ')
                #print(onlinePlayers)
                #print('Players online: ' + str(len(onlinePlayers)))
                #print('------------------------------------------------------------')
                self.updateFormattedConsole(seperator)

            now = str(datetime.datetime.now().time())
            #print(now)

            hour = str(int(now[0:2])-1)
            # -1 from hour for GMT+00 time!
            if hour == '24':
                hour = '00'
            elif hour == '-1':
                hour = '23'
            elif int(hour) < 10:
                hour = "0{}".format(hour)
            minute = now[3:5]
            sec = now[6:8]

            today = str(datetime.date.today())
            
##            if hour == '22' and minute == '59' and today == date:
##                logfile.close()
##                day = today[8:]
##                month = today[5:7]
##                year = today[0:4]
##                date = today
##                print(today)
##                
##                while True:
##                    try:
##                        logfile = self.openLogFile()
##                        print('Log file opened!')
##                        break
##                    except:
##                        print("No log file! - {}".format(str(today)))
##                        time.sleep(10)
##
##                logfile = self.follow(logfile)

            if hour != prevHour:
                # and (minute == '00' or minute == '05' or minute == '10'
                                     #or minute == '15' or minute == '20' or minute == '25'
                                     #or minute == '30' or minute == '35' or minute == '40'
                                     #or minute == '45' or minute == '50' or minute == '55')
                # Hourly updates.
                try:
                    playerCount = pickle.load(open('players/playerCount', 'rb'))
                except:
                    print('No player count file!')
                    playerCount = [{'00': 0},{'01': 0},{'02': 0},{'03': 0},{'04': 0},{'05': 0},
                                   {'06': 0},{'07': 0},{'08': 0},{'09': 0},{'10': 0},{'11': 0},
                                   {'12': 0},{'13': 0},{'14': 0},{'15': 0},{'16': 0},{'17': 0},
                                   {'18': 0},{'19': 0},{'20': 0},{'21': 0},{'22': 0},{'23': 0}]

                playerCountCopy = None
                for index, count in enumerate(playerCount):
                    #print(index,count)
                    #print(list(count.keys())[0] + ', hour: ' + hour)
                    if list(count.keys())[0] == '24':
                        playerCountCopy = playerCount
                        del playerCountCopy[index]
                    if list(count.keys())[0] == hour:
                        count[hour] = len(onlinePlayers)                        
                        #print('RECORDING {} PLAYERS ONLINE.'.format(len(onlinePlayers)))
                        self.updateFormattedConsole(str('RECORDING {} PLAYERS ONLINE.'.format(len(onlinePlayers))))

                        break

                if playerCountCopy:
                    playerCount = playerCountCopy
                    playerCountCopy = None
                                              
                with open('players/playerCount','wb') as f:
                    pickle.dump(playerCount,f)
                    f.close

                with open('players/playerCountPure','w') as fpure:
                    fpure.write(str(playerCount))
                    fpure.close
                    
                with open('players/playersListPure','w') as fPlayersPure:
                    fPlayersPure.write(str(players))
                    fPlayersPure.close
                                              
                prevHour = hour
                #print('prevHour: ' + str(prevHour) + ', hour: ' + str(hour))
                self.updateFormattedConsole(str('prevHour: ' + str(prevHour) + ', hour: ' + str(hour)))
                #print('------------------------------------------------------------')
                self.updateFormattedConsole(seperator)

class ServerConsole(tkinter.Frame):
    # Subprocess for MB server

    def __init__(self, parent, controller):
        tkinter.Frame.__init__(self,parent)

        self.server_pid = None
        self.sub_server_pid = None
        self.start_time = None
        self.uptime = None

        label = tkinter.Label(self, text="Server Console", font=LARGE_FONT)
        label.grid(row=0, column=0, stick="w", padx=10, pady=10, columnspan=1)

        scrollBar = ttk.Scrollbar(self)
        self.console = tkinter.Text(self, width=86, height=16, wrap="word", state='disabled', borderwidth=1)
        scrollBar.config(command=self.console.yview)
        self.console.config(yscrollcommand=scrollBar.set)
        scrollBar.grid(column=0,row=1, columnspan=6, stick='nse', pady=(0,10))
        self.console.grid(column=0,row=1, columnspan=6, stick="nsew", padx=(10,16), pady=(0,10))

        self.startButton = ttk.Button(self, text='Start', command= lambda: self.startServer())
        self.startButton.grid(column=4, row=2, stick="nsew")
        
        self.stopButton = ttk.Button(self, text='Stop', state='disabled', command= lambda: self.stopServer())
        self.stopButton.grid(column=5, row=2, stick="nsew", padx=(0,10))

        self.checkButton = ttk.Button(self, text='Check', state='normal', command= lambda: self.checkServer())
        self.checkButton.grid(column=0, row=2, stick="nsew", padx=(10,0))

        t3 = threading.Thread(target=self.runServerManagerServer)
        t3.start()

        self.autoRestartEnabled = True

        self.progressBar = ttk.Progressbar(self, orient="horizontal", length=400, mode="determinate")
        self.t4 = threading.Thread(target=self.autoRestart, args=(30,))

        self.checkForProcess()

    def startAutoRestart(self):
        self.t4 = threading.Thread(target=self.autoRestart, args=(30,))
        self.t4.start()    

    def enableStopButton(self):
        self.stopButton['state'] = 'normal'

    def enableStartButton(self):
        self.startButton['state'] = 'normal'

    def disableStopButton(self):
        self.stopButton['state'] = 'disabled'

    def disableStartButton(self):
        self.startButton['state'] = 'disabled'

    def updateConsole(self, msg):

        self.console['state'] = 'normal'
        self.console.insert('end', '\n')
        self.console.insert('end', msg)
        self.console.see(tkinter.END)
        self.console['state'] = 'disabled'

    def checkForProcess(self):
        procname = 'mb_warband_dedicated.exe'

        for proc in psutil.process_iter():
            try:
                if proc.name() == procname and proc.exe() == mb_dir:
                    print('PID: ' + str(proc.pid))
                    self.sub_server_pid = proc.pid
                    self.start_time = time.time()
                    print('Sub server PID: ' + str(self.sub_server_pid))
                    #self.checkServer()
                    self.startAutoRestart()
                    self.sub_server_pid = proc.pid
                    return proc.pid
            except:
                with print_lock:
                    print('Access denied!')
            #else:
            #    return None

    def checkServer(self):
        
        try:
            server_info = psutil.Process(self.sub_server_pid)
            
            #print('Name: ' + server_info.name())
            #print('Status: ' + server_info.status())
            #print('CPU Percent: ' + str(server_info.cpu_percent(interval=1.0)))
            #print('CPU Times: ' + str(server_info.cpu_times()))
            #print('CPU Affinity: ' + str(server_info.cpu_affinity()))
            #print('Memory: ' + str(server_info.memory_info()))
            #print('Memory Percent: ' + str(server_info.memory_percent()))

            if server_info.status() == 'running':
                server_alive = True
            else:
                server_alive = False
                
            name = server_info.name()
            #print('CPU Count: ' + str(psutil.cpu_count(logical=False)))
            #print('CPU Count Logical: ' + str(psutil.cpu_count(logical=True)))
            cpu_percent = abs(server_info.cpu_percent(interval=1.0) / psutil.cpu_count(logical=True))
            mem_percent = round(server_info.memory_percent(),2)
            
            self.enableStopButton()
            self.disableStartButton()

            self.uptime = round((time.time() - self.start_time),0)

            #print('Process: ' + str(name) + ', CPU Usage: ' + str(cpu_percent) + '%, MEM Usage: ' + str(mem_percent) + '%')
            #print('Uptime: ' + str(self.uptime) + ' seconds')

            self.updateConsole(str('Process: ' + str(name) + ', CPU Usage: ' + str(cpu_percent) + '%, MEM Usage: ' + str(mem_percent) + '%'))
            self.updateConsole(str('Uptime: ' + str(self.uptime) + ' seconds'))
        except:
            print('Server PID does not exist!')
            server_alive = False
            cpu_percent = None
            mem_percent = None
            self.enableStartButton()
            self.disableStopButton()
       
        return [server_alive, cpu_percent, mem_percent, self.uptime]
        
    def startServer(self):
        if self.checkServer()[0]:
            print('Server already running!')
        else:
            print('Starting server')
            self.updateConsole('Starting server ...')
            
            self.disableStartButton()
            self.enableStopButton()

            self.runServer()
            self.updateConsole('Server started')
            self.start_time = time.time()
            
            self.autoRestartEnabled = True
            self.progressBar.grid()
            self.startAutoRestart()

    def stopServer(self):
        if self.checkServer():
            print('Stopping server')
            self.updateConsole('Stopping server ...')
            self.autoRestartEnabled = False
            self.disableStopButton()
            self.enableStartButton()
            #os.kill(server_pid, 9)
            #stdout = server.communicate(input=b'exit')[0]
            #print(stdout.decode('utf-8'))
            try:
                server_process = psutil.Process(self.sub_server_pid)
##                for proc in server_process.children():
##                    print('Killing child PID: ' + str(proc.pid))
##                    proc.kill()
                print('Killing PID: ' + str(server_process.pid))
                server_process.kill()
            except:                
##                server_process = psutil.Process(self.sub_server_pid)
##                print('Killing sub PID: ' + str(server_process.pid))
##                server_process.kill()
                print('Failed to stop server!')
                
            self.start_time = None
            
            self.updateConsole('Server stopped ...')
        else:
            print('Server already stopped!')

    def runServer(self):

        global server
        global server_pid
        global sub_server_pid

        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200

        #mb_dir = 'C:/Users/Tim/Desktop/Coding/Python/MB Server Manager/V0.2/mb_warband_dedicated.exe'
        #mb_dir = 'C:/Servers/59th/NRP - Backup 07-03-16/mb_warband_dedicated.exe'
        #settings_file = 'NRP.txt'

        server = subprocess.Popen([mb_dir, '-r', settings_file, '-m', 'Napoleonic', 'Wars'], stdin = subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True) 
        
        #(output, err) = server.communicate()
        #exit_code = server.wait()
        #print('Output: ' + str(output.decode('utf-8')))
        
        print('PID: ' + str(server.pid))
        server_pid = server.pid
        self.server_pid = server.pid

        time.sleep(0.2)

        server_process = psutil.Process(self.server_pid)
        for proc in server_process.children():
            self.sub_server_pid = proc.pid
            sub_server_pid = proc.pid
            print('Sub PID: ' + str(sub_server_pid))

    def autoRestart(self, secs):
        # Auto restarts server if down every x amount of secs.
        self.progressBar.grid(column=0, row=6, columnspan=6, padx=(10), pady=(10), stick='nsew')
        while self.autoRestartEnabled:
            alive = self.checkServer()[0]
            if not alive:
                print('SERVER DOWN! RESTARTING ...')
                self.updateConsole('SERVER DOWN! RESTARTING ...')
                self.startServer()
            for x in range(99):
                if not self.autoRestartEnabled:
                    self.progressBar.grid_remove()
                    break
                time.sleep(secs/100)
                self.progressBar.step(1)
        pbValue = self.progressBar.cget('value')
        #print(pbValue)
        if pbValue != 0.0 and pbValue != 100:
            self.progressBar.step(100-int(pbValue))
        self.progressBar.grid_remove()
        return False

    def runServerManagerServer(self):
        
        host = ''
        #port = 5555

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        quiting = False

        try:
            s.bind((host,port))
        except socket.error as e:
            print(str(e))

        s.listen(5)
        
        with print_lock:
            print('Waiting for a connection...')
            
        client_no = 0
        client_list = []

        def threaded_client(conn, client_id):
            conn.send(str.encode('Welcome to Top Hat Servers!\n'))
            reply = None

            while True:
                data = conn.recv(4096)
                ddata = data.decode('utf-8')

                print(ddata)
                if 'start' in ddata:
                    if self.checkServer()[0]:
                        pass
                    else:
                        with print_lock:
                            print('Starting server...')
                        reply = 'Starting server ...'
                        self.startServer()
                        with print_lock:
                            print('Server started.')
                elif ddata == 'stop':
                    if self.checkServer()[0]:
                        with print_lock:
                            print('Stopping server ...')
                        reply = 'Stopping server ...'
                        self.stopServer()
                        with print_lock:
                            print('Server stopped.')
                elif ddata == 'check':
                    with print_lock:
                        print('Checking server ...')
                    status, cpu, mem, uptime = self.checkServer()
                    if status == True:
                        reply = 'status: {}, CPU Usage: {}, MEM Usage: {}'.format(str(status), str(cpu), str(mem))
                    else:
                        reply = 'status: {}'.format(str(status))
                elif ddata == 'Quit':
                    with print_lock:
                        print('Client {} has quit'.format(client_id))
                    break
                else:
                    reply = ddata
                
                if not data:
                    break

                conn.send(reply.encode('utf-8'))
                dataList = []
            with print_lock:
                print('Client disconnected')
            conn.close()

        while True:

            conn, addr = s.accept()
            with print_lock:
                print('Connected to: ' + addr[0] + ':' + str(addr[1]))

            client_list.append(conn)

            start_new_thread(threaded_client,(conn, client_no))
            client_no += 1
        

##        def getCommunication():
##            output = server.stdout.readlines()
##            for line in output:
##                print(line.decode('utf-8'))
##
##        t2 = threading.Thread(target=getCommunication())
##        t2.start()

##    def updateConsole(self, msg):
##        
##        self.console['state'] = 'normal'
##        self.console.insert('end - 2c', msg[0:-1]+'\n')
##        self.console.see(tkinter.END)
##        self.console['state'] = 'disabled'
             
class ServerSettings(tkinter.Frame):
    # Server settings file

    def __init__(self, parent, controller):
        tkinter.Frame.__init__(self,parent)

        try:
            settingsfile = open("../{}".format(settings_file), "r")
        except Exception as e:
            print("No script file found!")
            print("Error: {}".format(e))

        data = settingsfile.readlines()

        self.password = None
        self.serverName = None
        self.adminPassword = None
        self.welcomeMessage = None
        self.gamemodeValue = None
        self.pointLimit = None
        self.port = None
        self.maxPlayers = None
        self.maxReserved = None

        for line in data:
            if 'set_server_name ' in line:
                x = line.split(' ')
                if x[0][0] != '#':
                    self.serverName = x[1].strip()
                else:
                    print('Server name disabled')
            
            elif 'set_pass ' in line:
                x = line.split(' ')
                if x[0][0] != '#':
                    self.password = x[1].strip()
                else:
                    print('Password disabled')

            elif 'set_pass_admin ' in line:
                x = line.split(' ')
                if x[0][0] != '#':
                    self.adminPassword = x[1].strip()
                else:
                    print('Admin password disabled')

            elif 'set_welcome_message ' in line:
                x = line.split(' ')
                if x[0][0] != '#':
                    self.welcomeMessage = x[1:]
                else:
                    print('Welcome message disabled')

            elif 'set_team_point_limit ' in line:
                x = line.split(' ')
                if x[0][0] != '#':
                    self.pointLimit = x[1].strip()
                else:
                    print('Team point limit disabled')

            elif 'set_port ' in line:
                x = line.split(' ')
                if x[0][0] != '#':
                    self.port = x[1].strip()
                else:
                    print('Port disabled')

            elif 'set_max_players ' in line:
                x = line.split(' ')
                if x[0][0] != '#':
                    self.maxPlayers = x[1].strip()
                    self.maxReserved = x[2].strip()
                else:
                    print('Max players disabled')

            elif 'set_mission ' in line:
                x = line.split(' ')
                if x[0][0] != '#':
                    self.gamemodeValue = x[1].strip()
                    if self.gamemodeValue == 'multiplater_bt':
                        self.gamemodeValue = 'Battle'
                
        
        label = tkinter.Label(self, text="Server Settings", font=LARGE_FONT)
        label.grid(row=0, column=1, stick="nsew", padx=10, pady=10, columnspan=2)

        button1 = ttk.Button(self, text="Admins", command=lambda: controller.show_frame(PageOne))
        button1.grid(row=10, column=2, stick="nsew", padx=(2,0), pady=5, columnspan=1)
        button2 = ttk.Button(self, text="Save", command=lambda: popupmsg('WIP'))
        button2.grid(row=10, column=1, stick="nsew", padx=(0,2), pady=5, columnspan=1)

        serverNameLabel = tkinter.Label(self, text="Server Name: ", font=NORM_FONT)
        serverNameLabel.grid(row=1, column=0, stick="w", padx=(10,0))
        serverNameInput = ttk.Entry(self, state='normal', width=40)
        serverNameInput.grid(row=1, column=1, stick="w", columnspan=2, rowspan=1, padx=0, pady=4)        
        if self.serverName != None:
            serverNameInput.insert(0, self.serverName)

        serverPassLabel = tkinter.Label(self, text="Password: ", font=NORM_FONT)
        serverPassLabel.grid(row=2, column=0, stick="w", padx=(10,0))
        serverPassInput = ttk.Entry(self, state='normal', width=40)
        serverPassInput.grid(row=2, column=1, stick="w", columnspan=2, rowspan=1, padx=0, pady=4)        
        if self.password != None:
            serverPassInput.insert(0, self.password)

        adminPassLabel = tkinter.Label(self, text="Admin Password: ", font=NORM_FONT)
        adminPassLabel.grid(row=3, column=0, stick="w", padx=(10,0))
        adminPassInput = ttk.Entry(self, state='normal', width=40)
        adminPassInput.grid(row=3, column=1, stick="w", columnspan=2, rowspan=1, padx=0, pady=4)        
        if self.adminPassword != None:
            adminPassInput.insert(0, self.adminPassword)


        welcomeMessageLabel = tkinter.Label(self, text="Welcome Message: ", font=NORM_FONT)
        welcomeMessageLabel.grid(row=4, column=0, stick="w", padx=(10,0))
        welcomeMessageInput = tkinter.Text(self, state='normal', width=30, height=3, wrap='word')
        welcomeMessageInput.grid(row=4, column=1, stick="w", columnspan=2, rowspan=1, padx=0, pady=4)        
        if self.welcomeMessage != None:
            welcomeMessageInput.insert('end', self.welcomeMessage)
            
        gamemode = "Battle"
        gamemodeOptions = ("Battle","Deathmatch","Team deathmatch","Capture the flag","Duel")
        gamemode = tkinter.StringVar()
        gamemode.set(gamemodeOptions[0])
        gamemodeLabel = tkinter.Label(self, text="Gamemode: ", font=NORM_FONT)
        gamemodeLabel.grid(row=5, column=0, stick="w", padx=(10,0))
        gamemodeInput = ttk.OptionMenu(self, gamemode, *gamemodeOptions)
        gamemodeInput.config(width=35)
        gamemodeInput.grid(row=5, column=1, stick="w", columnspan=2, rowspan=1, padx=0, pady=4)        

        pointLimitLabel = tkinter.Label(self, text="Team point limit: ", font=NORM_FONT)
        pointLimitLabel.grid(row=6, column=0, stick="w", padx=(10,0))
        pointLimitInput = ttk.Entry(self, state='normal', width=40)
        pointLimitInput.grid(row=6, column=1, stick="w", columnspan=2, rowspan=1, padx=0, pady=4)        
        if self.pointLimit != None:
            pointLimitInput.insert(0, self.pointLimit)

        portLabel = tkinter.Label(self, text="Port: ", font=NORM_FONT)
        portLabel.grid(row=7, column=0, stick="w", padx=(10,0))
        portInput = ttk.Entry(self, state='normal', width=40)
        portInput.grid(row=7, column=1, stick="w", columnspan=2, rowspan=1, padx=0, pady=4)        
        if self.port != None:
            portInput.insert(0, self.port)

        maxPlayersLabel = tkinter.Label(self, text="Max players: ", font=NORM_FONT)
        maxPlayersLabel.grid(row=8, column=0, stick="w", padx=(10,0))
        maxPlayersInput = ttk.Entry(self, state='normal', width=19)
        maxPlayersInput.grid(row=8, column=1, stick="w", columnspan=1, rowspan=1, padx=0, pady=4)        
        if self.maxPlayers != None:
            maxPlayersInput.insert(0, self.maxPlayers)

        #maxReservesLabel = tkinter.Label(self, text="Max players: ", font=NORM_FONT)
        #maxReservesLabel.grid(row=8, column=0, stick="w", padx=(10,0))
        maxReservesInput = ttk.Entry(self, state='normal', width=19)
        maxReservesInput.grid(row=8, column=2, stick="e", columnspan=1, rowspan=1, padx=0, pady=4)        
        if self.maxReserved != None:
            maxReservesInput.insert(0, self.maxReserved)

class PageOne(tkinter.Frame):

    def __init__(self, parent, controller):
        tkinter.Frame.__init__(self,parent)

        adminList, adminCount, slotCount, data, lineNo = self.adminScript()
        self.adminCount = adminCount
        self.slotCount = slotCount
        
        label1 = tkinter.Label(self, text="Admin List", font=LARGE_FONT)
        label1.grid(row=0, column=1, stick="nsew", padx=10, pady=10)

        button1 = ttk.Button(self, text="Back", command=lambda: controller.show_frame(ServerSettings))
        button1.grid(row=0, column=0, stick="nw", padx=10, pady=10)

        self.label2 = tkinter.Label(self, text=(str(adminCount) + '/' + str(slotCount)), font=LARGE_FONT)
        self.label2.grid(row=0, column=3, stick="e", padx=10, pady=10)

        guidInput = ttk.Entry(self, state='normal', width=20)
        guidInput.grid(row=4, column=0, stick="nsew", columnspan=1, rowspan=1, padx=(10,4), pady=10)

        checkButton = ttk.Button(self, text="Check", command=lambda: self.checkAdmin(adminList, guidInput.get()))
        checkButton.grid(row=4, column=1, stick="nsew", columnspan=1, rowspan=1, pady=10)

        addButton = ttk.Button(self, text="Add", command=lambda: self.addAdmin(adminList, guidInput.get()))
        addButton.grid(row=4, column=2, stick="nsew", columnspan=1, rowspan=1, pady=10)

        removeButton = ttk.Button(self, text="Remove", command=lambda: self.removeAdmin(adminList, guidInput.get()))
        removeButton.grid(row=4, column=3, stick="nsew", columnspan=1, rowspan=1, pady=10, padx=(0,10))

        updateButton = ttk.Button(self, text="Update", command=lambda: self.updateScript(adminList, data, lineNo))
        updateButton.grid(row=6, column=3, stick="nsew", columnspan=1, rowspan=1, pady=10, padx=(0,10))

        self.writeToLog(adminList)

    def writeToLog(self, msg):

        log = tkinter.Text(self, state='disabled', width=86, height=12, wrap='word')
        log.grid(row=1, column=0, stick="nsew", columnspan=4, rowspan=3, padx=10)

        numlines = log.index('end - 1 line').split('.')[0]
        log['state'] = 'normal'
        if numlines==12:
            log.delete(1.0, 2.0)
        if log.index('end-1c')!='1.0':
            log.insert('end', '\n')
        log.insert('end', msg)
        log['state'] = 'disabled'

    def adminScript(self):
        try:
            scriptfile = open("../modules/Napoleonic wars/scripts.txt", "r")
        except Exception as e:
            print("No script file found!")
            print("Error: {}".format(e))

        data = scriptfile.readlines()

        adminString = ""
        adminList = []
        splitter = " 2147483679 2 1224979098644774913"
        startString = " 304 23 2 1224979098644774912 1 4 0 418 0 401 1 1224979098644774912 2147483679 2 1224979098644774912 0 430 1 1224979098644774912 441 2 1224979098644774913 1224979098644774912 2147483679 2 1224979098644774913 "
        lastString = "429 2 1224979098644774912 0 2350 2 2 1224979098644774912 2320 2 4 216172782113784513 1 1 160 466 3 1224979098644774912 0 0 3 0 \n"
        adminCount = 0

        x = -1
        lineNo = 0
        for line in data:
            x += 1
            if "304 23 2 1224979098644774912" in line:
                lineNo = x
                adminString = line
                adminString = adminString.replace(" 304 23 2 1224979098644774912 1 4 0 418 0 401 1 1224979098644774912 2147483679 2 1224979098644774912 0 430 1 1224979098644774912 441 2 1224979098644774913 1224979098644774912 2147483679 2 1224979098644774913 ", "")
                adminString = adminString.replace(" 429 2 1224979098644774912 0 2350 2 2 1224979098644774912 2320 2 4 216172782113784513 1 1 160 466 3 1224979098644774912 0 0 3 0 \n", "")

                for splitter in adminString:
                    adminString = adminString.replace(" 2147483679 2 1224979098644774913", "")
                adminList = adminString.split(" ")

        scriptfile.close()

        def adminCounter():
            adminCount = 0
            slotCount = 0
            for item in adminList:
                slotCount += 1
                if len(item) < 10:
                    adminCount += 1
            return adminCount, slotCount

        adminCount, slotCount = adminCounter()

        return adminList, adminCount, slotCount, data, lineNo

##    def displayAdmins():
##        #print(adminList)
##        adminListPure = open("players/adminListPure", "w")
##        adminListPure.write(str(adminList))
##        adminListPure.close()
##        return adminList

    def checkAdmin(self, adminList, guid):
        if guid in adminList:
            print('True')
            return True
        else:
            print('False')
            return False

    def removeAdmin(self, adminList, guid):
        try:
            index = adminList.index(guid)
            adminList[index] = "9999999999999"
            print("Removed admin with GUID: " + str(guid))
            self.writeToLog(adminList)
            self.adminCount -= 1
            self.label2['text'] = (str(self.adminCount) + '/' + str(self.slotCount))
            return True, adminList
        except ValueError:
            print('This admin is not in the list')
            return False

    def addAdmin(self, adminList, guid):
        # Check if this GUID already exists
        x = self.checkAdmin(adminList,guid)
        if x == False:
            try:
                index = adminList.index("9999999999999")
                adminList[index] = str(guid)
                print("Added admin with GUID: " + str(guid))
                self.writeToLog(adminList)
                self.adminCount += 1
                self.label2['text'] = (str(self.adminCount) + '/' + str(self.slotCount))
                return True, adminList
            except ValueError:
                print('Something went wrong ...')
                return False
        else:
            print('This GUID already exists!')
            return False

    def compileAdmins(self, adminList):
        compiledAdmins = " 304 23 2 1224979098644774912 1 4 0 418 0 401 1 1224979098644774912 2147483679 2 1224979098644774912 0 430 1 1224979098644774912 441 2 1224979098644774913 1224979098644774912 2147483679 2 1224979098644774913 "
        splitter = " 2147483679 2 1224979098644774913"
        lastString = "429 2 1224979098644774912 0 2350 2 2 1224979098644774912 2320 2 4 216172782113784513 1 1 160 466 3 1224979098644774912 0 0 3 0 \n"
        for admin in adminList:
            compiledAdmins = compiledAdmins + admin + splitter + ' '
        compiledAdmins = compiledAdmins[0:len(compiledAdmins)-33]
        compiledAdmins = compiledAdmins + lastString
        print('Script file compiled')
        return compiledAdmins

    def updateScript(self, adminList, data, lineNo):
        date = str(datetime.date.today())
        backupFile = open("backup/backup_scripts_{}.txt".format(date), "w")
        backupFile.writelines(data)
        backupFile.close()
        
        scriptfile = open("../modules/Napoleonic wars/scripts.txt", "w")

        admins = self.compileAdmins(adminList)
        
        data[lineNo] = admins
        scriptfile.writelines(data)
        scriptfile.close()

class OnlinePlayers(tkinter.Frame):
    # Online Players

    def __init__(self, parent, controller):
        tkinter.Frame.__init__(self,parent)

        onlinePlayersFile = open("players/onlinePlayers", "r", encoding='utf8')
        self.onlinePlayers = onlinePlayersFile.readlines()
        onlinePlayersFile.close()
        
        label1 = tkinter.Label(self, text="Online Players", font=LARGE_FONT)
        label1.grid(row=0, column=1, stick="nsew", padx=10, pady=10)

        button1 = ttk.Button(self, text="Back", command=lambda: controller.show_frame(ServerSettings))
        button1.grid(row=0, column=0, stick="nw", padx=10, pady=10)

##        self.label2 = tkinter.Label(self, text=(str(adminCount) + '/' + str(slotCount)), font=LARGE_FONT)
##        self.label2.grid(row=0, column=3, stick="e", padx=10, pady=10)

        checkButton = ttk.Button(self, text="Refresh", command=lambda: self.refresh())
        checkButton.grid(row=4, column=1, stick="nsew", columnspan=1, rowspan=1, pady=10)

        self.writeToLog(self.onlinePlayers)

    def refresh(self):
        onlinePlayersFile = open("players/onlinePlayers", "r", encoding='utf8')
        self.onlinePlayers = onlinePlayersFile.readlines()
        onlinePlayersFile.close()
        self.writeToLog(self.onlinePlayers)

    def writeToLog(self, msg):

        log = tkinter.Text(self, state='disabled', width=86, height=12, wrap='word')
        log.grid(row=1, column=0, stick="nsew", columnspan=4, rowspan=3, padx=10)

        numlines = log.index('end - 1 line').split('.')[0]
        log['state'] = 'normal'
        if numlines==12:
            log.delete(1.0, 2.0)
        if log.index('end-1c')!='1.0':
            log.insert('end', '\n')
        log.insert('end', msg)
        log['state'] = 'disabled'

app = ServerManagerApp()
app.geometry("720x620")
app.mainloop()
        
    
