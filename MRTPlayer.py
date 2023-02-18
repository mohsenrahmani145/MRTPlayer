import json
from time import time
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sys
import os
import datetime
from tkinter import filedialog
from pygame import mixer, error
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
import Style


class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        try:
            mixer.init()

        except error:
            err = QMessageBox()
            err.setWindowTitle('Error')
            err.setText("Audio device not found")
            err.setIcon(QMessageBox.Icon.Critical)
            err.setWindowIcon(QIcon('icon.png'))
            err.show()
            sys.exit(err.exec())

        self.first_time = time()
        self.secound_time = 0
        self.pathdir = os.path.expanduser('~')
        os.chdir(f'{self.pathdir}\Documents\MRTPlayer')

        self.setAcceptDrops(True)
        self.setWindowTitle("Music Player")
        self.setMinimumSize(500, 500)
        self.setWindowIcon(QIcon('icon.png'))

        self.dark_mode_enabled = False
        self.file_argv = None
        self.p = None
        self.s = None
        self.checker = None
        self.status_media = "stoped"  # "playing" , "stoped" , 'paused'
        self.create_menu_bar()
        self.create_main()
        self.create_button()
        self.create_shortcut()
        self.processArgument()
        self.pathChecker()
        self.bindSocket()
        self.load_settings()
        self.apply_settings()
  
    def load_settings(self):
        with open('settings.json', 'r') as f:
            self.settings = json.load(f)

    def apply_settings(self):
        if self.settings['mute'] == True:
            self.volume_slider.setValue(int(self.settings['volume']*100))
            self.mute()
        else:
            self.volume_slider.setValue(int(self.settings['volume']*100))
        if self.settings['darkmode'] == True:
            self.dark_mode()
        if self.settings['repeat'] == True:
            self.repeat()
        self.resize(self.settings['sizewindow'][0],self.settings['sizewindow'][1])

    def resizeEvent(self, event):
        window_size = self.size()
        self.volume_button.setGeometry(window_size.width()-92, 22, 92, 50)
        self.volume_slider.setGeometry(window_size.width()-35, 80, 20, 150)
        self.pause_button.setGeometry(int(window_size.width()/5)*0, window_size.height()-50, int(window_size.width()/5), 50)
        self.resume_button.setGeometry(int(window_size.width()/5)*1, window_size.height()-50, int(window_size.width()/5), 50)
        self.play_button.setGeometry(int(window_size.width()/5)*2, window_size.height()-50, int(window_size.width()/5), 50)
        self.stop_button.setGeometry(int(window_size.width()/5)*3, window_size.height()-50, int(window_size.width()/5), 50)
        self.import_button.setGeometry(int(window_size.width()/5)*4, window_size.height()-50, int(window_size.width()/5), 50)
        self.time_elapsed.move(10, window_size.height()-75)
        self.time_ended.move(window_size.width()-75, window_size.height()-80)
        self.label_track.setGeometry(0, window_size.height()-114, window_size.width(), 35)
        self.label_artist.setGeometry(0, window_size.height()-142, window_size.width(), 30)
        self.timeline_slider.setGeometry(81, window_size.height()-74, window_size.width()-160, 20)
        self.cover.setGeometry(0, 50, window_size.width(), window_size.height()-200)
        if window_size.width() <= window_size.height():
            self.scaleCalculation = window_size.width()-200
            self.cover.setPixmap(self.pixmap.scaled(self.scaleCalculation,self.scaleCalculation))
        elif window_size.width() > window_size.height():
            self.scaleCalculation = window_size.height()-200
            self.cover.setPixmap(self.pixmap.scaled(self.scaleCalculation,self.scaleCalculation))
        
        self.settings['sizewindow'] = [window_size.width(),window_size.height()]
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f)

    def create_shortcut(self):
        self.toggleplaypause_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_MediaTogglePlayPause), self)
        self.toggleplaypause_shortcut.activated.connect(
            self.actiontoggleplaypause_shortcut)
        self.stop_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_MediaStop), self)
        self.stop_shortcut.activated.connect(self.stopsong)
        self.previous_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_MediaPrevious), self)
        self.previous_shortcut.activated.connect(self.playsong)

    def actiontoggleplaypause_shortcut(self):
        if self.status_media == "stoped":
            self.playsong()
        elif self.status_media == "paused":
            self.resumesong()
        elif self.status_media == "playing":
            self.pausesong()

    def create_menu_bar(self):
        self.menubar = self.menuBar().addMenu("File")

        self.open_menu = self.menubar.addAction('Open', self.importfile)
        self.open_menu.setIcon(QIcon('icons/icon_open.png'))

        separator = self.menubar
        separator.addSeparator()

        self.play_menu = self.menubar.addAction('Play', self.playsong)
        self.play_menu.setIcon(QIcon('icons/icon_play.png'))

        self.stop_menu = self.menubar.addAction('Stop', self.stopsong)
        self.stop_menu.setIcon(QIcon('icons/icon_stop.png'))

        self.pause_menu = self.menubar.addAction('Pause', self.pausesong)
        self.pause_menu.setIcon(QIcon('icons/icon_pause.png'))
        self.pause_menu.setEnabled(False)

        self.resume_menu = self.menubar.addAction('Resume', self.resumesong)
        self.resume_menu.setIcon(QIcon('icons/icon_resume.png'))
        self.resume_menu.setEnabled(False)

        separator.addSeparator()

        self.repeat_menu = self.menubar.addAction('Repeat On', self.repeat)
        self.repeat_menu.setIcon(QIcon('icons/icon_repeat.png'))

        self.mute_menu = self.menubar.addAction('Mute', self.mute)
        self.mute_menu.setIcon(QIcon('icons/icon_unmute.png'))
        self.mute_menu.setCheckable(True)

        separator.addSeparator()

        self.exit_menu = self.menubar.addAction('Exit', self.exitprogram)
        self.exit_menu.setIcon(QIcon('icons/icon_exit.png'))

        self.menubar2 = self.menuBar().addMenu("View")
        self.darkmode = self.menubar2.addAction('Dark Mode', self.dark_mode)

        self.menubar3 = self.menuBar()
        self.menubar3.addAction('About', self.show_about)

    def create_main(self):
        self.cover = QLabel(self)

        self.pixmap = QPixmap('Untitledcover.png')

        self.cover.setPixmap(self.pixmap.scaled(300, 300))
        self.cover.setGeometry(0, 50, 500, 300)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_artist = QLabel("", self)
        self.label_artist.setText("Artist")
        self.label_artist.setFont(QFont('Arial', 20))
        self.label_artist.setGeometry(0, 357, 500, 30)
        self.label_artist.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_track = QLabel("", self)
        self.label_track.setText("Track")
        self.label_track.setFont(QFont('Arial', 23))
        self.label_track.setGeometry(0, 385, 500, 35)
        self.label_track.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.time_elapsed = QLabel("0:00:00", self)
        self.time_elapsed.setFont(QFont('Arial', 15))
        self.time_elapsed.move(10, 425)
        self.time_elapsed.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.timer = QTimer()
        self.timer.timeout.connect(self.time_counter)

        self.time_ended = QLabel("0:00:00", self)
        self.time_ended.setFont(QFont('Arial', 15))
        self.time_ended.move(425, 420)

        self.volume_slider = QSlider(self)
        self.volume_slider.setOrientation(Qt.Orientation.Vertical)
        self.volume_slider.setGeometry(465, 80, 20, 150)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.volume_changed)

        self.timeline_slider = QSlider(self)
        self.timeline_slider.setOrientation(Qt.Orientation.Horizontal)
        self.timeline_slider.setGeometry(81, 426, 340, 20)
        self.timeline_slider.setEnabled(False)
        self.timeline_slider.sliderMoved.connect(self.set_timeline_pos)

    def create_button(self):
        self.import_button = QPushButton("Open", self)
        self.import_button.setGeometry(400, 450, 100, 50)
        self.import_button.setIcon(QIcon('icons/icon_open.png'))
        self.import_button.setIconSize(QSize(23, 23))
        self.import_button.clicked.connect(self.importfile)

        self.pause_button = QPushButton("Pause", self)
        self.pause_button.setGeometry(0, 450, 100, 50)
        self.pause_button.setIcon(QIcon('icons/icon_pause.png'))
        self.pause_button.clicked.connect(self.pausesong)
        self.pause_button.setEnabled(False)

        self.resume_button = QPushButton("Resume", self)
        self.resume_button.setGeometry(100, 450, 100, 50)
        self.resume_button.setIcon(QIcon('icons/icon_resume.png'))
        self.resume_button.setIconSize(QSize(23, 23))
        self.resume_button.clicked.connect(self.resumesong)
        self.resume_button.setEnabled(False)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.setGeometry(300, 450, 100, 50)
        self.stop_button.setIcon(QIcon('icons/icon_stop.png'))
        self.stop_button.clicked.connect(self.stopsong)

        self.play_button = QPushButton("Play", self)
        self.play_button.setGeometry(200, 450, 100, 50)
        self.play_button.setIcon(QIcon('icons/icon_play.png'))
        self.play_button.clicked.connect(self.playsong)

        self.volume_button = QPushButton(self)
        self.volume_button.setGeometry(408, 22, 92, 50)
        self.volume_button.setIcon(QIcon('icons/icon_unmute.png'))
        self.volume_button.setIconSize(QSize(40, 40))
        self.volume_button.clicked.connect(self.mute)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            self.importfileargv(file_path)

    def show_about(self):
        self.message = QMessageBox(self)
        self.message.setWindowTitle('About')
        self.message.setText("Version: 2.5.1\nDeveloper: Mohsen Rahmani")
        self.message.setIcon(QMessageBox.Icon.Information)
        self.message.setWindowIcon(QIcon('icon.png'))
        self.message.exec()

    def file_dialog(self):
        return filedialog.askopenfilename(filetypes=[("Mp3 Files", "*.mp3")], title="Select A File")

    def get_id3(self, path):
        try:
            file = ID3(str(path))
            title = file.get('TIT2')
            self.label_track.setToolTip(str(title))
            artist = file.get('TPE1')
            self.label_artist.setToolTip(str(artist))
            if title == None or artist == None:
                title = (str(path).split('/')[-1])
                artist = ""
                self.label_artist.setToolTip(str(artist))
                self.label_track.setToolTip(str(title))
            print([str(title), str(artist)])
            if len(str(title)) > 25:
                title = str(title)[0:25] + '...'
            if len(str(artist)) > 25:
                artist = str(artist)[0:25] + '...'
            return [str(title), str(artist)]
        except:
            message = QMessageBox(self)
            message.setWindowTitle('Error')
            message.setText(
                "We can't open this file. This may be because the file type is unsupported, the file extension is incorrect or the file is corrupt.")
            message.setIcon(QMessageBox.Icon.Critical)
            message.setWindowIcon(QIcon('icon.png'))
            self.stopsong()
            self.cover.setPixmap(QPixmap('Untitledcover.png').scaled(300, 300))
            self.label_artist.setText('Artist')
            self.label_track.setText('Track')
            self.time_ended.setText('0:00:00')
            message.exec()

    def get_cover_img(self, path):
        try:
            file = ID3(str(path))
            pic = file.get('APIC:').data
            ba = QByteArray(pic)
            self.pixmap = QPixmap()
            self.pixmap.loadFromData(ba, "JPG")            
            self.cover.setPixmap(self.pixmap.scaled(self.scaleCalculation, self.scaleCalculation))
        except:
            self.pixmap = QPixmap('Untitledcover.png')
            self.cover.setPixmap(self.pixmap.scaled(self.scaleCalculation, self.scaleCalculation))

    def importfileargv(self, argv):
        try:
            file = str(argv).replace('\\', '/')
            mixer.music.load(file)
            id3 = self.get_id3(file)
            self.label_artist.setText(id3[1])
            self.label_track.setText(id3[0])
            self.get_time_length(file)
            self.get_cover_img(file)
            self.playsong()

        except:
            pass

    def importfile(self):
        try:
            file = self.file_dialog()
            mixer.music.load(file)
            id3 = self.get_id3(file)
            self.label_artist.setText(id3[1])
            self.label_track.setText(id3[0])
            self.get_time_length(file)
            self.get_cover_img(file)
            self.playsong()
        except:
            pass

    def pausesong(self):
        mixer.music.pause()
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(True)
        self.pause_menu.setEnabled(False)
        self.resume_menu.setEnabled(True)
        self.timer.stop()
        self.status_media = "paused"

    def stopsong(self):
        mixer.music.stop()
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)
        self.pause_menu.setEnabled(False)
        self.resume_menu.setEnabled(False)
        self.timer.stop()
        self.time_elapsed.setText('0:00:00')
        self.timeline_slider.setEnabled(False)
        self.status_media = "stoped"

    def resumesong(self):
        self.first_time, self.secound_time
        mixer.music.unpause()
        self.pause_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.pause_menu.setEnabled(True)
        self.resume_menu.setEnabled(False)
        self.first_time = (time()*1000) - self.secound_time
        self.timer.start(300)
        self.status_media = "playing"

    def dark_mode(self):
        if self.dark_mode_enabled == False:
            self.setStyleSheet(Style.stylesheet)
            if mixer.music.get_volume() != 0.0:
                self.volume_button.setIcon(QIcon('icons1/icon_unmute.png'))
                self.mute_menu.setIcon(QIcon('icons1/icon_unmute.png'))
            else:
                self.volume_button.setIcon(QIcon('icons1/icon_mute.png'))
                self.mute_menu.setIcon(QIcon('icons1/icon_mute.png'))
            self.play_button.setIcon(QIcon('icons1/icon_play.png'))
            self.stop_button.setIcon(QIcon('icons1/icon_stop.png'))
            self.resume_button.setIcon(QIcon('icons1/icon_resume.png'))
            self.pause_button.setIcon(QIcon('icons1/icon_pause.png'))
            self.import_button.setIcon(QIcon('icons1/icon_open.png'))
            self.play_menu.setIcon(QIcon('icons1/icon_play.png'))
            self.stop_menu.setIcon(QIcon('icons1/icon_stop.png'))
            self.resume_menu.setIcon(QIcon('icons1/icon_resume.png'))
            self.pause_menu.setIcon(QIcon('icons1/icon_pause.png'))
            self.open_menu.setIcon(QIcon('icons1/icon_open.png'))
            self.exit_menu.setIcon(QIcon('icons1/icon_exit.png'))
            self.repeat_menu.setIcon(QIcon('icons1/icon_repeat.png'))
            self.darkmode.setText("Light Mode")
            self.dark_mode_enabled = True

        elif self.dark_mode_enabled == True:
            self.setStyleSheet("")
            if mixer.music.get_volume() != 0.0:
                self.volume_button.setIcon(QIcon('icons/icon_unmute.png'))
                self.mute_menu.setIcon(QIcon('icons/icon_unmute.png'))
            else:
                self.volume_button.setIcon(QIcon('icons/icon_mute.png'))
                self.mute_menu.setIcon(QIcon('icons/icon_mute.png'))
            self.play_button.setIcon(QIcon('icons/icon_play.png'))
            self.stop_button.setIcon(QIcon('icons/icon_stop.png'))
            self.resume_button.setIcon(QIcon('icons/icon_resume.png'))
            self.pause_button.setIcon(QIcon('icons/icon_pause.png'))
            self.import_button.setIcon(QIcon('icons/icon_open.png'))
            self.play_menu.setIcon(QIcon('icons/icon_play.png'))
            self.stop_menu.setIcon(QIcon('icons/icon_stop.png'))
            self.resume_menu.setIcon(QIcon('icons/icon_resume.png'))
            self.pause_menu.setIcon(QIcon('icons/icon_pause.png'))
            self.open_menu.setIcon(QIcon('icons/icon_open.png'))
            self.exit_menu.setIcon(QIcon('icons/icon_exit.png'))
            self.repeat_menu.setIcon(QIcon('icons/icon_repeat.png'))
            self.darkmode.setText("Dark Mode")
            self.dark_mode_enabled = False
        
        self.settings['darkmode'] = self.dark_mode_enabled
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f)

    def mute(self):
        if mixer.music.get_volume() != 0.0:
            mixer.music.set_volume(0.0)
            if self.dark_mode_enabled == False:
                self.volume_button.setIcon(QIcon('icons/icon_mute.png'))
                self.mute_menu.setIcon(QIcon('icons/icon_mute.png'))
            else:
                self.volume_button.setIcon(QIcon('icons1/icon_mute.png'))
                self.mute_menu.setIcon(QIcon('icons1/icon_mute.png'))
            self.mute_menu.setChecked(True)
            self.mute_menu.setText('Unmute')
            self.settings['mute'] = True
            with open('settings.json', 'w') as f:
                json.dump(self.settings, f)
        elif mixer.music.get_volume() == 0.0:
            mixer.music.set_volume(self.volume_slider.value()/100)
            if self.volume_slider.value()/100 != 0.0:
                if self.dark_mode_enabled == False:
                    self.volume_button.setIcon(QIcon('icons/icon_unmute.png'))
                    self.mute_menu.setIcon(QIcon('icons/icon_unmute.png'))
                else:
                    self.volume_button.setIcon(QIcon('icons1/icon_unmute.png'))
                    self.mute_menu.setIcon(QIcon('icons1/icon_unmute.png'))
                self.mute_menu.setChecked(False)
                self.mute_menu.setText('Mute')
            self.settings['mute'] = False
            with open('settings.json', 'w') as f:
                json.dump(self.settings, f)

    def volume_changed(self):
        value = self.volume_slider.value()/100
        mixer.music.set_volume(value)
        if mixer.music.get_volume() != 0.0:
            if self.dark_mode_enabled == False:
                self.volume_button.setIcon(QIcon('icons/icon_unmute.png'))
                self.mute_menu.setIcon(QIcon('icons/icon_unmute.png'))
            else:
                self.volume_button.setIcon(QIcon('icons1/icon_unmute.png'))
                self.mute_menu.setIcon(QIcon('icons1/icon_unmute.png'))

            self.mute_menu.setChecked(False)
            self.mute_menu.setText('Mute')
        else:
            if self.dark_mode_enabled == False:
                self.volume_button.setIcon(QIcon('icons/icon_mute.png'))
                self.mute_menu.setIcon(QIcon('icons/icon_mute.png'))
            else:
                self.volume_button.setIcon(QIcon('icons1/icon_mute.png'))
                self.mute_menu.setIcon(QIcon('icons1/icon_mute.png'))

            self.mute_menu.setChecked(True)
            self.mute_menu.setText('Unmute')

        self.settings['volume'] = value
        self.settings['mute'] = False
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f)
        
    def playsong(self):
        try:
            self.first_time
            mixer.music.play()
            self.pause_button.setEnabled(True)
            self.resume_button.setEnabled(False)
            self.pause_menu.setEnabled(True)
            self.resume_menu.setEnabled(False)
            self.timeline_slider.setEnabled(True)
            self.first_time = time()*1000
            self.timer.start(300)
            self.status_media = "playing"
            pathfile = open("path.pth", 'w')
            pathfile.write("")
            pathfile.close()

        except:
            self.stopsong()

    def get_time_length(self, file):
        length = int(MP3(f"{file}").info.length)
        result = str(datetime.timedelta(seconds=length))
        self.time_ended.setText(result)
        self.timeline_slider.setMinimum(0)
        self.timeline_slider.setMaximum(length*1000)

    def set_timeline_pos(self):
        try:
            self.secound_time, self.first_time
            self.timer.stop()
            value = self.timeline_slider.value()
            self.first_time = (time()*1000) - value
            mixer.music.set_pos(value/1000)
            if mixer.music.get_busy() == False:
                self.resumesong()
            self.timer.start(300)
        except:
            pass

    def time_counter(self):
        self.secound_time
        get_pos = (time()*1000)-self.first_time
        sec = int(get_pos/1000)
        result = str(datetime.timedelta(seconds=sec))
        self.time_elapsed.setText(result)
        self.timeline_slider.setValue(int(get_pos))
        self.secound_time = get_pos
        if mixer.music.get_pos() == -1:
            if self.repeat_menu.isCheckable():
                self.playsong()
            else:
                self.stopsong()

    def path_checker(self):
        self.s
        f = None
        self.p
        if self.s != self.p:
            self.importfileargv(self.s)
            self.p = self.s
        f = open("path.pth", 'r')
        self.s = str(f.read())

    def repeat(self):

        if self.repeat_menu.isCheckable() == False:
            self.repeat_menu.setCheckable(True)
            self.repeat_menu.setChecked(True)
            self.repeat_menu.setText('Repeat Off')

        else:
            self.repeat_menu.setCheckable(False)
            self.repeat_menu.setChecked(False)
            self.repeat_menu.setText('Repeat On')

        self.settings['repeat'] = self.repeat_menu.isCheckable()
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f)

    def processArgument(self):
        try:
            if sys.argv[1].lower().split('.')[-1] == 'mp3':
                file_argv = sys.argv[1]
                self.p = str(file_argv)
                self.f = open("path.pth", 'w')
                self.f.write(f"{self.p}")
                self.f.close()
                self.f = open("path.pth", 'r')
                self.s = str(self.f.read())
                self.importfileargv(file_argv)
        except:
            pass

    def pathChecker(self):
        self.checker = QTimer()
        self.checker.timeout.connect(self.path_checker)
        self.checker.start(10)

    def exitprogram(self):
        os.remove('program.lock')
        sys.exit()

    def bindSocket(self):

        self.lock_file = 'program.lock'

        if os.path.isfile(self.lock_file):
            print("Program is already running.")
            sys.exit()
        else:
            open(self.lock_file, 'w').close()

app = QApplication(sys.argv)
window = MusicPlayer()
window.show()
app.exec()
os.remove('program.lock')
sys.exit()
