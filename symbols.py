import glob
import os
import cv2
import shutil
from shutil import copyfile
#from pdf2jpg import pdf2jpg_comments as pdf2jpg
import numpy as np
from numpy import array
import xlsxwriter
#import openpyxl
from openpyxl import Workbook, load_workbook
import pytesseract
from imutils.object_detection import non_max_suppression
import time
from time import localtime, strftime, sleep
import tkinter as tk
from tkinter import Tk,ttk,filedialog
from PIL import Image, ImageTk
from PyPDF2 import PdfFileReader
import math
from math import floor
#from lines_after import *
import ezdxf
#from linetag import *
import logging
#import io
import xlrd
import csv
import System_details as sd
import datetime
from symbol_text_wrapper import detect_text_symbol
from lines_and_text import lines_and_text, csv_from_excel
import sys
import linecache


"""This function is used to remove overlapping boxes during template matching
   The parameters passed are the co-ordinates of the boxes and the critical overlap area. """ 
def non_max_suppression_fast(boxes, overlapThresh):
    try:
        # if there are no boxes, return an empty list
        if len(boxes) == 0:
            return []
 
        # if the bounding boxes integers, convert them to floats --
        # this is important since we'll be doing a bunch of divisions
        if boxes.dtype.kind == "i":
            boxes = boxes.astype("float")
 
        # initialize the list of picked indexes    
        pick = []
 
        # grab the coordinates of the bounding boxes
        x1 = boxes[:,0]
        y1 = boxes[:,1]
        x2 = boxes[:,2]
        y2 = boxes[:,3]
 
        # compute the area of the bounding boxes and sort the bounding
        # boxes by the bottom-right y-coordinate of the bounding box
        area = (x2 - x1 + 1) * (y2 - y1 + 1)
        idxs = np.argsort(y2)
 
        # keep looping while some indexes still remain in the indexes
        # list
        while len(idxs) > 0:
            # grab the last index in the indexes list and add the
            # index value to the list of picked indexes
            last = len(idxs) - 1
            i = idxs[last]
            pick.append(i)
 
            # find the largest (x, y) coordinates for the start of
            # the bounding box and the smallest (x, y) coordinates
            # for the end of the bounding box
            xx1 = np.maximum(x1[i], x1[idxs[:last]])
            yy1 = np.maximum(y1[i], y1[idxs[:last]])
            xx2 = np.minimum(x2[i], x2[idxs[:last]])
            yy2 = np.minimum(y2[i], y2[idxs[:last]])
 
            # compute the width and height of the bounding box
            w = np.maximum(0, xx2 - xx1 + 1)
            h = np.maximum(0, yy2 - yy1 + 1)
 
            # compute the ratio of overlap
            overlap = (w * h) / area[idxs[:last]]
 
            # delete all indexes from the index list that have
            idxs = np.delete(idxs, np.concatenate(([last],
                np.where(overlap > overlapThresh)[0])))
 
        # return only the bounding boxes that were picked using the
        # integer data type
        return boxes[pick].astype("int")
    except:
        error_present = 1
        logging.error(' Error in "non_max_suppression_fast" function : ')
        
        raise
    

""" This function is used to perform template matching to locate the instruments in the drawing
    and highlighting the instruments in the output drawing """    
def getboxes(output_drawing, specific_template, file, template_name, threshold, workbook_instrument, instrument_excel_row, template_instance, dwg, modelspace, tested_blocks, padding):
    try:
        dh, dw = padding
        try:
            rotation = int(specific_template.lower().split("\\")[-1].strip(".jpg"))
        except:
            print("Symbol filename invalid")
            logging.critical("Symbol filename invalid, skipping")
            return
        #current_working_directory = os.getcwd()
        #global template_instance
        #global instrument_excel_row
        #global dwg
        #global modelspace
        #Template matching
        logging.info(' Performing template matching of ' + template_name + ' on ' + output_drawing)
        print(' Performing template matching of ' + template_name)
        """ Creating a copy of the dxf block of the template so that it can be placed in the final dxf drawing """
        #print(current_working_directory + "\\" + 'blocks\\' + template_name + '.dxf')
        '''if (file + str(rotation)) not in tested_blocks:
            dwgBlock, mspBlock = readDXF(current_working_directory + "\\" + 'Pankaj_blocks\\' + template_name + '.dxf')
            #print(dwgBlock, mspBlock)
            block = dwg.blocks.new(name=file + str(rotation))
            for insert in mspBlock.query():
                analyse_element(insert, block, dwgBlock)
        '''    
        #block = dwg.blocks.new(name=template_name + "1")
        
        img_original_drawing = cv2.imread(output_drawing)
        img_rgb = cv2.imread("cropc.jpg")
        img_height = img_rgb.shape[0]
        #logging.debug("SYMBOL IMAGE HEIGHT : " + str(img_height))
        #
        #img_width = img_rgb.shape[1]
        #logging.debug("SYMBOL IMAGE WIDTH : " + str(img_width))
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        template = cv2.imread(specific_template,0)
        w, h = template.shape[::-1]
        res = cv2.matchTemplate(img_gray,template,cv2.TM_CCOEFF_NORMED)
        loc = np.where( res >= threshold)
        boxes = []
        #Getting required templates
        for pt in zip(*loc[::-1]):
            box = [pt[0], pt[1], pt[0] + w, pt[1] + h]
            boxes.append(box)
        arr = array(boxes)
        boxes_new = non_max_suppression_fast(arr, 0.4)
        #Highlighting the detected instrument and performing East Text Extraction on it
        for box in boxes_new:
            symbol_text = ""
            box_in_a_list = [box]
            for element_of_box in detect_text_symbol(img_original_drawing, box_in_a_list):
                for element_of_text in element_of_box["text"]:
                    symbol_text = symbol_text + " " + element_of_text[4]
            img = cv2.imread(output_drawing)
            img1 = cv2.imread("cropc.jpg")
            x_coord = int((box[0] + box[2])/2)
            y_coord = int((box[1] + box[3])/2)
            #logging.info(' Template instance: ' + str(template_instance))
            template_instance = template_instance + 1
            crop_img = img[box[1]:box[3], box[0]:box[2]]
            cv2.imwrite("cropa.jpg", crop_img)
            #East_detection("cropa.jpg", file, template_name, x_coord, y_coord, workbook_instrument)
            instrument_excel(symbol_text, file, template_name, (x_coord-dw)*0.084667, (img_height-(y_coord-dh))*0.084667, workbook_instrument, instrument_excel_row, rotation)
            #Placing the instrument in the CAD drawing
            #scale = 1
            #modelspace.add_blockref(file + str(rotation), (x_coord, img_height - y_coord), {'xscale': scale, 'yscale': scale, 'rotation': float(rotation)})            
            cv2.rectangle(img_original_drawing, (box[0],box[1]), (box[2], box[3]), (0,128,0), 4)
            cv2.imwrite(output_drawing,img_original_drawing)
            for i in range(box[0],box[2] + 1): 
                for j in range(box[1], box[3] + 1):
                    if img1[j,i][0] != 255 or img1[j,i][1] != 255 or img1[j,i][2] != 255: 
                        img1[j,i] = np.array([255, 255, 255])
            cv2.imwrite("cropc.jpg",img1)
            instrument_excel_row = instrument_excel_row + 1
        tested_blocks.append(file + str(rotation))
        return instrument_excel_row, template_instance
        #print(detect_text_symbol(img_original_drawing, boxes_new))
        
    except:
        #global error_present
        error_present = 1
        logging.error(' Error in "getboxes" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise


def analyse_element(e, block, dwgBlock):
    try:
        #print(e.dxftype)
        if e.dxftype() == 'LINE':
            block.add_line(e.dxf.start, e.dxf.end, dxfattribs = {'color':2})
        elif e.dxftype() == 'ARC':
            block.add_arc(e.dxf.center, e.dxf.radius, e.dxf.start_angle, e.dxf.end_angle, dxfattribs = {'color':2})
        elif e.dxftype() == 'CIRCLE':
            block.add_circle(e.dxf.center, e.dxf.radius, dxfattribs = {'color':2})
        elif e.dxftype() == "POLYLINE":
            lw_list = []
            for i in e.points():
                lw_point = list(i)
                lw_list.append(lw_point)
            block.add_polyline2d(lw_list, dxfattribs = {'color':2})
        elif e.dxftype() == 'LWPOLYLINE':
            lw_list = []
            for i in e.vertices():
                lw_point = list(i)
                lw_list.append(lw_point)
            block.add_lwpolyline(lw_list, dxfattribs = {'color':2})
        elif e.dxftype() == 'ELLIPSE':
            block.add_ellipse(e.dxf.center, e.dxf.major_axis, e.dxf.major_axis, dxfattribs = {'color':2})
        elif e.dxftype() == 'INSERT':
            block_unknown = dwgBlock.blocks[e.dxf.name]
            for new_element in block_unknown:
                analyse_element(new_element, block, dwgBlock)
    except:
        error_present = 1
        logging.error(' Error in "analyse_element" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise    



""" This function read the DXF file and returns the dwg and msp """
def readDXF(file):

    drawing_dwg=ezdxf.readfile(file)
    modelspace_msp=drawing_dwg.modelspace()
    return drawing_dwg, modelspace_msp
    
    
""" This function is used to insert all the instrument related data 
    into the "INSTRUMENTS.xlsx" Excel workbook """        
def instrument_excel(text, file, temp, x_coord, y_coord, workbook_instrument, instrument_excel_row, rotation):    
    try:  
        wb = load_workbook(workbook_instrument)
        dest_filename = workbook_instrument
        sheet_get= wb.worksheets[0]
        #global instrument_excel_row
        row_num = instrument_excel_row
        cell_insert = 'A' + str(row_num)
        sheet_get [str(cell_insert)] = file
        cell_insert = 'B' + str(row_num)
        sheet_get [str(cell_insert)] = temp
        cell_insert = 'C' + str(row_num)
        sheet_get [str(cell_insert)] = x_coord
        cell_insert = 'D' + str(row_num)
        sheet_get [str(cell_insert)] = y_coord
        cell_insert = 'E' + str(row_num)
        sheet_get [str(cell_insert)] = text
        cell_insert = 'F' + str(row_num)
        sheet_get [str(cell_insert)] = rotation
        wb.save(filename = dest_filename)
        csv_from_excel(workbook_instrument, workbook_instrument.replace('xlsx','csv'))
    except:
        #global error_present
        error_present = 1
        logging.error(' Error in "instrument_excel" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise





