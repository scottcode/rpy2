"""
R objects as Python objects.

The module is structured around the singleton r of class R,
that represents an embedded R.

"""

import os
import array
import rpy2.rinterface as rinterface


#FIXME: close everything when leaving (check RPy for that).

def default_ri2py(o):
    if isinstance(o, RObject):
        res = o
    elif isinstance(o, rinterface.SexpVector):
        res = RVector(o)
    elif isinstance(o, rinterface.SexpClosure):
        res = RFunction(o)
    elif isinstance(o, rinterface.SexpEnvironment):
        res = REnvironment(o)
    elif isinstance(o, rinterface.SexpS4):
        res = RS4(o)
    else:
        res = RObject(o)
    return res

#FIXME: clean and nice mechanism to allow user-specified mapping function
#FIXME: better names for the functions
ri2py = default_ri2py

def default_py2ri(o):
    if isinstance(o, RObject):
        res = rinterface.Sexp(o)
    if isinstance(o, rinterface.Sexp):
        res = o
    elif isinstance(o, array.array):
        if o.typecode in ('h', 'H', 'i', 'I'):
            res = rinterface.SexpVector(o, rinterface.INTSXP)
        elif o.typecode in ('f', 'd'):
            res = rinterface.SexpVector(o, rinterface.REALSXP)
        else:
            raise(ValueError("Nothing can be done for this array type at the moment."))
    elif isinstance(o, bool):
        res = rinterface.SexpVector([o, ], rinterface.LGLSXP)
    elif isinstance(o, int):
        res = rinterface.SexpVector([o, ], rinterface.INTSXP)
    elif isinstance(o, float):
        res = rinterface.SexpVector([o, ], rinterface.REALSXP)
    elif isinstance(o, str):
        res = rinterface.SexpVector([o, ], rinterface.STRSXP)
    elif isinstance(o, list):
        res = r.list(*[ri2py(py2ri(x)) for x in o])
    else:
        raise(ValueError("Nothing can be done for this type at the moment."))
    return res

py2ri = default_py2ri


def default_py2ro(o):
    res = default_py2ri(o)
    return default_ri2py(res)

py2ro = default_py2ro


def repr_robject(o):
    s = r.deparse(o)
    s = str.join(os.linesep, s)
    return s


class RObjectMixin(object):
    name = None

    def __str__(self):
        tmp = baseNameSpaceEnv["fifo"]("")
        baseNameSpaceEnv["sink"](tmp)
        r.show(self)
        baseNameSpaceEnv["sink"]()
        s = baseNameSpaceEnv["readLines"](tmp)
        r.close(tmp)
        s = str.join(os.linesep, s)
        return s

    def __repr__(self):
        return repr_robject(self)

    def typeof(self):
        return super(rinterface.Sexp, self).typeof()

    def do_slot(self, name):
        return super(rinterface.Sexp, self).do_slot(name)

    def rclass(self):
        return baseNameSpaceEnv["class"](self)


class RObject(rinterface.Sexp, RObjectMixin):
    def __setattr__(self, name, value):
        if name == '_sexp':
            if not isinstance(value, rinterface.Sexp):
                raise ValueError("_attr must contain an object " +\
                                     "that inherits from rinterface.Sexp" +\
                                     "(not from %s)" %type(value))
        super(RObject, self).__setattr__(name, value)
    


class RVector(rinterface.SexpVector, RObjectMixin):
    """ R vector-like object. Items in those instances can
       be accessed with the method "__getitem__" ("[" operator),
       or with the method "subset"."""

    def __init__(self, o):
        if not isinstance(o, rinterface.SexpVector):
            o = py2ri(o)
        super(RVector, self).__init__(o)
            

    def subset(self, *args, **kwargs):
        """ Subset the "R-way.", using R's "[" function. 
           In a nutshell, R indexing differs from Python's with
           - indexing can be done with integers or strings (that are 'names')
           - an index equal to TRUE will mean everything selected (because of the recycling rule)
           - integer indexing starts at one
           - negative integer indexing means exclusion of the given integers
           - an index is itself a vector of elements to select
        """
        
        #for a in args:
        #    if not isinstance(a, Rvector):
        #        raise(TypeError("Subset only take R vectors"))
        args = [py2ro(x) for x in args]
        for k, v in kwargs.itervalues():
            args[k] = py2ro(v)
        
        res = r["["](*([self, ] + [x for x in args]), **kwargs)
        return res

    def __getitem__(self, i):
        res = super(RVector, self).__getitem__(i)
        if isinstance(res, rinterface.Sexp):
            res = ri2py(res)
        return res

    def __add__(self, x):
        res = r.get("+")(self, x)
        return res

    def __sub__(self, x):
        res = r.get("-")(self, x)
        return res

    def __mul__(self, x):
        res = r.get("*")(self, x)
        return res

    def __div__(self, x):
        res = r.get("/")(self, x)
        return res

    def __divmod__(self, x):
        res = r.get("%%")(self, x)
        return res

    def __or__(self, x):
        res = r.get("|")(self, x)
        return res

    def __and__(self, x):
        res = r.get("&")(self, x)
        return res

    def getNames(self):
        res = r.names(self)
        return res

class RArray(RVector):
    """ An R array """
    def __init__(self, o):
        super(RArray, self).__init__(o)
        #import pdb; pdb.set_trace()
        if not r["is.array"](self)[0]:
            raise(TypeError("The object must be reflecting an R array"))

    def __getattr__(self, name):
        if name == 'dim':
            res = r.dim(self)
            res = ri2py(res)
            return res

    def __setattr__(self, name, value):
        if name == 'dim':
            value = py2ro(value)
            res = r["dim<-"](value)
        

class RMatrix(RArray):
    """ An R matrix """

    def nrow(self):
        """ Number of rows """
        return self.dim[0]

    def ncol(self):
        """ Number of columns """
        return self.dim[1]

class DataFrame(RVector):
    #FIXME: not implemented
    def __init__(self, o):
        raise Exception("not implemented.")



class RFunction(rinterface.SexpClosure, RObjectMixin):
    """ An R function (aka "closure").
    
    """

    def __call__(self, *args, **kwargs):
        new_args = [py2ri(a) for a in args]
	new_kwargs = {}
        for k, v in kwargs.iteritems():
            new_kwargs[k] = py2ri(v)
        res = super(RFunction, self).__call__(*new_args, **new_kwargs)
        res = ri2py(res)
        return res

    #def getSexp(self):
    #    return super(rinterface.SexpClosure, self).__init__(self)

class REnvironment(rinterface.SexpEnvironment, RObjectMixin):
    """ An R environement. """
    
    def __init__(self, o=None):
        if o is None:
            o = rinterface.baseNameSpaceEnv["new.env"](hash=rinterface.SexpVector([True, ], rinterface.LGLSXP))
        super(REnvironment, self).__init__(o)

    def __getitem__(self, item):
        res = super(REnvironment, self).__getitem__(item)
        res = ri2py(res)
        return res

    def __setitem__(self, item, value):
        robj = py2ro(value)
        super(REnvironment, self).__setitem__(item, robj)

    def get(self, item):
        res = super(REnvironment, self).get(item)
        res = ri2py(res)
        return res

class RS4(rinterface.SexpS4, RObjectMixin):

    def __getattr__(self, attr):
        res = r.get("@")(self, attr)
        return res

    
class R(object):
    _instance = None

    def __init__(self):
        if R._instance is None:
            rinterface.initEmbeddedR()
            R._instance = self
        else:
            raise(ValueError("Only one instance of R can be created"))
        
    def __getattribute__(self, attr):
        return self[attr]

    def __getitem__(self, item):
        res = rinterface.globalEnv.get(item)
	res = ri2py(res)
        return res

    #FIXME: check that this is properly working
    def __cleanup__(self):
        rinterface.endEmbeddedR()
        del(self)

    def __str__(self):
        s = super(R, self).__str__()
        s += str(self["version"])
        return s

    def __call__(self, string):
        p = self.parse(text=string)
        res = self.eval(p)
        return res

r = R()

globalEnv = ri2py(rinterface.globalEnv)
baseNameSpaceEnv = ri2py(rinterface.baseNameSpaceEnv)

