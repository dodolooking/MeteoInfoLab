#-----------------------------------------------------
# Author: Yaqiang Wang
# Date: 2014-12-27
# Purpose: MeteoInfo dimarray module
# Note: Jython
#-----------------------------------------------------
from org.meteoinfo.projection import ProjectionInfo, KnownCoordinateSystems, Reproject
from org.meteoinfo.data import GridData, GridArray, StationData, ArrayMath, ArrayUtil
from org.meteoinfo.data.meteodata import Dimension, DimensionType
from org.meteoinfo.geoprocess.analysis import ResampleMethods
from org.meteoinfo.layer import VectorLayer
from org.meteoinfo.global import PointD
from ucar.ma2 import Array, Range, MAMath
import miarray
import milayer
from miarray import MIArray
from milayer import MILayer
import math
import datetime
import miutil
from java.lang import Double

nan = Double.NaN

# Dimension array
class DimArray():
    
    # array must be MIArray
    def __init__(self, array=None, dims=None, fill_value=-9999.0, proj=None):
        self.array = array
        if not array is None:
            self.rank = array.rank
            self.shape = array.shape
            self.datatype = array.datatype
            if self.rank > 0:
                self.sizestr = str(self.shape[0])
                if self.rank > 1:
                    for i in range(1, self.rank):
                        self.sizestr = self.sizestr + '*%s' % self.shape[i]
            else:
                self.sizestr = '1'
        self.dims = dims
        if not dims is None:
            self.ndim = len(dims)
        self.fill_value = fill_value        
        if math.isnan(self.fill_value):
            self.fill_value = -9999.0
        self.proj = proj
        
    def __len__(self):
        shape = self.array.getshape()
        len = 1
        for l in shape:
            len = len * l
        return len

    def __str__(self):
        return self.array.__repr__()
        
    def __repr__(self):
        return self.array.__repr__()
        
    def __getitem__(self, indices):
        #print type(indices)
        if not isinstance(indices, tuple):
            inds = []
            inds.append(indices)
            indices = inds
        
        if len(indices) != self.ndim:
            print 'indices must be ' + str(self.ndim) + ' dimensions!'
            return None
            
        if not self.proj is None and not self.proj.isLonLat():
            xlim = None
            ylim = None
            xidx = -1
            yidx = -1
            for i in range(0, self.ndim):
                dim = self.dims[i]
                if dim.getDimType() == DimensionType.X:                    
                    k = indices[i]
                    if isinstance(k, (tuple, list)):
                        xlim = k
                        xidx = i
                elif dim.getDimType() == DimensionType.Y:
                    k = indices[i]
                    if isinstance(k, (tuple, list)):
                        ylim = k
                        yidx = i
            if not xlim is None and not ylim is None:                
                fromproj=KnownCoordinateSystems.geographic.world.WGS1984
                inpt = PointD(xlim[0], ylim[0])
                outpt1 = Reproject.reprojectPoint(inpt, fromproj, self.proj)
                inpt = PointD(xlim[1], ylim[1])
                outpt2 = Reproject.reprojectPoint(inpt, fromproj, self.proj)
                xlim = [outpt1.X, outpt2.X]
                ylim = [outpt1.Y, outpt2.Y]
                indices1 = []
                for i in range(0, self.ndim):
                    if i == xidx:
                        indices1.append(xlim)
                    elif i == yidx:
                        indices1.append(ylim)
                    else:
                        indices1.append(indices[i])
                indices = indices1
            
        #origin = []
        #size = []
        #stride = []
        dims = []
        ranges = []
        flips = []
        iszerodim = True
        for i in range(0, self.ndim):  
            k = indices[i]
            if isinstance(indices[i], int):
                sidx = k
                eidx = k
                step = 1                
            elif isinstance(k, slice):
                sidx = 0 if k.start is None else k.start
                eidx = self.dims[i].getLength()-1 if k.stop is None else k.stop-1
                step = 1 if k.step is None else k.step
            elif isinstance(k, tuple) or isinstance(k, list):
                dim = self.dims[i]
                sidx = dim.getValueIndex(k[0])
                if len(k) == 1:
                    eidx = sidx
                    step = 1
                else:                    
                    eidx = dim.getValueIndex(k[1])
                    if len(k) == 2:
                        step = 1
                    else:
                        step = int(k[2] / dim.getDeltaValue)
            else:
                print k
                return None

            if sidx >= self.shape[i]:
                raise IndexError()
                
            if sidx != eidx:
                iszerodim = False
            if step < 0:
                step = abs(step)
                flips.append(i)
            rr = Range(sidx, eidx, step)
            ranges.append(rr)
            #origin.append(sidx)
            n = eidx - sidx + 1
            #size.append(n)
            #stride.append(step)
            if n > 1:
                dim = self.dims[i]
                dims.append(dim.extract(sidx, eidx, step))
                    
        #r = ArrayMath.section(self.array.array, origin, size, stride)
        r = ArrayMath.section(self.array.array, ranges)
        if iszerodim:
            return r.getObject(0)
        else:
            for i in flips:
                r = r.flip(i)
            rr = Array.factory(r.getDataType(), r.getShape());
            MAMath.copy(rr, r);
            array = MIArray(rr)
            data = DimArray(array, dims, self.fill_value, self.proj)
            return data
        
    def __setitem__(self, indices, value):
        #print type(indices) 
        if isinstance(indices, (MIArray, DimArray)):
            ArrayMath.setValue(self.asarray(), indices.asarray(), value)
            return None
        
        if not isinstance(indices, tuple):
            inds = []
            inds.append(indices)
            indices = inds
        
        if self.rank == 0:
            self.array.array.setObject(0, value)
            return None
        
        if len(indices) != self.rank:
            print 'indices must be ' + str(self.rank) + ' dimensions!'
            return None

        ranges = []
        flips = []        
        for i in range(0, self.rank):   
            if isinstance(indices[i], int):
                sidx = indices[i]
                eidx = indices[i]
                step = 1
            else:
                sidx = 0 if indices[i].start is None else indices[i].start
                eidx = self.shape[i]-1 if indices[i].stop is None else indices[i].stop
                step = 1 if indices[i].step is None else indices[i].step
            if step < 0:
                step = abs(step)
                flips.append(i)
            rr = Range(sidx, eidx, step)
            ranges.append(rr)
    
        if isinstance(value, (MIArray, DimArray)):
            value = value.asarray()
        r = ArrayMath.setSection(self.array.array, ranges, value)
        self.array.array = r
        
    def __add__(self, other):
        r = None
        ArrayMath.fill_value = self.fill_value
        if isinstance(other, DimArray):      
            r = DimArray(self.array.__add__(other.array), self.dims, self.fill_value, self.proj)
        else:
            r = DimArray(self.array.__add__(other), self.dims, self.fill_value, self.proj)
        return r
        
    def __radd__(self, other):
        return DimArray.__add__(self, other)
        
    def __sub__(self, other):
        r = None
        if isinstance(other, DimArray): 
            r = DimArray(self.array.__sub__(other.array), self.dims, self.fill_value, self.proj)
        else:
            r = DimArray(self.array.__sub__(other), self.dims, self.fill_value, self.proj)
        return r
        
    def __rsub__(self, other):
        r = None
        if isinstance(other, DimArray): 
            r = DimArray(self.array.__rsub__(other.array), self.dims, self.fill_value, self.proj)
        else:
            r = DimArray(self.array.__rsub__(other), self.dims, self.fill_value, self.proj)
        return r
        
    def __mul__(self, other):
        r = None
        if isinstance(other, DimArray): 
            r = DimArray(self.array.__mul__(other.array), self.dims, self.fill_value, self.proj)
        else:
            r = DimArray(self.array.__mul__(other), self.dims, self.fill_value, self.proj)
        return r
        
    def __rmul__(self, other):
        return DimArray.__mul__(self, other)
        
    def __div__(self, other):
        r = None
        if isinstance(other, DimArray): 
            r = DimArray(self.array.__div__(other.array), self.dims, self.fill_value, self.proj)
        else:
            r = DimArray(self.array.__div__(other), self.dims, self.fill_value, self.proj)
        return r
        
    def __rdiv__(self, other):
        r = None
        if isinstance(other, DimArray): 
            r = DimArray(self.array.__rdiv__(other.array), self.dims, self.fill_value, self.proj)
        else:
            r = DimArray(self.array.__rdiv__(other), self.dims, self.fill_value, self.proj)
        return r
        
    def __pow__(self, other):
        r = DimArray(self.array.__pow__(other), self.dims, self.fill_value, self.proj)
        return r
        
    def __neg__(self):
        r = DimArray(self.array.__neg__(), self.dims, self.fill_value, self.proj)
        return r
        
    def __lt__(self, other):
        r = DimArray(self.array.__lt__(other), self.dims, self.fill_value, self.proj)
        return r
        
    def __le__(self, other):
        r = DimArray(self.array.__le__(other), self.dims, self.fill_value, self.proj)
        return r
        
    def __eq__(self, other):
        r = DimArray(self.array.__eq__(other), self.dims, self.fill_value, self.proj)
        return r
        
    def __ne__(self, other):
        r = DimArray(self.array.__ne__(other), self.dims, self.fill_value, self.proj)
        return r
        
    def __gt__(self, other):
        r = DimArray(self.array.__gt__(other), self.dims, self.fill_value, self.proj)
        return r
        
    def __ge__(self, other):
        r = DimArray(self.array.__ge__(other), self.dims, self.fill_value, self.proj)
        return r   

    def __and__(self, other):
        r = DimArray(self.array.__and__(other), self.dims, self.fill_value, self.proj)
        return r
        
    def astype(self, dtype):
        r = DimArray(self.array.astype(dtype), self.dims, self.fill_value, self.proj)
        return r
    
    def value(self, indices):
        #print type(indices)
        if not isinstance(indices, tuple):
            inds = []
            inds.append(indices)
            indices = inds
        
        if len(indices) != self.ndim:
            print 'indices must be ' + str(self.ndim) + ' dimensions!'
            return None
            
        #origin = []
        #size = []
        #stride = []
        dims = []
        ranges = []
        flips = []
        for i in range(0, self.ndim):  
            k = indices[i]
            if isinstance(indices[i], int):
                sidx = k
                eidx = k
                step = 1                
            elif isinstance(k, slice):
                sidx = 0 if k.start is None else k.start
                eidx = self.dims[i].getLength()-1 if k.stop is None else k.stop
                step = 1 if k.step is None else k.step
            elif isinstance(k, tuple) or isinstance(k, list):
                dim = self.dims[i]
                sidx = dim.getValueIndex(k[0])
                if len(k) == 1:
                    eidx = sidx
                    step = 1
                else:                    
                    eidx = dim.getValueIndex(k[1])
                    if len(k) == 2:
                        step = 1
                    else:
                        step = int(k[2] / dim.getDeltaValue)
            else:
                print k
                return None
                
            if step < 0:
                step = abs(step)
                flips.append(i)
            rr = Range(sidx, eidx, step)
            ranges.append(rr)
            #origin.append(sidx)
            n = eidx - sidx + 1
            #size.append(n)
            #stride.append(step)
            if n > 1:
                dim = self.dims[i]
                dims.append(dim.extract(sidx, eidx, step))
                    
        #r = ArrayMath.section(self.array.array, origin, size, stride)
        r = ArrayMath.section(self.array.array, ranges)
        for i in flips:
            r = r.flip(i)
        rr = Array.factory(r.getDataType(), r.getShape());
        MAMath.copy(rr, r);
        array = MIArray(rr)
        data = DimArray(array, dims, self.fill_value, self.proj)
        return data
    
    def getsize():
        if name == 'size':
            sizestr = str(self.shape[0])
            if self.rank > 1:
                for i in range(1, self.rank):
                    sizestr = sizestr + '*%s' % self.shape[i]
            return sizestr
    
    # get dimension length
    def dimlen(self, idx=0):
        return self.dims[idx].getLength()
        
    def dimvalue(self, idx=0):
        return MIArray(ArrayUtil.array(self.dims[idx].getDimValue()))
        
    def setdimvalue(self, idx, dimvalue):
        if isinstance(dimvalue, (MIArray, DimArray)):
            dimvalue = dimvalue.aslist()
        self.dims[idx].setDimValues(dimvalue)
        
    def adddim(self, dimvalue, dimtype=None, index=None):
        if isinstance(dimvalue, (MIArray, DimArray)):
            dimvalue = dimvalue.aslist()
        dtype = DimensionType.Other
        if not dimtype is None:
            if dimtype.upper() == 'X':
                dtype = DimensionType.X
            elif dimtype.upper() == 'Y':
                dtype = DimensionType.Y
            elif dimtype.upper() == 'Z':
                dtype = DimensionType.Z
            elif dimtype.upper() == 'T':
                dtype = DimensionType.T
        dim = Dimension(dtype)
        dim.setDimValues(dimvalue)
        if self.dims is None:
            self.dims = [dim]
        else:
            if index is None:
                self.dims.append(dim)
            else:
                self.dims.insert(index, dim)
        self.ndim = len(self.dims)
        
    def xdim(self):
        for dim in self.dims:
            if dim.getDimType() == DimensionType.X:
                return dim        
        return None
        
    def ydim(self):
        for dim in self.dims:
            if dim.getDimType() == DimensionType.Y:
                return dim        
        return None
        
    def zdim(self):
        for dim in self.dims:
            if dim.getDimType() == DimensionType.Z:
                return dim        
        return None
        
    def tdim(self):
        for dim in self.dims:
            if dim.getDimType() == DimensionType.T:
                return dim        
        return None
        
    def islondim(self, idx=0):
        dim = self.dims[idx]
        if dim.getDimType() == DimensionType.X and self.proj.isLonLat():
            return True
        else:
            return False
            
    def islatdim(self, idx=0):
        dim = self.dims[idx]
        if dim.getDimType() == DimensionType.Y and self.proj.isLonLat():
            return True
        else:
            return False
            
    def islonlatdim(self, idx=0):
        return self.islondim(idx) or self.islatdim(idx)
            
    def istimedim(self, idx=0):
        dim = self.dims[idx]
        if dim.getDimType() == DimensionType.T:
            return True
        else:
            return False
                   
    def asgriddata(self):
        xdata = self.dims[1].getDimValue()
        ydata = self.dims[0].getDimValue()
        gdata = GridData(self.array.array, xdata, ydata, self.fill_value, self.proj)
        return PyGridData(gdata)
        
    def asgridarray(self):
        xdata = self.dims[1].getDimValue()
        ydata = self.dims[0].getDimValue()
        gdata = GridArray(self.array.array, xdata, ydata, self.fill_value, self.proj)
        return gdata
        
    def sqrt(self):
        r = DimArray(self.array.sqrt(), self.dims, self.fill_value, self.proj)
        return r
    
    def sin(self):
        r = DimArray(self.array.sin(), self.dims, self.fill_value, self.proj)
        return r
        
    def cos(self):
        r = DimArray(self.array.cos(), self.dims, self.fill_value, self.proj)
        return r
        
    def tan(self):
        r = DimArray(self.array.tan(), self.dims, self.fill_value, self.proj)
        return r
        
    def asin(self):
        r = DimArray(self.array.asin(), self.dims, self.fill_value, self.proj)
        return r
        
    def acos(self):
        r = DimArray(self.array.acos(), self.dims, self.fill_value, self.proj)
        return r
        
    def atan(self):
        r = DimArray(self.array.atan(), self.dims, self.fill_value, self.proj)
        return r
        
    def exp(self):
        r = DimArray(self.array.exp(), self.dims, self.fill_value, self.proj)
        return r
        
    def log(self):
        r = DimArray(self.array.log(), self.dims, self.fill_value, self.proj)
        return r
        
    def log10(self):
        r = DimArray(self.array.log10(), self.dims, self.fill_value, self.proj)
        return r
        
    def min(self):
        return self.array.min()
        
    def max(self):
        return self.array.max()
        
    def sum(self):
        return self.array.sum()
        
    def ave(self):
        return self.array.ave()
        
    def setdata(self, v, x=None, y=None, method='mean'):
        '''
        Set data values according the locations.
        
        :param v: (*array_like*) The data array.
        :param x: (*array_like*) X coordinate array.
        :param y: (*array_like*) Y coordinate array.
        :param method: (*string*) Method, ['mean' | 'max' | 'min' | 'count'].               
        '''
        if x is None:
            x = self.dimvalue(1)
            y = self.dimvalue(0)
        
        
    def inpolygon(self, polygon):
        #x = self.dims[1].getDimValue()
        #y = self.dims[0].getDimValue()
        x = self.dimvalue(1)
        y = self.dimvalue(0)
        if isinstance(polygon, tuple):
            x_p = polygon[0]
            y_p = polygon[1]
            if isinstance(x_p, MIArray):
                x_p = x_p.aslist()
            if isinstance(y_p, MIArray):
                y_p = y_p.aslist()
            r = self.array.inpolygon(x, y, x_p, y_p)
        else:
            r = self.array.inpolygon(x, y, polygon)
        r = DimArray(r, self.dims, self.fill_value, self.proj)
        return r
        
    def maskout(self, mask):
        if isinstance(mask, (MIArray, DimArray)):
            r = ArrayMath.maskout(self.asarray(), mask.asarray())
            return DimArray(MIArray(r), self.dims, self.fill_value, self.proj)
        else:
            x = self.dims[1].getDimValue()
            y = self.dims[0].getDimValue()
            r = DimArray(self.array.maskout(mask, x, y), self.dims, self.fill_value, self.proj)
            return r
     
    def aslist(self):
        return ArrayMath.asList(self.array.array)
        
    def asarray(self):
        return self.array.array
        
    def reshape(self, *args):
        return self.array.reshape(*args)
        
    def interpn(self, xi):
        """
        Multidimensional interpolation on regular grids.

        :param xi: (*list*) The coordinates to sample the gridded data at.
        
        :returns: (*float*) Interpolated value at input coordinates.
        """
        points = []
        for i in range(self.ndim):
            points.append(self.dims[i].getDimValue())
        if isinstance(xi, (MIArray, DimArray)):
            xi = xi.aslist()
        nxi = []
        for x in xi:
            if isinstance(x, datetime.datetime):
                x = miutil.date2num(x)
            nxi.append(x)
        r = ArrayUtil.interpn(points, self.asarray(), nxi)
        return r
     
    def tostation(self, x, y):
        gdata = self.asgriddata()
        if isinstance(x, MIArray) or isinstance(x, DimArray):
            r = gdata.data.toStation(x.aslist(), y.aslist())
            return MIArray(ArrayUtil.array(r))
        else:
            return gdata.data.toStation(x, y)
            
    def project(self, x=None, y=None, toproj=None, method='bilinear'):
        """
        Project array
        
        :param x: To x coordinates.
        :param y: To y coordinates.
        :param toproj: To projection.
        :param method: Interpolation method: ``bilinear`` or ``neareast`` .
        
        :returns: (*MIArray*) Projected array
        """
        yy = self.dims[self.ndim - 2].getDimValue()
        xx = self.dims[self.ndim - 1].getDimValue()
        if toproj is None:
            toproj = self.proj
        
        if x is None or y is None:
            pr = ArrayUtil.reproject(self.array.array, xx, yy, self.proj, toproj)
            r = pr[0]
            x = pr[1]
            y = pr[2]
            dims = []
            ydim = Dimension()
            ydim.setDimValues(MIArray(y).aslist())
            dims.append(ydim)
            xdim = Dimension()
            xdim.setDimValues(MIArray(x).aslist())    
            dims.append(xdim)
            rr = DimArray(MIArray(r), dims, self.fill_value, toproj)
            return rr
        
        if method == 'bilinear':
            method = ResampleMethods.Bilinear
        else:
            method = ResampleMethods.NearestNeighbor
        if isinstance(x, list):
            r = ArrayUtil.reproject(self.array.array, xx, yy, x, y, self.proj, toproj, self.fill_value, method)
        elif isinstance(x, MIArray):
            if x.rank == 1:
                r = ArrayUtil.reproject(self.array.array, xx, yy, x.aslist(), y.aslist(), self.proj, toproj, self.fill_value, method)
            else:
                r = ArrayUtil.reproject(self.array.array, xx, yy, x.asarray(), y.asarray(), self.proj, toproj, self.fill_value, method)
        else:
            r = ArrayUtil.reproject(self.array.array, xx, yy, x.asarray(), y.asarray(), self.proj, toproj, self.fill_value, method)
        #r = ArrayUtil.reproject(self.array.array, xx, yy, x.asarray(), y.asarray(), self.proj, toproj, self.fill_value, method)
        return MIArray(r)
            
    def join(self, b, dimidx):
        r = ArrayMath.join(self.array.array, b.array.array, dimidx)
        dima = self.dimvalue(dimidx)
        dimb = b.dimvalue(dimidx)
        dimr = []
        if dima[0] < dimb[0]:
            for i in range(0, len(dima)):
                dimr.append(dima[i])
            for i in range(0, len(dimb)):
                dimr.append(dimb[i])
        else:
            for i in range(0, len(dimb)):
                dimr.append(dimb[i])
            for i in range(0, len(dima)):
                dimr.append(dima[i])
        rdims = []
        for i in range(0, len(self.dims)):
            if i == dimidx:
                ndim = Dimension()
                ndim.setDimValues(dimr)
                rdims.append(ndim)
            else:
                rdims.append(self.dims[i])
        return DimArray(MIArray(r), rdims, self.fill_value, self.proj)
        
    def savegrid(self, fname, format='surfer', **kwargs):
        gdata = self.asgridarray()
        if format == 'surfer':
            gdata.saveAsSurferASCIIFile(fname)
        elif format == 'bil':
            gdata.saveAsBILFile(fname)
        elif format == 'esri_ascii':
            gdata.saveAsESRIASCIIFile(fname)
        elif format == 'micaps4':
            desc = kwargs.pop('description', 'var')
            date = kwargs.pop('date', datetime.datetime.now())
            date = miutil.jdate(date)
            hours = kwargs.pop('hours', 0)
            level = kwargs.pop('level', 0)
            smooth = kwargs.pop('smooth', 1)
            boldvalue =kwargs.pop('boldvalue', 0)
            proj = kwargs.pop('proj', self.proj)
            if proj is None:
                gdata.saveAsMICAPS4File(fname, desc, date, hours, level, smooth, boldvalue)
            else:
                if proj.isLonLat():
                    gdata.saveAsMICAPS4File(fname, desc, date, hours, level, smooth, boldvalue)
                else:
                    gdata.saveAsMICAPS4File(fname, desc, date, hours, level, smooth, boldvalue, proj)
    
       
# The encapsulate class of GridData
class PyGridData():
    
    # griddata must be a GridData object
    def __init__(self, griddata=None):
        if griddata != None:
            self.data = griddata
        else:
            self.data = GridData()
    
    def __getitem__(self, indices):
        print type(indices)
        if not isinstance(indices, tuple):
            print 'indices must be tuple!'
            return None
        
        if len(indices) != 2:
            print 'indices must be 2 dimension!'
            return None

        if isinstance(indices[0], int):
            sxidx = indices[0]
            exidx = indices[0]
            xstep = 1
        else:
            sxidx = 0 if indices[0].start is None else indices[0].start
            exidx = self.data.getXNum() if indices[0].stop is None else indices[0].stop
            xstep = 1 if indices[0].step is None else indices[0].step
        if isinstance(indices[1], int):
            syidx = indices[1]
            eyidx = indices[1]
            ystep = 1
        else:
            syidx = 0 if indices[1].start is None else indices[1].start
            eyidx = self.data.getYNum() if indices[1].stop is None else indices[1].stop
            ystep = 1 if indices[1].step is None else indices[1].step
        gdata = PyGridData(self.data.extract(sxidx, exidx, xstep, syidx, eyidx, ystep))
        return gdata
    
    def add(self, other):
        gdata = None
        if isinstance(other, PyGridData):            
            gdata = PyGridData(self.data.add(other.data))
        else:
            gdata = PyGridData(self.data.add(other))
        return gdata
    
    def __add__(self, other):
        gdata = None
        print isinstance(other, PyGridData)
        if isinstance(other, PyGridData):            
            gdata = PyGridData(self.data.add(other.data))
        else:
            gdata = PyGridData(self.data.add(other))
        return gdata
        
    def __radd__(self, other):
        return PyGridData.__add__(self, other)
        
    def __sub__(self, other):
        gdata = None
        if isinstance(other, PyGridData):
            gdata = PyGridData(self.data.sub(other.data))
        else:
            gdata = PyGridData(self.data.sub(other))
        return gdata
        
    def __rsub__(self, other):
        gdata = None
        if isinstance(other, PyGridData):
            gdata = PyGridData(other.data.sub(self.data))
        else:
            gdata = PyGridData(DataMath.sub(other, self.data))
        return gdata
    
    def __mul__(self, other):
        gdata = None
        if isinstance(other, PyGridData):
            gdata = PyGridData(self.data.mul(other.data))
        else:
            gdata = PyGridData(self.data.mul(other))
        return gdata
        
    def __rmul__(self, other):
        return PyGridData.__mul__(self, other)
        
    def __div__(self, other):
        gdata = None
        if isinstance(other, PyGridData):
            gdata = PyGridData(self.data.div(other.data))
        else:
            gdata = PyGridData(self.data.div(other))
        return gdata
        
    def __rdiv__(self, other):
        gdata = None
        if isinstance(other, PyGridData):
            gdata = PyGridData(other.data.div(self.data))
        else:
            gdata = PyGridData(DataMath.div(other, self))
        return gdata
        
    # other must be a numeric data
    def __pow__(self, other):
        gdata = PyGridData(self.data.pow(other))
        return gdata
        
    def min(self):
        return self.data.getMinValue()
        
    def max(self):
        return self.data.getMaxValue()  

    def interpolate(self):
        return PyGridData(self.data.interpolate())
        
    def asdimarray(self):
        a = self.data.getArray()
        dims = self.data.getDimensions()
        return DimArray(MIArray(a), dims, self.data.missingValue, self.data.projInfo)

    def savedata(self, filename):
        self.data.saveAsSurferASCIIFile(filename)
        
###############################################################         
# The encapsulate class of StationData
class PyStationData():
    
    # data must be a StationData object
    def __init__(self, data=None):
        self.data = data
    
    def __len__(self):
        return self.data.getStNum()
        
    def __getitem__(self, indices):
        if isinstance(indices, int):    #Data index
            idx = indices
            stid = self.data.getStid(idx)
            x = self.data.getX(idx)
            y = self.data.getY(idx)
            return stid, x, y
        elif isinstance(indices, str):    #Station identifer
            stid = indices
            idx = self.data.indexOf(stid)
            x = self.data.getX(idx)
            y = self.data.getY(idx)
            return stid, x, y
        else:
            return None
    
    def add(self, other):
        gdata = None
        if isinstance(other, PyStationData):            
            gdata = PyStationData(self.data.add(other.data))
        else:
            gdata = PyStationData(self.data.add(other))
        return gdata
    
    def __add__(self, other):
        gdata = None
        if isinstance(other, PyStationData):            
            gdata = PyStationData(self.data.add(other.data))
        else:
            gdata = PyStationData(self.data.add(other))
        return gdata
        
    def __radd__(self, other):
        return PyStationData.__add__(self, other)
        
    def __sub__(self, other):
        gdata = None
        if isinstance(other, PyStationData):
            gdata = PyStationData(self.data.sub(other.data))
        else:
            gdata = PyStationData(self.data.sub(other))
        return gdata
        
    def __rsub__(self, other):
        gdata = None
        if isinstance(other, PyStationData):
            gdata = PyStationData(other.data.sub(self.data))
        else:
            gdata = PyStationData(DataMath.sub(other, self.data))
        return gdata
    
    def __mul__(self, other):
        gdata = None
        if isinstance(other, PyStationData):
            gdata = PyStationData(self.data.mul(other.data))
        else:
            gdata = PyStationData(self.data.mul(other))
        return gdata
        
    def __rmul__(self, other):
        return PyStationData.__mul__(self, other)
        
    def __div__(self, other):
        gdata = None
        if isinstance(other, PyStationData):
            gdata = PyStationData(self.data.div(other.data))
        else:
            gdata = PyStationData(self.data.div(other))
        return gdata
        
    def __rdiv__(self, other):
        gdata = None
        if isinstance(other, PyStationData):
            gdata = PyStationData(other.data.div(self.data))
        else:
            gdata = PyStationData(DataMath.div(other, self))
        return gdata
        
    # other must be a numeric data
    def __pow__(self, other):
        gdata = PyStationData(self.data.pow(other))
        return gdata        
        
    def toarray(self):
        r = ArrayUtil.getArraysFromStationData(self.data)
        return MIArray(r[0]), MIArray(r[1]), MIArray(r[2])
        
    def min(self):
        return self.data.getMinValue()
        
    def minloc(self):
        minv = self.data.getMinValueIndex()
        return minv[0], minv[1]
        
    def max(self):
        return self.data.getMaxValue()    

    def maxloc(self):
        maxv = self.data.getMaxValueIndex() 
        return maxv[0], maxv[1]     
        
    def maskout(self, polygon):
        if isinstance(polygon, MILayer):
            polygon = polygon.layer
        return PyStationData(self.data.maskout(polygon))
        
    def maskin(self, polygon):
        return PyStationData(self.data.maskin(polygon))
        
    def filter(self, stations):
        return PyStationData(self.data.filter(stations))
        
    def join(self, other):
        return PyStationData(self.data.join(other.data))     

    def ave(self):
        return self.data.average()
        
    def mean(self):
        return self.data.average()
        
    def sum(self):
        return self.data.sum()
        
    def griddata(self, xi=None, **kwargs):
        method = kwargs.pop('method', 'idw')
        fill_value = self.data.missingValue
        x_s = MIArray(ArrayUtil.array(self.data.getXList()))
        y_s = MIArray(ArrayUtil.array(self.data.getYList()))
        if xi is None:            
            xn = int(math.sqrt(len(x_s)))
            yn = xn
            x_g = MIArray(ArrayUtil.lineSpace(x_s.min(), x_s.max(), xn, True))
            y_g = MIArray(ArrayUtil.lineSpace(y_s.min(), y_s.max(), yn, True))     
        else:
            x_g = xi[0]
            y_g = xi[1]
        if isinstance(x_s, MIArray):
            x_s = x_s.aslist()
        if isinstance(y_s, MIArray):
            y_s = y_s.aslist()    
        if isinstance(x_g, MIArray):
            x_g = x_g.aslist()
        if isinstance(y_g, MIArray):
            y_g = y_g.aslist()
        if method == 'idw':
            pnum = kwargs.pop('pointnum', 2)
            radius = kwargs.pop('radius', None)
            if radius is None:
                r = self.data.interpolate_Neighbor(x_g, y_g, pnum, fill_value)
                return PyGridData(r)
            else:
                r = self.data.interpolate_Radius(x_g, y_g, pnum, radius, fill_value)
                return PyGridData(r)
        elif method == 'cressman':
            radius = kwargs.pop('radius', [10, 7, 4, 2, 1])
            if isinstance(radius, MIArray):
                radius = radius.aslist()
            r = self.data.interpolate_Cressman(x_g, y_g, radius, fill_value)
            return PyGridData(r)
        elif method == 'neareast':
            r = self.data.interpolate_Assign(x_g, y_g, fill_value)
            return PyGridData(r)
        else:
            return None
        
    def savedata(self, filename, fieldname='data', savemissingv=False):
        self.data.saveAsCSVFile(filename, fieldname, savemissingv)