from detect_text import detect_text
from imutils.object_detection import non_max_suppression
import numpy as np
from math import ceil
from time import perf_counter
import cv2
import pytesseract
import csv
import os
import shutil
import random
import logging
import sys
import linecache

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    error_message = 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj) 
    return error_message

def detect_text_symbol(img, symbol_list):
    """
    Detects text in a list of symbols.
    
    Arguments:
        img {numpy.ndarray} -- Reference image
        symbol_list {list} -- List of coordinates of the symbols
    
    Returns:
        list -- List of dictionaries containing the coordinates of the symbols and the coordinates of text detected in symbols
    """
    try:
        ret = []
        for l in symbol_list:
            a, b, c, d = l[0].item(), l[1].item(), l[2].item(), l[3].item(),
            print(a)
            print(type(a))

            crop = img[b:d, a:c]
        
            lst = detect_text(img_in_memory=True, img=crop, img_name='temp_symbol')
            lt = []
            for t in lst:
                lt.append([int(t[0]) + l[0], int(t[1]) + l[1], int(t[2]) + l[2], int(t[3]) + l[3], t[4]])
            ret.append({'symbol':l, 'text':lt})

        return ret
    except:
        error_present = 1
        logging.error(' Error in detect_text_symbol function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise

if __name__ == "__main__":
    img = cv2.imread('C:\\Users\\kartik.gokte\\Desktop\\BrewCAD stuff\\Drawings\\Input\\0_082-0268-100-285-01.PDF.jpg')
    print(detect_text_symbol(img, [[1167, 400, 1230, 580]]))