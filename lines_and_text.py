import glob
from detect_text import detect_text
from lines_extraction import final_lines, distance_between_two_points
from coords_to_dxf import coords_to_dxf
from PIL import Image
import os
import cv2
from time import localtime, strftime, sleep
import gc
import numpy as np
from time import perf_counter
from math import ceil
import re
import datetime
#import openpyxl
from openpyxl import Workbook, load_workbook
import xlrd
import csv
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

def lines_and_text(f, page_name, workbook_name, output_drawing, dxfpath, padding):
    """
    Detects all lines and text in a drawing
    
    Arguments:
        f {str} -- Path to input image
        page_name {str} -- Name of current drawing
        workbook_name {str} -- Name of output Excel file
        output_drawing {str} -- Path to output drawing
        dxfpath {str} -- Path to output AutoCAD DXF file
        padding {(int, int)} -- Amount by which image has been padded in pixels
    
    Raises:
        RuntimeError: Raised if image cannot be written to file
    
    Returns:
        {str:(int, int, int, int, str), str:(int, int, int, int)} -- Dictionary containing lines and text
    """    
    try:
        
        # Load the image in memory
        dh, dw = padding
        print("Running 'lines_and_text' function")
        img = cv2.imread(f)
        op = cv2.imread(output_drawing)
        iter_start = perf_counter()
        height = img.shape[0] - (2*dh)
        t_start = perf_counter()
        print('Starting text detection...')
        #text = detect_text(img_in_memory=True, img=img, img_name=os.path.splitext(fname_clean)[0])
        text = [] #!!!TEMPORARY CHANGE  
        #TODO
        '''
        for x in text:
            print(re.match("\w{2, 5}-\w{2, 5}-\w{2, 5}", x[4]))
        '''   
        
        # PRINT TIMESTAMP
        lap_t = perf_counter()
        diff = lap_t - t_start
        print(int(diff))
        t = str(datetime.timedelta(seconds=int(diff)))
        
        print('Time taken for text detection: ' + t)

        print('Starting line detection...')
        lines_t = final_lines(img_in_memory=True, input_img=img)
        
       
        # Filter lines by line length
        lines = []
        line_excel_row = 2
        totallinedist = 0
        linedist = []
        threshold_line_length = 100
        for l in lines_t:
            p1 = (l[0], l[1])
            p2 = (l[2], l[3])
            linedist.append(int(distance_between_two_points(p1, p2)))
            totallinedist += int(distance_between_two_points(p1, p2))
            if distance_between_two_points(p1, p2) > threshold_line_length:
                cv2.line(op, (l[0], l[1]), (l[2], l[3]), (0, 0, 255), 2)
                line_excel(line_excel_row, (l[0]-dw)*0.084667, (height-(l[1]-dh))*0.084667, (l[2]-dw)*0.084667, (height-(l[3]-dh))*0.084667, page_name, "", workbook_name)
                line_excel_row = line_excel_row + 1
                lines.append(l)

         # PRINT TIMESTAMP
        lap_l = perf_counter()
        diff = lap_l - iter_start
        t = str(datetime.timedelta(seconds=int(diff)))
        print('Time taken for line detection: ' + t)
        if not cv2.imwrite(output_drawing, op):
            raise RuntimeError("Image could not be written to file")

       
        d_start = perf_counter()

        # Place elements in DXF file
        coords_to_dxf(text, lines, 300, height, dxfpath)

        # PRINT TIMESTAMP
        lap_d = perf_counter()
        diff = lap_d - d_start
        t = str(datetime.timedelta(seconds=int(diff)))
        print('Time taken for placing components in a DXF file: ' + t)

        ret = {f:{'lines':lines, 'text':text}}

        del img
        del lines
        del lines_t 
        del text
        gc.collect()

        iter_end = perf_counter()
        diff = iter_end - iter_start
        print(diff)
        t = str(datetime.timedelta(seconds=int(diff)))
        print('Time taken for this file: ' + t)

        return ret
    except:
        error_present = 1
        logging.error(' Error in "lines_and_text" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise

""" This function is used to insert all the piping line related data 
    into the "LINES.xlsx" Excel workbook """
def line_excel(line_excel_row, x1, y1, x2, y2, page_name, linetag, workbook_name):       
    try: 
        
        #logging.info(' Line instance: ' + str(line_excel_row))
        wb = load_workbook(workbook_name)
        dest_filename = workbook_name
        sheet_get= wb.worksheets[0]
        row_no = line_excel_row
        cell_insert = 'A' + str(row_no)
        sheet_get [str(cell_insert)] = x1
        cell_insert = 'B' + str(row_no)
        sheet_get [str(cell_insert)] = y1
        cell_insert = 'C' + str(row_no)
        sheet_get [str(cell_insert)] = x2
        cell_insert = 'D' + str(row_no)
        sheet_get [str(cell_insert)] = y2
        cell_insert = 'E' + str(row_no)
        sheet_get [str(cell_insert)] = linetag
        wb.save(filename = dest_filename)
        csv_from_excel(workbook_name, workbook_name.replace('xlsx','csv'))
    except: 
        #global error_present
        error_present = 1
        logging.error(' Error in "line_excel" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise
    




""" This function is used to create a CSV file out of an Excel workbook """    
def csv_from_excel(excel_file, csv_file):
    try:
        workbook_opened = xlrd.open_workbook(excel_file, encoding_override='utf-8')
        sheet_name = workbook_opened.sheet_by_name('Sheet1')
        csv_file_opened = open(csv_file, 'w', encoding = 'utf8')
        csv_writer = csv.writer(csv_file_opened,delimiter=',',lineterminator='\n', quoting=csv.QUOTE_MINIMAL)

        for rownum in range(sheet_name.nrows):
            csv_writer.writerow(sheet_name.row_values(rownum))

        csv_file_opened.close()
    except:
        #global error_present
        error_present = 1
        logging.error(' Error in "csv_from_excel" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise
        
if __name__ == '__main__':
    f = glob.glob('C:\\Users\\kartik.gokte\\Desktop\\BrewCAD stuff\\testc.jpg')
    for l in f:
        print(process_image_lines_text(l))