import sys

sys.path.insert(0, "lib/picosdk-python-examples/python-picoscope/picoscope/")
import ps2000a as ps
from picostatus import pico_num

sys.path.insert(0, "lib/asciimatics/")
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.widgets import Label, Frame, ListBox, Layout, Divider, Text, \
    Button, TextBox, Widget, PopUpDialog
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication

sys.path.insert(0, "lib/quantiphy/")
from quantiphy import Quantity

import threading
import math
from matplotlib.mlab import find
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches
import warnings
from lib.resolution import *

class MainView(Frame):
    
    ###########################################################################
    # Frame initialization
    ###########################################################################	
    def __init__(self, screen):
        super(MainView, self).__init__(screen,
                                       screen.height * 4 // 5,
                                       screen.width * 4 // 5,
                                       title="PicoScope Frequency Counter by VK2UTL")

        #Set basic layout
        self.modelLabel = Label("Model: ")
        self.calDateLabel = Label("Cal. date: ")
        self.serialLabel = Label("Serial: ")
        self.firmware1Label = Label("Firmware 1: ")
        self.firmware2Label = Label("Firmware 2: ")
        #self.minIntervalLabel = Label("Min. interval: ")
        #self.maxRateLabel = Label("Max. rate: ")
        self.memoryLabel = Label("Memory: ")
        self.driverLabel = Label("Driver: ")
        
        self.channelBox = ListBox(1,[],label="Channel: ")
        self.rangeBox = ListBox(1,[],label="Range: ")
        self.overVoltagedLabel = Label("Overvolt.: ")
        self.couplingBox = ListBox(1,[],label="Coupling: ")
        self.offsetText = Text("Offset: ")
        
        self.timebaseText = Text("Timebase: ", on_change=self._timebase_changed)
        self.intervalText = Text("Interval: ", on_change=self._interval_changed)
        self.rateText = Text("Rate: ", on_change=self._rate_changed)
        self.gateText = Text("Time/gate: ", on_change=self._gate_changed)
        self.samplesText = Text("Samp./gate: ", on_change=self._samples_changed)
        self.resolutionBox = ListBox(1,[],label="Resolution: ",on_change=self._resolution_changed)
        
        self.frequencyLabel = Label("Frequency: ")
        self.frequencyResolutionErrrorLabel = Label("Resolution Error: ")
        self.meanLabel = Label("Mean: ")
        self.stdLabel = Label("Deviation: ")
        self.gatesLabel = Label("Gates: ")
        self.totalSamplesLabel = Label("Samples: ")
        self.timeLabel = Label("Time: ")
        
                
        layout = Layout([48,4,48], fill_frame=True)
        self.add_layout(layout)
        
        layout.add_widget(self.modelLabel,0)
        layout.add_widget(self.calDateLabel,0)
        layout.add_widget(self.serialLabel,0)
        layout.add_widget(self.firmware1Label,0)
        layout.add_widget(self.firmware2Label,0)
        #layout.add_widget(self.minIntervalLabel,0)
        #layout.add_widget(self.maxRateLabel,0)
        layout.add_widget(self.driverLabel,0)
        layout.add_widget(self.memoryLabel,0)
        layout.add_widget(Divider(),0)
        
        layout.add_widget(self.channelBox,0)
        layout.add_widget(self.rangeBox,0)
        layout.add_widget(self.overVoltagedLabel,0)
        layout.add_widget(self.couplingBox,0)
        layout.add_widget(self.offsetText,0)
        
        layout.add_widget(Divider(),0)
        layout.add_widget(self.timebaseText,0)
        layout.add_widget(self.intervalText,0)
        layout.add_widget(self.rateText,0)
        layout.add_widget(self.resolutionBox,0)
        layout.add_widget(self.gateText,0)
        layout.add_widget(self.samplesText,0)
    
        
        layout.add_widget(self.frequencyLabel,2)
        layout.add_widget(self.meanLabel,2)
        layout.add_widget(self.stdLabel,2)
        layout.add_widget(self.gatesLabel,2)
        layout.add_widget(self.totalSamplesLabel,2)
        layout.add_widget(self.timeLabel,2)
        
    	layout = Layout([1])
    	self.add_layout(layout)
    	layout.add_widget(Divider())
    	
        layout = Layout([1, 1, 1, 1, 1])
        self.add_layout(layout)
        
        self.startButton = Button("Start", self._start)
        self.startButton.disabled = True
        layout.add_widget(self.startButton, 0)
        
        self.stopButton = Button("Stop", self._stop)
        self.stopButton.disabled = True
        layout.add_widget(self.stopButton, 1)
        
        self.plotButton = Button("Plot", self._plot)
        self.plotButton.disabled = True
        layout.add_widget(self.plotButton, 2)
        
        self.saveButton = Button("Save", self._quit)
        self.saveButton.disabled = True
        layout.add_widget(self.saveButton, 3)
        
        self.quitButton = Button("Quit", self._quit)
        layout.add_widget(self.quitButton, 4)
               
        self.fix()
        
        # Start scope initialization thread
        self.initThread = threading.Thread(target=self._initializeScope)
        self.initThread.start()
    	#self._initializeScope()
        
        # Needed to force screen update later
        #self.screen=screen
               
	###########################################################################
    # Set up scope connection and initialize it
    ###########################################################################	
    def _initializeScope(self):
    	
    	# open Device
    	self.scope = ps.Device()
    	status = self.scope.open_unit() 
        #if status != pico_num("PICO_OK"):
        #	self.modelLabel._text = "Model: Error"
        #	return 
        		
        # get basic info
        self.modelLabel._text = "Model: %s" % self.scope.info.variant_info
        self.calDateLabel._text = "Cal. date: %s" % self.scope.info.cal_date
        self.serialLabel._text = "Serial: %s" % self.scope.info.batch_and_serial
        self.firmware1Label._text = "Firmware 1: %s" % self.scope.info.firmware_version_1
        self.firmware2Label._text = "Firmware 2: %s" % self.scope.info.firmware_version_2
        driver = self.scope.info.driver_version.split(" Driver, ")
        self.driverLabel._text = "Driver: %s, %s" % (driver[0],driver[1])
        
        # activate channel A
        self.channelMap = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.channelBox.options = [ (self.channelMap[i],i) for i in range(0,self.scope.info.num_channels) ]
        
        self.fullRangeMap = ("10mv", "20mV", "50mV", "100mV", "200mV", "500mV", "1V", "2V", "5V", "10V", "20V", "50V", "100V", "200V", "400V")
        self.rangeMap = [ self.fullRangeMap[i] for i in range(self.scope.info.min_range,self.scope.info.max_range) ]
        self.rangeBox.options = [ (self.rangeMap[i], i) for i in range(0,len(self.rangeMap))]
        
        self.couplingBox.options = [ ("AC",0),("DC",1) ]
        
        self.channelBox.value = 0
        self.couplingBox.value = self.scope.m.Couplings.ac
        self.rangeBox.value = 0
        self.offsetText.value = "0 V"
        self.overVoltagedMap = ["No", "Yes"]
        self._update_channels()
        
    	# sampling info
    	self.timebase = 0
    	status, self.minInterval = self.scope.get_basic_interval(self.timebase)
        self.minInterval *= 10**-9
        self.memory = self.scope.set_memory_segments(1)[1]
        self.interval = self.minInterval
        self.rate = 1/self.interval
        #self.gate = self.memory*self.interval
        #self.samples = self.memory
        #self.resolution = self._get_resolution(1/self.gate)     
    
    	self.timebaseText.value = str(self.timebase)
        self.intervalText.value = Quantity(self.interval, "s").render()
        self.rateText.value = Quantity(self.rate, "Hz").render()
        #self.gateText.value = Quantity(self.gate, "s").render()
        #self.samplesText.value = Quantity(self.samples, "S").render()
        #self.resolutionText.value = Quantity(self.resolution, "Hz").render()
        self.memoryLabel._text = "Memory: %s" % Quantity(self.memory, "S").render()
                       
        self.startButton.disabled = False
        #self.startButton.focus()
        #self.quitButton.blur()
        
        self.screen.force_update()
    
    ###########################################################################
    # Update channel settings
    ###########################################################################	   
    def _update_channels(self):
    		
    	self.channel = self.channelBox.value
    	self.range = self.fullRangeMap.index(self.rangeMap[self.rangeBox.value])
    	self.coupling = self.couplingBox.value
    	self.offset = Quantity(self.offsetText.value)
    		    		
        for i in range(0,self.scope.info.num_channels):
            status, state = self.scope.get_channel_state(channel=i)
            state.enabled = False
            self.scope.set_channel(self.channel, state)
            
        status, state = self.scope.get_channel_state(channel=self.channel)
        state.offset = self.offset
        state.coupling = self.coupling
        state.range = self.range
        state.enabled = True
        self.scope.set_channel(self.channel, state)
        
       	status, state = self.scope.get_channel_state(channel=self.channel)
       	if state.overvoltaged:
       		self.overVoltagedLabel._text = "Overvolt.:   Yes"
       	else:
       		self.overVoltagedLabel._text = "Overvolt.:   No"
        
    ###########################################################################
    # Time base text field changed
    ###########################################################################	
    def _timebase_changed(self):
    	try:
    		int(self.timebaseText.value)
    	except:
    		return
    	
    	self.timebase = int(self.timebaseText.value)
    	self.interval = self.scope.get_basic_interval(self.timebase)[1]*10**-9
    	self.rate = 1/self.interval
    	
        self.intervalText._value = Quantity(self.interval, "s").render()
        self.rateText._value = Quantity(self.rate, "Hz").render()
                
        self._set_resolution()      	
                 
    
    ###########################################################################
    # Interval text field changed
    ###########################################################################		
    def _interval_changed(self):
    	try:
    		Quantity(self.intervalText.value)
    	except:
    		return
    		
    	self.timebase, self.interval = self._get_timebase(Quantity(self.intervalText.value).real)
    	self.rate = 1/self.interval
    	
    	self.timebaseText._value = str(self.timebase)
        self.rateText._value = Quantity(self.rate, "Hz").render()
        
        self._set_resolution()
        
        
    ###########################################################################
    # Rate text field changed
    ###########################################################################		
    def _rate_changed(self):
    	try:
    		Quantity(self.rateText.value)
    	except:
    		return
    	if Quantity(self.rateText.value) == 0:
    		return
    		
    	self.timebase, self.interval = self._get_timebase(1/Quantity(self.rateText.value).real)
    	self.rate = 1/self.interval
    	
    	self.timebaseText._value = str(self.timebase)
    	self.intervalText._value = Quantity(self.interval, "s").render()
    	
    	self._set_resolution()
    
    ###########################################################################
    # Returns the resolution for a value
    ###########################################################################	
    def _get_resolution(self,f):
    	return 10**int(math.ceil(math.log10(abs(f))))
    	
    ###########################################################################
    # Set resolution
    ###########################################################################	
    def _set_resolution(self):
    
    	#determine possible resolutions for current sampling rate and available
    	#memory
        resWorst = self._get_resolution(1/self.minInterval)
        resBest = self._get_resolution(1/(self.memory*self.interval))
        steps = int(math.log10(resWorst)) - int(math.log10(resBest))
               
        self.resolutionBox.options = [ (Quantity(resBest*10**i,"Hz").render(),i) for i in range(0,steps) ]
    	
        self._resolution_changed()
        
    ###########################################################################
    # Resolution box changed
    ###########################################################################	   
    def _resolution_changed(self):
    
    	try:
    		self.resolutionBox.value
    	except:
    		return
    	
    	self.resolution = Quantity(self.resolutionBox.options[self.resolutionBox.value][0])
    	   	
    	self.gate = int(math.ceil((1/self.resolution)/self.interval))*self.interval	#need multiple of interval
    	self.samples = self.gate*self.rate
    	
    	self.gateText._value = Quantity(self.gate, "s").render()
    	self.samplesText._value = Quantity(self.samples, "S").render()
    	
        
    ###########################################################################
    # Gate text field changed
    ###########################################################################		
    def _gate_changed(self):
    	
    	try:
    		Quantity(self.gateText.value)
    	except:
    		return
    		
    	if Quantity(self.gateText.value) == 0:
    		return
    		
    	self.gate = Quantity(self.gateText.value)
    	if self.gate > self.memory*self.interval:
    		self.gate = self.memory*self.interval
    	elif self.gate < self.minInterval:
    		self.gate = self.minInterval
    		
    	self.gate = int(math.ceil(self.gate/self.interval))*self.interval
    	
    	self.resolution = self._get_resolution(1/self.gate)	
    	resls = self.resolutionBox.options
    	resls = [ r[0] for r in resls ]
    	self.resolutionBox._line = resls.index(Quantity(self.resolution,"Hz").render())
    	self.resolutionBox._value = self.resolutionBox._line
    	
    	self.samples = self.gate/self.interval
    	self.samplesText._value = Quantity(self.samples, "S").render()
    	
    		
    ###########################################################################
    # Samples text field changed
    ###########################################################################		
    def _samples_changed(self):
    	try:
    		Quantity(self.samplesText.value)
    	except:
    		return

    	#self.samples = Quantity(self.samplesText.value)
    	#self.rateText.text = Quantity(self.gate/self.samples, "Hz").render()
    	#self.samples = 
    		
    	    	    
    ###########################################################################
    # Computes timebase closest to given interval
    # Currently only implemented for the 2000 series
    # (not so nicely implemented...)
    ###########################################################################	
    def _get_timebase(self,interval):
    	if self.scope.info.variant_info in ['2206A', '2206B']:
			if interval <= 3.0*10**-9:
				return 0, 2.0*10**-9
			elif interval > 3.0*10**-9 and interval <= 6.0*10**-9:
				return 1, 4.0*10**-9
			elif interval > 6.0*10**-9 and interval <= 12.0*10**-9:
				return 2, 8.0*10**-9
			elif interval >= float(2**32-1)/62500000.0:
				return 2**32-1, float(2**32-1)/62500000.0
			else:
				timebase = int(interval*62500000) + 2
				timebaseInterval = self.scope.get_basic_interval(timebase)[1]*10**-9
				if timebaseInterval == interval:
					return timebase, timebaseInterval
				elif timebaseInterval < interval:
					while timebaseInterval < interval:
						previousTimeBaseInterval = self.scope.get_basic_interval(timebase)[1]*10**-9
						timebase += 1
						timebaseInterval = self.scope.get_basic_interval(timebase)[1]*10**-9					
					if abs(interval - timebaseInterval) <= abs(interval - previousTimeBaseInterval):
						return timebase, timebaseInterval
					else:
						return timebase-1, previousTimeBaseInterval
				else:
					while timebaseInterval >= interval:
						previousTimeBaseInterval = self.scope.get_basic_interval(timebase)[1]*10**-9
						timebase -= 1
						timebaseInterval = self.scope.get_basic_interval(timebase)[1]*10**-9					
					if abs(interval - timebaseInterval) <= abs(interval - previousTimeBaseInterval):
						return timebase, timebaseInterval
					else:
						return timebase+1, previousTimeBaseInterval
        
        elif self.scope.info.variant_info in ['2207A','2207B','2208A','2208B']:
			if interval <= 1.5*10**-9:
				return 0, 1.0*10**-9
			elif interval > 1.5*10**-9 and interval <= 3.0*10**-9:
				return 1, 2.0*10**-9
			elif interval > 3.0*10**-9 and interval <= 6.0*10**-9:
				return 2, 4.0*10**-9
			elif interval >= float(2**32-1)/125000000.0:
				return 2**32-1, float(2**32-1)/125000000.0
			else:
				timebase = int(interval*125000000) + 2
				timebaseInterval = self.scope.get_basic_interval(timebase)[1]*10**-9
				if timebaseInterval == interval:
					return timebase, timebaseInterval
				elif timebaseInterval < interval:
					while timebaseInterval < interval:
						previousTimeBaseInterval = self.scope.get_basic_interval(timebase)[1]*10**-9
						timebase += 1
						timebaseInterval = self.scope.get_basic_interval(timebase)[1]*10**-9					
					if abs(interval - timebaseInterval) <= abs(interval - previousTimeBaseInterval):
						return timebase, timebaseInterval
					else:
						return timebase-1, previousTimeBaseInterval
				else:
					while timebaseInterval >= interval:
						previousTimeBaseInterval = self.scope.get_basic_interval(timebase)[1]*10**-9
						timebase -= 1
						timebaseInterval = self.scope.get_basic_interval(timebase)[1]*10**-9					
					if abs(interval - timebaseInterval) <= abs(interval - previousTimeBaseInterval):
						return timebase, timebaseInterval
					else:
						return timebase+1, previousTimeBaseInterval
    	
    ###########################################################################
    # Collect data
    ###########################################################################	
    def _start(self):
    	self._update_channels()
    	self.frequencies = np.array([])
    	self.gateCounter = 0
    	self.timeCounter = 0
    	self.sampleCounter = 0
    	self.stopRequested = False
    	self.collectThread = threading.Thread(target=self._collect_data)
    	self.collectThread.daemon = True
    	self.stopButton.disabled = False
    	self.startButton.disabled = True
    	self.plotButton.disabled = True
        self.collectThread.start()
           	
    def _collect_data(self):
		
		state, index = self.scope.locate_buffer(channel=self.channel,
                                samples=int(self.samples),
                                segment=0,
                                mode=self.scope.m.RatioModes.raw,
                                downsample=0)
		
		while self.stopRequested == False:
                                
			status = self.scope.collect_segment(segment=0,timebase=self.timebase)
			status, data = self.scope.get_buffer_volts(0)
			
			freq = float(self._number_of_crossings(data,0.0))/self.gate
			freq = TruncateToResolution(freq, self.resolution)
			self.frequencies = np.append(self.frequencies, freq)
			freq = Quantity(freq, "Hz")
			freq = SetPrecisionToResolution(freq, self.resolution)
			
			self.frequencyLabel._text = "Frequency: %s" % freq.render()
			
			avg = Quantity(self.frequencies.mean(), "Hz")
			avg = SetPrecisionToResolution(avg, self.resolution/10.0)
			self.meanLabel._text = "Average:   %s" % avg.render()
			
			self.stdLabel._text = "Deviation: %s" % Quantity(self.frequencies.std(), "Hz").render()
			
			self.gateCounter += 1
			self.timeCounter += self.gate
			self.sampleCounter += self.samples
			self.gatesLabel._text = "Gates:     %s" % Quantity(self.gateCounter).render()
			self.timeLabel._text = "Time:      %s" % Quantity(self.timeCounter,"s").render()
			self.totalSamplesLabel._text = "Samples:   %s" % Quantity(self.sampleCounter,"S").render()
					
			self.screen.force_update()
			
		
		self.stopButton.disabled = True
		self.startButton.disabled = False
		self.plotButton.disabled = False
		
	###########################################################################
    # Stop collect
    ###########################################################################
    def _stop(self):
    	self.stopRequested = True
    
    ###########################################################################
    # Number of crossings
    ###########################################################################
    def _number_of_crossings(self,data,base):
    	if len(data) == 0:
    		return 0
    	crossings = len(find((data[1:] >= base) & (data[:-1] < base)))
    	if data[0] == 0:
    		crossings += 1
    	if len(data) > 1 and data[-1] == 0:
    		crossings += 1
    	return crossings
    	
    ###########################################################################
    # Plot frequencies
    ###########################################################################	
    def _plot(self):
    	
    	# create plot
		fig = plt.figure()
		ax = plt.subplot(111)
		ax.scatter(range(0,len(self.frequencies)),self.frequencies, color="#00A2FF", label='Frequency')

		# grid
		plt.grid(b=True, which='major', color='k', linestyle='-', alpha=0.2, linewidth=0.3)
		plt.grid(b=True, which='minor', color='k', linestyle='-', alpha=0.15, linewidth=0.15)
		plt.minorticks_on()

		# limits
		#ax.set_xlim([freq.min(),freq.max()])

		#plt.xticks([0,len(freq)], freq)

		# layout
		fig.set_tight_layout(True)
		plt.rcParams.update({'font.size': 8})
		
		avg = Quantity(self.frequencies.mean(), "Hz")
		avg = SetPrecisionToResolution(avg, self.resolution/10.0)
		std = Quantity(self.frequencies.std(), "Hz")
		
		ax.annotate("Sample rate: %s, gate time: %s\nmean: %s, std: %s" % (Quantity(self.rate, "Hz").render(), Quantity(self.gate, "s").render(), avg.render(), std.render()), xy=(1, 0), xycoords='axes fraction', fontsize=8, xytext=(-5, 5), textcoords='offset points', ha='right', va='bottom')
		
		# axis labels
		plt.xlabel("Gate #")
		plt.ylabel("Frequency [Hz]")

		#PYTHON....There's a matplotlib bug coming up here'
		with warnings.catch_warnings():
			warnings.simplefilter(action='ignore', category=FutureWarning)
			plt.show()

    
    ###########################################################################
    # Quit application (close scope connection first)
    ###########################################################################	
    def _quit(self):
        self.scope.close_unit()
        raise StopApplication("User pressed quit")
        
    ###########################################################################
    # Additional event handler for TABs to update timebase etc. text fields
    ###########################################################################	
    def process_event(self, event):
        super(MainView,self).process_event(event)
        
        if isinstance(event, KeyboardEvent):
            if event.key_code in [Screen.KEY_TAB]:
            	self.timebaseText._value = str(self.timebase)
                self.intervalText._value = Quantity(self.interval, "s").render()
                self.rateText._value = Quantity(self.rate, "Hz").render()
                self.gateText._value = Quantity(self.gate, "s").render()
                #self.samplesText._value = Quantity(self.samples, "S").render()
                #self.resolutionText._value = Quantity(self.resolution, "Hz").render()
       		
         
       

def main(screen):
    scenes = [
        Scene([MainView(screen)], -1, name="Main")
    ]

    screen.play(scenes)

Screen.wrapper(main)