import numpy as np
cimport numpy as np
cimport scipy.special.cython_special as scipy
cimport cython
ctypedef np.float_t DTYPE_t
from libc.math cimport exp, fmax
from nms cimport nms, soft_nms

#CONSTRUCTOR
@cython.cdivision(True)
@cython.boundscheck(False) # turn off bounds-checking for entire function
@cython.wraparound(False)  # turn off negative index wrapping for entire function
def box_constructor(meta, np.ndarray[float,ndim=3] net_out_in):
    cdef:
        np.intp_t H, W, _, C, B, i, j, k, l
        float thresh = meta['thresh']
        int soft = meta['soft_nms']
        float conf
        float m = 0
        float n = 0
        double[:] anchors = np.asarray(meta['anchors'])
        list boxes = list()

    H, W, _ = meta['out_size']
    C = meta['classes']
    B = meta['num']

    cdef:
        float[:, :, :, ::1] net_out = net_out_in.reshape([H, W, B, net_out_in.shape[2]/B])
        float[:, :, :, ::1] classes = net_out[:, :, :, 5:]
        float[:, :, :, ::1] pred =  net_out[:, :, :, :5]
        float[:, :, :, ::1] probs = np.empty((H, W, B, C), dtype=np.float32)

    for i in range(H): # rows
        for j in range(W): # columns
            for k in range(B): # boxes
                m=0
                n=0
                pred[i,j,k,0] = (j + scipy.expit(pred[i,j,k,0])) / W
                pred[i,j,k,1] = (i + scipy.expit(pred[i,j,k,1])) / H
                pred[i,j,k,2] = exp(pred[i,j,k,2]) * anchors[2*k+0] / W
                pred[i,j,k,3] = exp(pred[i,j,k,3]) * anchors[2*k+1] / H
                pred[i,j,k,4] = scipy.expit(pred[i,j,k,4])

                for l in range(C): # classes
                    m = fmax(m, classes[i,j,k,l])
                    for l in range(C): # classes
                        classes[i,j,k,l] = exp(classes[i,j,k,l] - m)
                        n += classes[i,j,k,l]
                        conf = classes[i,j,k,l] * pred[i,j,k,4] / n
                        if conf > thresh:
                            probs[i,j,k,l] = conf
                        else: # only zero
                            probs[i,j,k,l] = 0.0
    #NMS
    if soft:
      return soft_nms(np.ascontiguousarray(probs).reshape(H*W*B, C), np.ascontiguousarray(pred).reshape(H*W*B, 5))
    else:
      return nms(np.ascontiguousarray(probs).reshape(H*W*B, C), np.ascontiguousarray(pred).reshape(H*W*B, 5))

