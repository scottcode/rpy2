"""
R objects as Python objects.

The module is structured around the singleton r of class R,
that represents an embedded R.

"""

import array
import rinterface


#FIXME: close everything when leaving (check RPy for that).

def defaultPy2RMapper(self, o):
    if isinstance(o, Robject):
        return o._sexp
    if isinstance(o, rinterface.Sexp):
        return o
    if isinstance(o, array.array):
        if o.typecode in ('h', 'H', 'i', 'I'):
            res = rinterface.SexpVector(o, rinterface.INTSXP)
        elif o.typecode in ('f', 'd'):
            res = rinterface.SexpVector(o, rinterface.REALSXP)
        else:
            raise(ValueError("Nothing can be done for this array type at the moment."))
    elif isinstance(o, int):
        res = rinterface.SexpVector([o, ], rinterface.INTSXP)
    elif isinstance(o, float):
        res = rinterface.SexpVector([o, ], rinterface.REALSXP)
    elif isinstance(o, bool):
        res = rinterface.SexpVector([o, ], rinterface.LGLSXP)
    elif isinstance(o, str):
        res = rinterface.SexpVector([o, ], rinterface.STRSXP)
    else:
        raise(ValueError("Nothing can be done for this type at the moment."))
    return res
    
def defaultR2PyMapper(o):
    if isinstance(o, rinterface.SexpVector):
        res = Rvector(o)
    elif isinstance(o, rinterface.SexpClosure):
        res = Rfunction(o)
    elif isinstance(o, rinterface.SexpEnvironment):
        res = Renvironment(o)
    elif isinstance(o, rinterface.SexpS4):
        res = RS4(o)
    else:
        res = o
    return res


#FIXME: clean and nice mechanism to allow user-specifier mapping function
mapper = defaultR2PyMapper




#FIXME: Looks hackish. inheritance should be used ?
class Robject(object):
    def __repr__(self):
        r.show(self)


class Rvector(Robject):
    """ R vector-like object. Items in those instances can
       be accessed with the method "__getitem__" ("[" operator),
       or with the method "subset"."""

    def __init__(self, o):
        if (isinstance(o, rinterface.SexpVector)):
            self._sexp = o
        else:
            self._sexp = defaultPy2RMapper(self, o)

    def subset(self, *args):
        """ Subset the "R-way.", using R's "[" function """
        for a in args:
            if not isinstance(a, rinterface.SexpVector):
                raise(TypeError("Subset only take R vectors"))
        res = rinterface.globalEnv.get("[")([self._sexp, ] + args)#, drop=drop)
        return res

    def __getitem__(self, i):
        res = self._sexp[i]
        return res

    def __add__(self, x):
        res = r.__getattribute__("+")(self, x)
        return res

    def __sub__(self, x):
        res = r.__getattribute__("-")(self, x)
        return res

    def __mul__(self, x):
        res = r.__getattribute__("*")(self, x)
        return res

    def __div__(self, x):
        res = r.__getattribute__("/")(self, x)
        return res

    def __divmod__(self, x):
        res = r.__getattribute__("%%")(self, x)
        return res

    def __or__(self, x):
        res = r.__getattribute__("|")(self, x)
        return res

    def __and__(self, x):
        res = r.__getattribute__("&")(self, x)
        return res


class Rfunction(Robject):
    """ An R function (aka "closure").
    
    The attribute "mapper" is a function that will
    transform Python objects into Sexp objects.
    """

    mapper = defaultPy2RMapper

    def __init__(self, o):
        if (isinstance(o, rinterface.SexpClosure)):
            self._sexp = o
        else:
            raise(ValueError("Cannot instantiate."))

    def __call__(self, *args, **kwargs):
        new_args = [self.mapper(a) for a in args]
	new_kwargs = {}
        for k, v in kwargs.iteritems():
            new_kwargs[k] = self.mapper(v)
        res = self._sexp(*new_args, **new_kwargs)
        res = mapper(res)
        return res


class Renvironment(Robject):
    """ An R environement. """
    def __init__(self, o):
        if (isinstance(o, rinterface.SexpEnvironment)):
            self._sexp = o
        else:
            raise(ValueError("Cannot instantiate"))

    def __getitem__(self, item):
        res = self._sexp[item]
        res = mapper(res)
        return res

class RS4(Robject):
    def __init__(self, o):
        if (isinstance(o, rinterface.SexpS4)):
            self._sexp = o
        else:
            raise(ValueError("Cannot instantiate"))

    def __getattr__(self, attr):
        res = r.get("@")(self, attr)
        return res

class R(object):
    _instance = None

    def __init__(self, options):
        if R._instance is None:
	    args = ["robjects", ] + options
            rinterface.initEmbeddedR(*args)
            R._instance = self
        else:
            raise(ValueError("Only one instance of R can be created"))
        
    def __getattribute__(self, attr):
        return self[attr]

    def __getitem__(self, item):
        res = rinterface.globalEnv.get(item)
	res = mapper(res)
        return res

r = R(["--no-save", "--quiet"])


