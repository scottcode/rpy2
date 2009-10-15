from rpy2.robjects.robject import RObjectMixin, RObject
import rpy2.rinterface as rinterface
#import rpy2.robjects.conversion as conversion
import conversion

baseenv_ri = rinterface.baseenv

#needed to avoid circular imports
_parse = rinterface.baseenv['parse']
_reval = rinterface.baseenv['eval']
NULL = _reval(_parse(text = rinterface.StrSexpVector(("NULL", ))))


class Function(RObjectMixin, rinterface.SexpClosure):
    """ An R function.
    
    """

    __formals = baseenv_ri.get('formals')
    __local = baseenv_ri.get('local')
    __call = baseenv_ri.get('call')
    __assymbol = baseenv_ri.get('as.symbol')
    __newenv = baseenv_ri.get('new.env')

    _local_env = None

    def __init__(self, *args, **kwargs):
        super(Function, self).__init__(*args, **kwargs)
        self._local_env = self.__newenv(hash=rinterface.BoolSexpVector((True, )))

    def __call__(self, *args, **kwargs):
        new_args = [conversion.py2ri(a) for a in args]
        new_kwargs = {}
        for k, v in kwargs.iteritems():
            new_kwargs[k] = conversion.py2ri(v)
        res = super(Function, self).__call__(*new_args, **new_kwargs)
        res = conversion.ri2py(res)
        return res

    def formals(self):
        """ Return the signature of the underlying R function 
        (as the R function 'formals()' would). """
        res = self.__formals(self)
        res = conversion.ri2py(res)
        return res

class SignatureTranslatedFunction(Function):
    """ Wraps an R function in such way that the R argument names with the
    character '.' are replaced with '_' whenever present """
    _prm_translate = None

    def __init__(self, *args):
        super(SignatureTranslatedFunction, self).__init__(*args)
        prm_translate = {}
        if not self.formals().rsame(NULL):
            for r_param in self.formals().names:
                py_param = r_param.replace('.', '_')
                if py_param in prm_translate:
                    raise ValueError("Error: '%s' already in the transalation table" %r_param)
                if py_param != r_param:
                    prm_translate[py_param] = r_param
        self._prm_translate = prm_translate

    def __call__(self, *args, **kwargs):
        prm_translate = self._prm_translate
        for k in tuple(kwargs.keys()):
            r_k = prm_translate.get(k, None)
            if r_k is not None:
                v = kwargs.pop(k)
                kwargs[r_k] = v
        return super(SignatureTranslatedFunction, self).__call__(*args, **kwargs)
