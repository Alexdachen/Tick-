# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 14:37:53 2018

@author: J
"""

import sys
from PyQt4 import QtGui,QtCore
#from PyQt4 import QtGui,QtCore
#from qtpy import QtWidgets, QtGui, QtCore
from pymongo import MongoClient
import matplotlib.dates as mpd
sys.path.append('..')
import pyqtgraph as pg
import datetime as dt          
import pytz

class Crosshair(object):
    """
    此类给pg.PlotWidget()添加crossHair功能
    PlotWidget实例需要初始化时传入
    根据PlotWidget的x坐标刻度依据，需要定义一个getTickDatetimeByXPosition方法
    """
    #----------------------------------------------------------------------
    def __init__(self,parent):
        """Constructor"""
        self.__view = parent
        
        super(Crosshair, self).__init__()
        self.__vLine = pg.InfiniteLine(angle=90, movable=False)
        self.__hLine = pg.InfiniteLine(angle=0, movable=False)
        self.__textPrice = pg.TextItem('price')
        self.__textDate = pg.TextItem('date')
        
        #mid 在y轴动态跟随最新价显示最新价和最新时间
        self.__textLastPrice = pg.TextItem('lastTickPrice')    
        
        view = self.__view
        
        view.addItem(self.__textDate, ignoreBounds=True)
        view.addItem(self.__textPrice, ignoreBounds=True)        
        view.addItem(self.__vLine, ignoreBounds=True)
        view.addItem(self.__hLine, ignoreBounds=True)    
        view.addItem(self.__textLastPrice, ignoreBounds=True)     
        self.proxy = pg.SignalProxy(view.scene().sigMouseMoved, rateLimit=60, slot=self.__mouseMoved)        
        
    #----------------------------------------------------------------------
    def __mouseMoved(self,evt):
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        view = self.__view
        if not view.sceneBoundingRect().contains(pos):
            return
        mousePoint = view.plotItem.vb.mapSceneToView(pos)        
        xAxis = mousePoint.x()
        yAxis = mousePoint.y()    
        
        #mid 1)set contents to price and date lable
        self.__vLine.setPos(xAxis)
        self.__hLine.setPos(yAxis)      
        
        getTickDatetimeByXPosition = None
        if(hasattr(view, 'getTickDatetimeByXPosition')):
            getTickDatetimeByXPosition = getattr(view, 'getTickDatetimeByXPosition')
        else:
            getTickDatetimeByXPosition = self.__getTickDatetimeByXPosition

        if(not getTickDatetimeByXPosition):
            return
        tickDatetime = getTickDatetimeByXPosition(xAxis) 
        if(isinstance(tickDatetime,dt.datetime)):
            tickDatetimeStr = "%s" % (dt.datetime.strftime(tickDatetime,'%Y-%m-%d %H:%M:%S.%f'))          
        elif(isinstance(tickDatetime,float)):
            tickDatetimeStr = "%.10f" % (tickDatetime)
            #print tickDatetimeStr
        elif(isinstance(tickDatetime,str)):
            tickDatetimeStr = tickDatetime
        else:
            tickDatetime = "wrong value."
            
        
        if(True):
            self.plotLastTickLable(xAxis, yAxis, tickDatetime, yAxis)        
            
        #--------------------
        self.__textPrice.setHtml(
                            '<div style="text-align: center">\
                                <span style="color: red; font-size: 10pt;">\
                                  %0.5f\
                                </span>\
                            </div>'\
                                % (yAxis))   
        self.__textDate.setHtml(
                            '<div style="text-align: center">\
                                <span style="color: red; font-size: 10pt;">\
                                  %s\
                                </span>\
                            </div>'\
                                % (tickDatetimeStr))   
        #mid 2)get position environments
        #mid 2.1)client area rect
        rect = view.sceneBoundingRect()
        leftAxis = view.getAxis('left')
        bottomAxis = view.getAxis('bottom')            
        rectTextDate = self.__textDate.boundingRect()         
        #mid 2.2)leftAxis width,bottomAxis height and textDate height.
        leftAxisWidth = leftAxis.width()
        bottomAxisHeight = bottomAxis.height()
        rectTextDateHeight = rectTextDate.height()
        #print leftAxisWidth,bottomAxisHeight
        #mid 3)set positions of price and date lable
        topLeft = view.plotItem.vb.mapSceneToView(QtCore.QPointF(rect.left()+leftAxisWidth,rect.top()))
        bottomRight = view.plotItem.vb.mapSceneToView(QtCore.QPointF(rect.width(),rect.bottom()-(bottomAxisHeight+rectTextDateHeight)))
        self.__textDate.setPos(xAxis,bottomRight.y())
        self.__textPrice.setPos(topLeft.x(),yAxis)
        
    #----------------------------------------------------------------------
    def __getTickDatetimeByXPosition(self,xAxis):
        """mid
        默认计算方式，用datetimeNum标记x轴
        根据某个view中鼠标所在位置的x坐标获取其所在tick的time，xAxis可以是index，也可是一datetime转换而得到的datetimeNum
        return:str
        """        
        tickDatetimeRet = xAxis
        minYearDatetimeNum = mpd.date2num(dt.datetime(1900,1,1))
        if(xAxis > minYearDatetimeNum):
            tickDatetime = mpd.num2date(xAxis).astimezone(pytz.timezone('utc'))
            if(tickDatetime.year >=1900):
                tickDatetimeRet = tickDatetime 
        return tickDatetimeRet       
    
    #----------------------------------------------------------------------
    def plotLastTickLable(self,x,y,lasttime,lastprice):        
        """mid
        被嵌入的plotWidget在需要的时候通过调用此方法显示lastprice和lasttime
        比如，在每个tick到来的时候
        """
        tickDatetime,yAxis = lasttime,lastprice
        
        if(isinstance(tickDatetime,dt.datetime)):
            dateText = dt.datetime.strftime(tickDatetime,'%Y-%m-%d')
            timeText = dt.datetime.strftime(tickDatetime,'%H:%M:%S.%f')
        else:
            dateText = "not set."
            timeText = "not set."
        if(isinstance(yAxis,float)):
            priceText = "%.5f" % yAxis
        else:
            priceText = "not set."
            
        self.__textLastPrice.setHtml(
                            '<div style="text-align: center">\
                                <span style="color: red; font-size: 10pt;">\
                                  %s\
                                </span>\
                                <br>\
                                <span style="color: red; font-size: 10pt;">\
                                %s\
                                </span>\
                                <br>\
                                <span style="color: red; font-size: 10pt;">\
                                %s\
                                </span>\
                            </div>'\
                                % (priceText,timeText,dateText))             
        
        self.__textLastPrice.setPos(x,y)  
class TickMonitor(pg.PlotWidget):
    #----------------------------------------------------------------------
    def __init__(self,host,port,dbName,symbolName,startDatetimeStr,endDatetimeStr):
        super(TickMonitor, self).__init__()
        self.crosshair = Crosshair(self)        #mid 实现crosshair功能
        tickMonitor = self.plot(clear=False,pen=(255, 255, 255), name="tickTimeLine")
        self.addItem(tickMonitor)  

        #mid 加载数据
        tickDatetimeNums,tickPrices = self.__loadTicksFromMongo(host,port,dbName,symbolName,startDatetimeStr,endDatetimeStr)
        #mid 显示数据
        tickMonitor.setData(tickDatetimeNums,tickPrices,clear=False,)  
        
    #----------------------------------------------------------------------
    def __loadTicksFromMongo(self,host,port,dbName,symbolName,startDatetimeStr,endDatetimeStr):
        """mid
        加载mongodb数据转换并返回数字格式的时间及价格
        """
        mongoConnection = MongoClient(host=host,port=port)
        collection = mongoConnection[dbName][symbolName]   

        startDate = dt.datetime.strptime(startDatetimeStr, '%Y-%m-%d')
        if endDatetimeStr:
            endDate = dt.datetime.strptime(endDatetimeStr, '%Y-%m-%d')
            cx = collection.find({'datetime': {'$gte': startDate, '$lte': endDate}})  
        else:
            cx = collection.find({'datetime': {'$gte': startDate}})  
        tickDatetimeNums = []
        tickPrices = []
        for d in cx:
            tickDatetimeNums.append(mpd.date2num(d['datetime']))
            tickPrices.append(d['lastPrice'])
        return tickDatetimeNums,tickPrices
    
    #----------------------------------------------------------------------
#    def getTickDatetimeByXPosition(self,xAxis):
#        """mid
#        根据传入的x轴坐标值，返回其所代表的时间
#        """
#        tickDatetimeRet = xAxis
#        minYearDatetimeNum = mpd.date2num(dt.datetime(1900,1,1))
#        if(xAxis > minYearDatetimeNum):
#            tickDatetime = mpd.num2date(xAxis).astimezone(pytz.timezone('utc'))
#            if(tickDatetime.year >=1900):
#                tickDatetimeRet = tickDatetime 
#        return tickDatetimeRet  
        
        
class winForm(QtGui.QWidget):
    def __init__(self):
        super(winForm,self).__init__()
        self.initUI()

    def initUI(self):
        self.setToolTip(u'绘图')
        vtsymbol = QtGui.QLabel(u'合约')
        startdate = QtGui.QLabel(u'起始时间')
        enddate = QtGui.QLabel(u'结束时间')
        self.vtsymbol = QtGui.QLineEdit()
        self.startdate = QtGui.QLineEdit()
        self.enddate = QtGui.QLineEdit()
        self.grid =QtGui.QGridLayout()
        self.grid.addWidget(vtsymbol,1,0)
        self.grid.addWidget(self.vtsymbol,1,1)
        self.grid.addWidget(startdate,1,3)
        self.grid.addWidget(self.startdate,1,4)
        self.grid.addWidget(enddate,1,5)
        self.grid.addWidget(self.enddate,1,6)
        btn=QtGui.QPushButton(u'画图',self)
        btn.setToolTip(u'输入参数开始画图')
        btn.resize(btn.sizeHint())
        btn.move(50,0)
        self.connect(btn,QtCore.SIGNAL('clicked()'), self.draw)  #OK按钮 的clicked()时间 信号 绑定到addNum这个函数 也叫槽
                
        
        btn1=QtGui.QPushButton(u'退出',self)
        btn1.clicked.connect(QtCore.QCoreApplication.instance().quit)
        btn1.resize(btn1.sizeHint())
        btn1.move(150,0)

        self.grid.addWidget(btn,1,7)
        self.grid.addWidget(btn1,1,8)
#        main = TickMonitor('localhost',27017,'VnTrader_Tick_Db',self.symbol,self.start,self.end)
#        grid.addWidget(main,2,1)
        
        self.setLayout(self.grid)
        #self.setGeometry(300,300,250,150)
        self.setWindowTitle(u'绘图')
        self.setWindowIcon(QtGui.QIcon())
        self.show()

    def closeEvent(self,event):
        res=QtGui.QMessageBox.question(self,'info',
                u"你要确定退出吗？",QtGui.QMessageBox.Yes |
                                       QtGui.QMessageBox.No,
                                       QtGui.QMessageBox.No)
        if res==QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
            
    def draw(self):
        symbol = str(self.vtsymbol.text())   #获取文本框内容
        start = str(self.startdate.text())
        end = str(self.enddate.text())
        main = TickMonitor('localhost',27017,'VnTrader_Tick_Db',symbol,start,end)
        self.grid.addWidget(main,2,1)
  

def main():
    app=QtGui.QApplication(sys.argv)
    ex=winForm()
    sys.exit(app.exec_())

if __name__=='__main__':
    main()