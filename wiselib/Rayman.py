# -*- coding: utf-8 -*-
"""
Created on Wed Jun 08 14:06:01 2016
Huygens Fresnel Method Library
@authors:

Cose da sistemare
- capire come chiamare gli assi del fascio gaussiano RhoZ ?
- trovare denominazione comune xMir yMir, Mir_x MirX Mir_xy MirXY e salaminchia
"""
#%%
from __future__ import division
import numpy as np
#import cmath as cm
from numpy import  cos, sin, tan, arctan, arctan2, pi, array, arange, size, polyval, polyfit, dot, exp, arcsin, arccos, real, imag
from numpy.lib.scimath import sqrt

from  scipy import ndimage
import multiprocessing

Amp = lambda x : abs(x) / max(abs(x))
Cyc = lambda x : real(x) / abs(x)

def ro_property(field):
	return property(lambda self : self.__dict__[field])


def GetCentre(N):
	'''
	%  Y = GetCentre(X)
	% Restituisce il centro del vettore X. Il centro è inteso come
	% il punto in cui compare la DC della trasformata di Fourier.
	% Ovviamente, il tutto è in base-1, compatibile con matlab.
	'''
	return int(np.floor(N/2))

def ArgMax (X = np.empty(0)):
	r,c = np.unravel_index(X.argmax(), X.shape)
	return r,c

def ArgMin (X = np.empty(0)):
	r,c = np.unravel_index(X.argmin(), X.shape)
	return r,c


def MakeScreenXY_1d(XY0, L, N, Theta = 0, Normal = False ):
	if Normal == True:
		Theta = Theta - pi/2

	if abs(Theta) == pi/2:
		Det_y0 = XY0[1] - L/2
		Det_y1 = XY0[1] + L/2
		y = np.linspace(Det_y0, Det_y1,N)
		x = 0*y + XY0[0]

	else:
		m = tan(Theta)
		q = XY0[1] - XY0[0] * m
		p = array([m,q])
		Det_x0 = XY0[0] - L/2 * cos(Theta)
		Det_x1 = XY0[0] + L/2 * cos(Theta)
		x = np.linspace(Det_x0, Det_x1,N)
		y = polyval(p,x)

	return x,y

def FastResample1d(*args):
	'''
		FastResample1d([x], [y], [n])
		Usage:
		yy = FastResample1d(y,1000)
		or
		xx,yy =FastResample1d(x,y,1000)
	'''
	from scipy import interpolate as interpolate
	# input: y,N
	if len(args) == 2:
		y = args[0]
		N0 = len(y)
		N = args[1]
		if N == N0:
			return y

		x = np.arange(0, N0)
		f = interpolate.interp1d(x, y)
		xNew = np.linspace(0,N0-1,N)
		yNew = f(xNew)
		return  yNew
	#input: x,y,N
	elif len(args) == 3:
		x = args[0]
		y = args[1]
		N = args[2]
		N0 = len(x)
		xNew = np.linspace(np.amin(x), np.amax(x),N)
		fy = interpolate.interp1d(x, y)
		yNew = fy(xNew)
		return xNew, yNew
	else:
		raise  ValueError('Wrong argument number in calling FastResample1d')
		return None



def HalfEnergyWidth_1d(X,  UseCentreOfMass = True, Step = 1,  TotalEnergy = None,
						AlgorithmType = 0):
	'''

		Inputs
		------------
		X: 1d array

		Returns
		------------


		the Half width energy of the array X (1d)
		UseCentreOfMass: if False, computes the HEW respect with the maximum
		TotalEnergy: if None, uses TotalEnergy = sum(X).
	'''

	''' Stupid remarks
	The Hew of a Gaussian is 0.675

	'''

	TotalEnergy = sum(X) if TotalEnergy==None else TotalEnergy
	HalfEnergy = 0.5 * TotalEnergy ;

	if UseCentreOfMass == True:
		iCentre = int(np.floor(ndimage.measurements.center_of_mass(X)))
	else:	# uses max value. May be issues if many equal values are found
		iCentre = X.argmax()

	if AlgorithmType ==1:
		#================================================
		# Algoritmo binario
		#================================================
		RHi = np.floor(len(X)/2) ;
		RLow = 1 ;

		# algoritmo intelligente, ma che non funziona
		myR = int(np.floor(np.ceil(RHi + RLow)/2));
		DeltaR = RHi-RLow ; # variabile di controllo
		NIterations = 0 ;
		while DeltaR > 1:
			NIterations = NIterations + 1 ;
			iStart = int(round(iCentre - myR))
			iEnd = int(round(iCentre + myR))+1
			if sum(X[iStart:iEnd]) < HalfEnergy:
				RLow = myR;
			else:
				RHi = myR;
			myR = np.ceil(RLow + RHi)/2;
			DeltaR = RHi-RLow ;
	elif AlgorithmType == 0 :
		#================================================
		# Algoritmo stupido
		#================================================
		myEnergy = 0
		iR = 1
		while myEnergy < HalfEnergy:
			myEnergy = sum(X[iCentre - iR : iCentre + iR])
			iR = iR + 1
		myR = iR
	Diameter = 2*myR ;
	return Diameter * Step




def Gauss1d(N, Sigma):
	x = arange(0,N) - GetCentre(N)
	y = exp(-0.5 *x**2 / Sigma**2)
	return y



'''
def GaussNoise(N,Sigma):
	Sigma = N/Sigma
	y = Gauss1d(N,Sigma)
	y = np.fft.fftshift(y)
	r = 2*pi * np.random.rand(N)
	f = np.fft.ifft(y * exp(1j*r))
	return real(f)
'''

#______________________________________________________________________________
# 	xy2xyList
#______________________________________________________________________________
def xy2v(x,y):
	return [[xi,yi] for xi in x for yi in y]

def v2xy(v):
	return []




#______________________________________________________________________________
# 	RMat
#______________________________________________________________________________
def RMat(Theta):
	return [[cos(Theta), -sin(Theta)],
				[sin(Theta), cos(Theta)]]

#______________________________________________________________________________
# 	RMat
#______________________________________________________________________________

def XY_to_L(x,y):
	'''
	Dato un segmento di coordinate x,y, calcola la coordinata propria (solidale al segmento).
	L'origine della nuova coordinata L viene assunta a metà della lunghezza degli array di ingresso (che ha senso finché x,y definiscono un segmento di retta).
	'''
	N2 = int(np.floor(len(x)/2))
	L = 0*x
	L[0:N2] = -1 * sqrt((x[0:N2] - x[N2])**2 + (y[0:N2] - y[N2])**2)
	L[N2:] = 1 * sqrt((x[N2:] - x[N2])**2 + (y[N2:] - y[N2])**2)
	return L

def xy_to_s(x,y):
	'''
	For two arrays x,y computes the array of displacements s defined as
				s_i = sqrt( dx_i^2 + dy_i^2)
	where
				dx_i = x_i - x_(i-1)   and similarly for dy_i
	Essentially, s is the proper coordinate axis of the curve described by x,y.
	'''

	N2 = int(np.floor(len(x)/2))
	s0 = len(x)/2
	Steps = np.sqrt(np.diff(x)**2 + np.diff(y)**2)
	s  = np.cumsum(Steps)
	s = np.append(0,s) - s[int(len(s)/2)]
	return s

def PathLength(x,y):
	return sum(np.sqrt(np.diff(x)**2 + np.diff(y)**2))

#______________________________________________________________________________
# 	CartT
#______________________________________________________________________________
def CartT(Vxy, NewOrigin = np.array([0,0]), Theta = 0 ):
	Vxy = array(Vxy)
	NewOrigin = array(NewOrigin)
	return  dot(Vxy - NewOrigin, RMat(Theta))


def CartChange(x,y, NewOrigin = np.array([0,0]), Theta = 0):
	Vxy = np.column_stack((x,y))
	U = CartT(Vxy, NewOrigin, Theta)
	return (U[:,0], U[:,1])

def RotXY(x,y, Theta = 0, Origin = np.array([0,0])):
	if Theta == 0:
		return (x,y)
	Theta = -Theta # non so perché il -1, odio le matrici di rotazione.
	Vxy = np.column_stack((x,y))
	U  = dot(Vxy - Origin, RMat(Theta)) + Origin
	return (U[:,0], U[:,1])

#______________________________________________________________________________
# 	Range
#______________________________________________________________________________
def Range(Start, End, Step):
	return arange(Start, End+Step, Step)


#==============================================================================
# 	CLASS: SphericalWave_2d
#==============================================================================
class SphericalWave_1d(object):
	#================================================
	# 	__init__
	#================================================
	def __init__(self, Lambda, OriginZ = 0, OriginY = 0):
		self.Lambda = Lambda
		self.OriginZY = array([OriginZ, OriginY])

	#================================================
	# 	EvalPhase
	#================================================
	def EvalPhase(self,z,y):
		k = 2 * pi / self.Lambda
		(z,y) = _MatchArrayLengths(z,y)
		return k * sqrt((y - self.OriginZY[1])**2 + (z - self.OriginZY[0])**2)


	#================================================
	# 	EvalCycles
	#================================================
	def EvalCycles(self,z = np.array(None) , y = np.array(None)):
		(z,y) = _MatchArrayLengths(z,y)
		return np.cos(self.EvalPhase(z,y))

	#================================================
	# 	EvalField
	#================================================
	def EvalField(self, z = np.array(None), y = np.array(None) ):
		(z,y) = _MatchArrayLengths(z,y)
		R = sqrt((y - self.OriginZY[1])**2 + (z - self.OriginZY[0])**2)
		return 1/R * 	np.exp(1j*self.EvalPhase(z,y))
'''
	#================================================
	# 	Eval
	#================================================
	def Eval(self, z = np.array(None) , y = np.array(None)):
		return self.Field(z,y)
'''

#	def ChirpCyclesInParaxialApproximation







class SourceType():
	POINT = 0
	GAUSSIAN_TEM00 = 1




#==============================================================================
# 	FUN: HuygensIntegral_1d_Kernel
#==============================================================================
def HuygensIntegral_1d_Kernel(Lambda, Ea, xa, ya, xb, yb, bStart = None, bEnd=None):
	k = 2*pi/Lambda
	if bStart == None:
		bEnd = np.size(xb)
		bStart = 0

	EbTokN = bEnd - bStart
	EbTok = 1j*np.zeros(EbTokN)

	# loop on items within the segment of B
	for (i, xbi) in enumerate(xb[bStart : bEnd]):
		ybi = yb[i+bStart]

		EbTok[i] = 1./(Lambda)**0.5*sum(Ea * 						# field complex amplitude
					exp(1j*k*(sqrt((xa - xbi)**2 + (ya - ybi)**2))) # huygens spherical wave
					)


	return EbTok

def _MatchArrayLengths (x,y):
	'''
		If x(or y) is a Mx1 array and y(or x) is a scalar, then y (or x) is a Mx1 	array filled with replica of the single value of input y
	'''
	IsArray = lambda t : True if type(t) == np.ndarray else False

	if IsArray(x) and not IsArray(y) :
		y = np.array(x) * 0 + y
		return (x,y)
	elif IsArray(y) and not IsArray(x):
		x = np.array(y) * 0 +x
		return (x,y)
	else:
		return (x,y)

#==============================================================================
# 	WRAPPER
#==============================================================================
def _wrapper_HuygensIntegral_1d_Kernel(parameters):
	Lambda, Ea, xa, ya, xb, yb, bStart, bEnd = parameters

	return HuygensIntegral_1d_Kernel(Lambda, Ea, xa, ya, xb, yb, bStart, bEnd)

#==============================================================================
# 	WRAPPER ARGUMENTS
#==============================================================================
def _wrapper_args_HuygensIntegral_1d_Kernel(Lambda, Ea, xa, ya, xb, yb, NPools):
	N = np.size(xb)
	r = np.linspace(0,N, NPools+1) ; r = np.array([np.floor(ri) for ri in r]) ;
	#args_StartStop = list(zip([x for x in r], r[1:]))
	args_StartStop = list(zip(r[0:], r[1:]))
	#args_StartStop  = (len(r)-1) * [(r[0], r[1])] # toglier
	args =  [[Lambda, Ea, xa, ya, xb, yb] + list(myArg) for myArg in args_StartStop]
	return (args,args_StartStop)

#==============================================================================
# 	FUN: HuygensIntegral_1d_MultiPool
#==============================================================================
def HuygensIntegral_1d_MultiPool(Lambda, Ea, xa, ya, xb, yb, NPools = 0):

	(xa , ya) = _MatchArrayLengths(xa,ya)
	(xb, yb) = _MatchArrayLengths(xb,yb)

	if NPools > 0:
		p = multiprocessing.Pool(NPools)
		(args, argsStartStop) = _wrapper_args_HuygensIntegral_1d_Kernel(Lambda, Ea, xa, ya, xb, yb, NPools )
		res = p.map(_wrapper_HuygensIntegral_1d_Kernel, args)
		p.close()
#		return argsStartStop # toglire
		if np.size(res) > 1:
			return np.concatenate(res)
		else:
			return res
	else: #single thread
		return HuygensIntegral_1d_Kernel(Lambda, Ea, xa, ya, xb, yb )

#==============================================================================
# 	FUN: HuygensIntegral_1d
#==============================================================================
HuygensIntegral_1d = HuygensIntegral_1d_MultiPool

#==============================================================================
# 	FUN: HuygensIntegral_1d
#==============================================================================
def SamplingCalculator(Lambda, z, L0, L1,  Theta0, Theta1):
	'''
	Lambda: wavalenght
	z:distance b|w start and arrival planes
	L0,L1: lenght of start and arrival planes
	Theta0, Theta1: orientationf of start and arivval planes
	'''
	return int(10 * L0 * L1* cos(Theta0 - Theta1) /Lambda/z)
#	int(10 * kbv.L * Det_Size  * cos(kbv.pTan_Angle - arctan(-1/kbv.p2[0])) /Lambda/kbv.f2)

def  SamplingGoodness_QuadraticPhase(MatrixN, dPix, Lambda, z, R=np.inf, Verbose = True):
	'''
	[iqLim, TextOutput, OUT] =
	'''
	class strucOUT:
		zMin = np.nan
		NOsc = np.nan
		alpha = np.nan
		alphaMax = np.nan
		alphaRatio = np.nan
		iLim = np.nan
		Text = 'text'

	OUT  = strucOUT()
	#% SamplingGoodness(MatrixN, PixelPhysicalSize, Lambda, z)
	k = 2*pi/Lambda
	N = MatrixN;
	L = N * dPix/2 # assume l'onda piana centrata nella matrice

	zMin = (Lambda/dPix/L + 1/R)**-1  # z minimum
	alpha = k/2 * (1/z + 1/R) ;
	alphaMax = pi/2/dPix/L;
	NOsc = alpha*L**2/2/pi

	OUT.zMin = zMin
	OUT.NOsc = NOsc ;
	OUT.alpha = alpha ;
	OUT.alphaMax = alphaMax ;
	OUT.alphaRatio = alpha/alphaMax ;
#	OUT.iqLim = iqLim ;
	OUT.Text = 'No aliasing for z < %0.1e m \n N Oscillations =\t%0.1f\n MagicRatio =\t%0.2f\n iqLim =\t%0.2f (N/2=%d)' %(zMin, NOsc, OUT.alphaRatio , OUT.iLim, N/2);
	if Verbose == True:
		print(OUT.Text)
	return OUT



#	#==============================================================================
#	# 	CLASS: Ellipse:Simulation
#	#==============================================================================
#	class Simulation(object):
#
#		#=======================================================================
#		# 	SMALL CLASS: SimulationSettings
#		#=======================================================================
#		class SimulationSettings(object):
#			def __init__(self):
#				self.Lambda = 10e-9
#				self.DetectorSize = 50e-6
#				self.Defocus = 0
#				self.NPools = 6
#				self.GaussianSourceWaist = 10e-3
#				self.AnalyticSourceType = SourceType.POINT
#
#			#=======================================================================
#			# 	Simulation:__init__
#			#=======================================================================
#			def __init__(self, ParentEllipse = None):
#				self.Ellipse = ParentEllipse
#				self.Settings = SimulationSettings()
#
#
#
#			#=======================================================================
#			# 	Simulation:AnalyticSource_EvalFieldAtFocalPlane
#			#=======================================================================
#			def FieldAtFocalPlane(self, Source,																								DetectorSize = self.Settings.DetectorSize,
#									Defocus = self.Settings.Defocus,
#									NPools = self.Settings.NPools,
#									):
#				'''
#				Computes the Electromagnetic field around the focal plane (F2) of the
#				ellipse object. The detector plane is normal to the ellipse axis.
#
#
#				Return: Field (complex), displacement array (float)
#				'''
#				Det_Size = DetectorSize
#				Kb = self.Ellipse
#				# Auto Sampling (easy way)
#				NAuto = int(10 * self.L * Det_Size  * cos(Kb.pTan_Angle - arctan(-1/Kb.p2[0])) /Lambda/Bb.f2)
#				# Plane 0
#				[Mir_x, Mir_y] = Kb.GetXY_MeasuredMirror(NAuto,0)
#				# E0
#				Mir_E = Source.EvalField_XYLab(Mir_x, Mir_y)
#	#			Source.
#				# Plane 1
#				Det_x, Det_y = kbv.GetXY_TransversePlaneAtF2(Det_Size, NAuto, Defocus )
#				Det_ds = np.sqrt((Det_x[0] - Det_x[-1])**2 + (Det_y[0] - Det_y[-1])**2)
#				# E1
#				E1[i,:] = HuygensIntegral_1d_MultiPool(Lambda,
#														Mir_E,Mir_x, Mir_y, Det_x, Det_y, NPools)
#
#				Det_s = xy_to_s(Det_x, Det_y)
#				return E1, Det_s
#'''
