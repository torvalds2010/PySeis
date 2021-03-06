import numpy as np
import time      
import sys


#==================================================
#              timing decorator
#==================================================
import time
def timeit(method):

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print '%r %2.2f sec' % \
              (method.__name__,  te-ts)
        return result

    return timed

traceHeaderDtype = np.dtype([
('tracl', np.int32),
('tracr', np.int32),
('fldr', np.int32),
('tracf', np.int32),
('ep', np.int32),
('cdp', np.int32),
('cdpt', np.int32),
('trid', np.int16),
('nvs', np.int16),
('nhs', np.int16),
('duse', np.int16),
('offset', np.int32),
('gelev', np.int32),
('selev', np.int32),
('sdepth', np.int32),
('gdel', np.int32),
('sdel', np.int32),
('swdep', np.int32),
('gwdep', np.int32),
('scalel', np.int16),
('scalco', np.int16),
('sx', np.int32),
('sy', np.int32),
('gx', np.int32),
('gy', np.int32),
('counit', np.int16),
('wevel', np.int16),
('swevel', np.int16),
('sut', np.int16),
('gut', np.int16),
('sstat', np.int16),
('gstat', np.int16),
('tstat', np.int16),
('laga', np.int16),
('lagb', np.int16),
('delrt', np.int16),
('muts', np.int16),
('mute', np.int16),
('ns', np.uint16),
('dt', np.uint16),
('gain', np.int16),
('igc', np.int16),
('igi', np.int16),
('corr', np.int16),
('sfs', np.int16),
('sfe', np.int16),
('slen', np.int16),
('styp', np.int16),
('stas', np.int16),
('stae', np.int16),
('tatyp', np.int16),
('afilf', np.int16),
('afils', np.int16),
('nofilf', np.int16),
('nofils', np.int16),
('lcf', np.int16),
('hcf', np.int16),
('lcs', np.int16),
('hcs', np.int16),
('year', np.int16),
('day', np.int16),
('hour', np.int16),
('minute', np.int16),
('sec', np.int16),
('timebas', np.int16),
('trwf', np.int16),
('grnors', np.int16),
('grnofr', np.int16),
('grnlof', np.int16),
('gaps', np.int16),
('otrav', np.int16), #179,180
('d1', np.float32), #181,184
('f1', np.float32), #185,188
('d2', np.float32), #189,192
('f2', np.float32), #193, 196
('ShotPoint', np.int32), #197,200
('unscale', np.int16), #201, 204
('TraceValueMeasurementUnit', np.int16),
('TransductionConstantMantissa', np.int32),
('TransductionConstantPower', np.int16),
('TransductionUnit', np.int16),
('TraceIdentifier', np.int16),
('ScalarTraceHeader', np.int16),
('SourceType', np.int16),
('SourceEnergyDirectionMantissa', np.int32),
('SourceEnergyDirectionExponent', np.int16),
('SourceMeasurementMantissa', np.int32),
('SourceMeasurementExponent', np.int16),
('SourceMeasurementUnit', np.int16),
('UnassignedInt1', np.int32),
('ns1', np.int32),
])

def build_dtype(_ns):
    '''
    builds a numpy dtype as defined
    in format. 
    '''
    return np.dtype(traceHeaderDtype.descr + [('trace', ('<f4',_ns))])

def getNs(file):
    '''
    reaches into the SU file and reads the number of samples
    fom the first trace header.
    '''
    return np.fromfile(file, dtype=traceHeaderDtype, count=1)['ns']

def loadSU(infile, outfile):
    '''
    initialises a file
    i.e. memmaps the SU file to a numpy array.
    '''
    _ns = getNs(infile)
    _type = build_dtype(_ns)
    indata= np.memmap(infile, dtype=_type, mode='r')
    outdata = np.lib.format.open_memmap(outfile, dtype=_type, shape=indata.shape, mode='w+')
    outdata[:] = indata[:]
    outdata.flush()
    
def saveSU(infile, outfile):
    ''' 
    saves npy file infile
    to su file outfile
    '''
    np.lib.format.open_memmap(infile, mode='r').tofile(outfile)
    
        

def update_progress(progress):
    barLength = 10 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(barLength*progress))
    text = "\rMb/S: [{0}] {1}% {2}".format( "#"*block + "-"*(barLength-block), progress*100, status)
    sys.stdout.write(text)
    sys.stdout.flush()
    
class Gather(object):
    '''
    data object which contains 
    
     * the gather to be processed
     * its source and destination (memmapped files)
     * the mask used to extract and save
     '''

    def __init__(self, source, dest, mask):
        self.data = np.array(source[mask])
        self.dest = dest
        self.mask = mask

    def __getitem__(self, i):
        return self.data[i]

    def save(self):
        self.dest[self.mask] = self.data
        
    def close(self):
        self.dest.flush()
        
        

class Stream(object):
    '''
    streams in the seismic data in gathers
    needs the sort order to be definied.
    requires input to be .npy file
    '''

    def __init__(self, infile, outfile, order=['fldr', 'tracf']): #default to shot gathers
        self.primaryOrder = order[0]
        self.secondaryOrder = order[1]
        self.indata = np.lib.format.open_memmap(infile, mode='r')    
        self.outdata = np.lib.format.open_memmap(outfile, dtype=self.indata.dtype, shape= self.indata.shape, mode='w+') 
        self.outdata[:] = self.indata[:]
        self.outdata['trace'].fill(0.0)
        self.outdata.flush()


    def __iter__(self):
        keys = np.unique(self.indata[self.primaryOrder])
        steps = (len(keys)*1.0)
        t = time.time()
        for count, key in enumerate(keys):
            mask = self.indata[self.primaryOrder] == key
            gather = Gather(self.indata, self.outdata, mask)
            gather.data.sort(order=self.secondaryOrder)
            update_progress(gather.data.nbytes*1e-6/time.time()-t)
            t = time.time()
            yield gather
            
    def save(self):
        self.outdata[self.mask] = self.gather

    def close(self):
        del self.outdata
            


        
            

        
        
    
    
