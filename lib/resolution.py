import math

def TruncateToResolution(f, res):
	resexp = int(math.ceil(math.log10(abs(res))))	
	f = f*10**(-resexp)
	f = int(f)
	f = f*10**(resexp)
	return f
	
def SetPrecisionToResolution(f, res):
	resexp = int(math.ceil(math.log10(abs(res))))
	fexp = int(math.ceil(math.log10(abs(f))))
	f.strip_zeros=False
	f.prec = fexp-resexp-1
	return f