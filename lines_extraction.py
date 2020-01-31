import cv2
import numpy as np
import glob
from pylsd.lsd import lsd
import os
from operator import itemgetter
import itertools
import logging
from time import localtime, strftime
import linecache
import sys
import csv
import math
import statistics
# This defines the maximum distance required for merging two adjacent lines
threshold_merge = 25
# This defines the maximum distance required for merging two parallel lines
threshold_parallel = 10
threshold_line_length = 40   # Minimum Line length


    
'''
The following 4 functions deal with merging adjacent horizontal lines and adjacent vertical lines
            _____________________<--------------->______________      => ____________________________________
                                  threshold_merge
'''


def merge_overlapping_intervals(temp_tuple):
    '''
    This function takes a list of lists as inputs and merges the overlapping intervals and returns the final merged list

    Example:
        input   -->   temp_tuple = [[1,6], [4,8]]
        output  -->   merged= [[1,8]]

    '''
    try:
        temp_tuple.sort(key=lambda interval: interval[0])
        merged = [temp_tuple[0]]
        for current in temp_tuple:
            previous = merged[-1]
            if current[0] <= previous[1]:
                previous[1] = max(previous[1], current[1])
            else:
                merged.append(current)

        return (merged)
    except:
        logging.error(' Error in "merge_overlapping_intervals" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise

def merge(temp):
    '''
    Merges a set of lists based on the threshold
    '''
    try:
        temp = sorted(temp, key=itemgetter(0))
        list_to_remove = []
        merged = []

        for i in range(0, len(temp) - 1):

            diff = abs(temp[i][1] - temp[i + 1][0])

            if (diff < threshold_merge):
                c = [temp[i][0], temp[i + 1][1]]
                list_to_remove.append(temp[i])
                list_to_remove.append(temp[i + 1])
                merged.append(c)

        for i in temp:
            if i not in list_to_remove:
                merged.append(i)
        return merged
    except:
        logging.error(' Error in "merge" function : ' )
        error_message = PrintException()
        logging.error(error_message)
        raise


def merge_adjacent_horizontal_lines(hor):
    '''
    Merges two adjacent horizontal lines which are at a distance  <= threshold_merge
    '''
    try:
        for i in hor:           # making x1 always less than x2. if line = [x1,y1, x2, y2] there might be a chance that x2 < x1. So this condition will ensure that the values are always sorted
            if i[0] > i[2]:
                i[0], i[2] = i[2], i[0]

        # sorting on the basis of y-coordinate
        hor_sorted = sorted(hor, key=itemgetter(1))

        only_y = []         # storing all the y values into a list
        for i in hor_sorted:
            only_y.append(i[1])

        only_y = list(set(only_y))

        d = {}              # forming a dictionary of all the lines. with key value being the y-coordinate and the value being all the lines with the same y value
      
        for i in only_y:
            d.update({i: []})

        for i in hor_sorted:
            if i[1] in only_y:
                c = [i[0], i[2]]
                d[i[1]].append(c)

        '''
        Now for each y-value => lines lying on the same line, we apply merge adjacent lines functions. So we would be considering only those lines which have same y-value and check if we can merge them
        '''
        for i in d:
            temp_tuple = d[i]

            a = merge(temp_tuple)

            if (len(a) > 1):
                merged = merge_overlapping_intervals(a)

                d[i] = merged

            else:
                d[i] = a

        horizontalLines = []            # final list of merged adjacent horizontal lines
        for i in d:
            for j in d[i]:
                c = [j[0], i, j[1], i]
                horizontalLines.append(c)

        return (horizontalLines)
    except:
        logging.error(' Error in "merge_adjacent_horizontal_lines" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise


def merge_adjacent_vertical_lines(ver):
    '''
    Similar to the horizontal lines. Only difference is we would be considering the lines which have the same x-coordinate and check if we can merge them
    '''
    try:
        for i in ver:
            if i[1] > i[3]:
                i[1], i[3] = i[3], i[1]

        ver_sorted = sorted(ver, key=itemgetter(0))

        only_x = []
        for i in ver_sorted:
            only_x.append(i[0])

        only_x = list(set(only_x))

        d = {}
        for i in only_x:
            d.update({i: []})

        for i in ver_sorted:
            if i[0] in only_x:
                c = [i[1], i[3]]
                d[i[0]].append(c)

        for i in d:
            temp_tuple = d[i]

            a = merge(temp_tuple)

            if (len(a) > 1):
                merged = merge_overlapping_intervals(a)

                d[i] = merged

            else:
                d[i] = a

        verticalLines = []
        for i in d:
            for j in d[i]:
                c = [i, j[0], i, j[1]]
                verticalLines.append(c)

        return (verticalLines)
    except:
        logging.error(' Error in "merge_adjacent_vertical_lines" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise


'''
The following functions deal with merging parallel lines.
In total, 6 cases are possible each while dealing with parallel horizontal and parallel vertical lines

    ___________             |               ____________      |                 _______              |       __________________       |                    _________        |          ________                 |
    ___________________     |            ________________     |          ______________________      |           ________             |   ______________                    |                       _________   |


    We would be merging the parallel lines which contain atleast some area in common. So in our case, the first 4 cases are valid for merging parallel lines.
'''


def check_limits_horizontal(line1, line2):
    '''
    This checks if the lines contain common area. It returns false if they contain common area

    So here we check two lines are satisfying the last two cases mentioned above, if it is satisfying => we can't merge them

            a______b
        c_____________d

        We check if two coordinates are outside the limits of the two coordinates of the other lines

        bool1 -> case 6
        bool2 -> case 5

    '''
    try:
        a, b = (line1[0], line1[2])
        c, d = (line2[0], line2[2])

        bool1 = (a < b < c) and (a < b < d)
        bool2 = (c < a < b) and (d < a < b)

        return (bool1 or bool2)
    except:
        logging.error(' Error in "check_limits_horizontal" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise


def merge_parallel_horizontal_lines(hor):
    '''
    for merging parallel lines, we take the midpoint of the two lines if difference is > 1 pixel.
    if difference is 1 pixel, we would take the first line because we can't take the midpoint
    '''
    try:
        hor_sorted = sorted(hor, key=itemgetter(0))
        list_to_remove = []
        #threshold_parallel = 10

        merged_parallel_lines = []
        for a,b in itertools.combinations(hor_sorted,2):

            if ((abs(b[1] - a[1]) == 1)  and check_limits_horizontal(a, b) == False):  # if difference is 1
                    
                # consider the first line as the merged line
                merged_parallel_lines.append(a)
                list_to_remove.append(a)
                list_to_remove.append(b)

            elif ((abs(b[1] - a[1]) > 1) and (abs(b[1] - a[1]) <= threshold_parallel) and check_limits_horizontal(a, b) == False):  # if difference > 1

                x1 = min(a[0], b[0])
                y1 = y2 = (a[1] + b[1]) // 2
                x2 = max(a[2], b[2])

                # take the line going through the midpoint of two y coordinates
                merged_parallel_lines.append([x1, y1, x2, y2])

                list_to_remove.append(a)
                list_to_remove.append(b)

        for i in hor_sorted:
            if i not in list_to_remove:
                merged_parallel_lines.append(i)

        return merged_parallel_lines
    except:
        logging.error(' Error in "merge_parallel_horizontal_lines" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise


# Similar operations of merging parallel horizontal lines

def check_limits_vertical(line1, line2):
    try:
        a, b = (line1[1], line1[3])
        c, d = (line2[1], line2[3])

        bool1 = (a < b < c) and (a < b < d)
        bool2 = (c < a < b) and (d < a < b)

        return (bool1 or bool2)
    except:
        logging.error(' Error in "check_limits_vertical" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise


def merge_parallel_vertical_lines(ver):
    try:
        ver_sorted = sorted(ver, key=itemgetter(1))

        #threshold_parallel = 10
        list_to_remove = []
        merged_parallel_lines = []
        for a,b in itertools.combinations(ver_sorted,2):

            if ((abs(b[0] - a[0]) == 1) and check_limits_vertical(a, b) == False):
                                            

                merged_parallel_lines.append(a)
                list_to_remove.append(a)
                list_to_remove.append(b)

            elif ((abs(b[0] - a[0]) > 1) and (abs(b[0] - a[0]) <= threshold_parallel) and check_limits_vertical(a, b) == False):

                y1 = min(a[1], b[1])
                x1 = x2 = (a[0] + b[0]) // 2
                y2 = max(a[3], b[3])

                merged_parallel_lines.append([x1, y1, x2, y2])

                list_to_remove.append(a)
                list_to_remove.append(b)

        for i in ver_sorted:
            if i not in list_to_remove:
                merged_parallel_lines.append(i)
        return merged_parallel_lines
    except:
        logging.error(' Error in "merge_parallel_vertical_lines" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise


def horizontal_operation(horizontalLines):
    try:
        # This function calls the two functions for merging adjacent and merging
        # parallel lines into a single function
        horizontal_merged_adjacently = merge_adjacent_horizontal_lines(horizontalLines)
            
        HORIZONTAL = merge_parallel_horizontal_lines(horizontal_merged_adjacently)

        return HORIZONTAL
    except:
        logging.error(' Error in "horizontal_operation" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise


def horizontal_lines_main(horizontalLines):
    try:
        # we call merge adjacent and parallel lines repeatedly till we get a
        # single line from a set of parallel lines (in cases of having more than 2
        # parallel lines satistying the thresold condition)
        hor = horizontal_operation(horizontalLines)
        if hor == horizontalLines:
            return horizontalLines
        else:
            return horizontal_lines_main(hor)
    except:
        logging.error(' Error in "horizontal_lines_main" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise

def vertical_operation(verticalLines):
    try:

        vertical_merged_adjacently = merge_adjacent_vertical_lines(verticalLines)

        VERTICAL = merge_parallel_vertical_lines(vertical_merged_adjacently)

        return VERTICAL
    except:
        logging.error(' Error in "vertical_operation" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise


def vertical_lines_main(verticalLines):
    try:
        ver = vertical_operation(verticalLines)
        if ver == verticalLines:
            return verticalLines
        else:
            return vertical_lines_main(ver)
    except:
        logging.error(' Error in "vertical_lines_main" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise

        

def get_slant_line_length(line):
    return math.sqrt( (line[2] - line[0])**2 + (line[3] - line[1])**2 )

    
'''
This function takes the middle lines between two parallel slant lines
'''


def get_distance_between_two_parallel_lines(a,b):
    m = get_slope(a)
    b1 = a[1]- (m* a[0])
    b2 = b[1]- (m* b[0])

    d = abs(b2-b1)/ math.sqrt((m*m) + 1)

    return (d)


def check_limits_slant_x(line1, line2):
    '''
    This checks if the lines contain common area. It returns false if they contain common area

    So here we check two lines are satisfying the last two cases mentioned above, if it is satisfying => we can't merge them

            a______b
        c_____________d

        We check if two coordinates are outside the limits of the two coordinates of the other lines

        bool1 -> case 6
        bool2 -> case 5

    '''
    a, b = (line1[0], line1[2])
    c, d = (line2[0], line2[2])

    bool1 = (a < b < c) and (a < b < d)
    bool2 = (c < a < b) and (d < a < b)

    return (bool1 or bool2)


def check_limits_slant_y(line1, line2):
    a, b = (line1[1], line1[3])
    c, d = (line2[1], line2[3])

    bool1 = (a < b < c) and (a < b < d)
    bool2 = (c < a < b) and (d < a < b)

    return (bool1 or bool2)


def distance_between_two_points(x1,x2):
    return math.sqrt( (x2[0] - x1[0])**2 + (x2[1]-x1[1])**2 )


def get_slant_line_length(line):
    return math.sqrt( (line[2] - line[0])**2 + (line[3] - line[1])**2 )


def get_slope(line):
    return (( ((line[3]- line[1])/ (line[2]-line[0]))))   


def get_angle(line):
    slope = (line[1]- line[3])/ (line[2]-line[0])
    return int(math.degrees(math.atan(slope)))


def merge_parallel_slant_lines(slant):
    '''
    for merging parallel lines, we take the midpoint of the two lines if difference is > 1 pixel.
    if difference is 1 pixel, we would take the first line because we can't take the midpoint
    '''

    for line in slant:
        if line[0] > line[2]:
            line[0],line[2] = line[2], line[0]
            line[1], line[3] = line[3], line[1]
    slant_sorted = sorted(slant, key=itemgetter(0))
    list_to_remove = []


    merged_parallel_lines = []
    long_lines= []
    for line in slant_sorted:
        if get_slant_line_length(line) >= threshold_line_length:
            long_lines.append(line)

    for a,b in itertools.combinations(long_lines,2):
        if abs(get_angle(a)- get_angle(b)) <= 1 and check_limits_slant_x (a,b) == False and check_limits_slant_y(a,b)== False :
            m = get_slope(a)
            c1 = a[1]- (m* a[0])
            c2 = b[1]- (m* b[0])
            if get_distance_between_two_parallel_lines(a,b)<= threshold_parallel:
                c = (c1+c2)//2

                x1 = int (min(a[0], b[0], a[2], b[2]))
                x2 = int (max(a[0], b[0], a[2], b[2]))
                y1 = int((m*x1)+ c)
                y2 = int((m*x2)+ c )

                merged_parallel_lines.append([x1,y1,x2,y2])

    return merged_parallel_lines

    
    
def remove_duplicates(array):
    try:
        resultant_array= []
        for i in array:
            if i not in resultant_array:
                resultant_array.append(i)

        return resultant_array
    except:
        logging.error(' Error in "remove_duplicates" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise


def final_lines(input_drawing=None, img_in_memory=False, input_img=None):
    try:
        if not img_in_memory:
            image = cv2.imread(input_drawing, cv2.IMREAD_COLOR)
        else:
            if type(input_img) is not np.ndarray:
                raise TypeError
            image = input_img
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        lines = []
        lines_list = lsd(gray)
        for line in lines_list:
            lines.append([int(line[0]), int(line[1]), int(line[2]), int(line[3])])
        horizontalLines = []
        verticalLines = []
        points = []
        others = []
        for line in lines:
            # considering the lines which are a bit slant and making them straight
            if abs(line[1] - line[3]) <= 1 and abs(line[2] - line[0]) > 1:
                line[1] = line[3]
                horizontalLines.append(line)

            elif abs(line[0] - line[2]) <= 1 and abs(line[3] - line[1]) >1 :
                line[0] = line[2]
                verticalLines.append(line)

            else:
                others.append(line)

        horizontal_lines = horizontal_lines_main(horizontalLines)
        vertical_lines = vertical_lines_main(verticalLines)
        slant_lines = merge_parallel_slant_lines(others)

        # removing duplicates (if any)
        HORIZONTAL = remove_duplicates(horizontal_lines)
        VERTICAL = remove_duplicates(vertical_lines)
        SLANT = remove_duplicates(slant_lines)

        LINES = VERTICAL + HORIZONTAL + SLANT  # Final merged lines
        #return LINES
        logging.debug("\n after merging: " + str(len(LINES)))
        #assert 2 < 1
        #print(LINES)
        
        '''
       if not img_in_memory:
            filename = os.path.splitext(os.path.basename(input_drawing))[0]
        else:
            filename = os.path.splitext(filename)[0]

        working_dir = os.path.abspath(os.path.dirname(__file__))
        dir = os.path.join(working_dir, 'output')
        dir = os.path.join(dir, 'out_' + filename)
        if not os.path.exists(dir):
            os.mkdir(dir)
        
        
        csv_filename = os.path.join(dir, 'lines_' + filename + '.csv')
        if not os.path.exists(csv_filename):
            f = open(csv_filename, 'a')
        else:
            f = open(csv_filename, 'w')
        data = csv.writer(f)
        data.writerow(['X1', 'Y1', 'X2', 'Y2'])
        for l in LINES:
            data.writerow(l)
        f.close()
        '''
        return LINES

    except:
        logging.error(' Error in "final_lines" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    error_message = 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj) 
    return error_message

if __name__ == "__main__":
    linesf = final_lines("C:\\Users\\kartik.gokte\\Desktop\\BrewCAD stuff\\Drawings\\Input\\0_082-0267-120-054-01.pdf.jpg")
    lines = []
    for l in linesf:
        if distance_between_two_points((l[0], l[1]), (l[2], l[3])) >= threshold_line_length:
            lines.append(l)
    f = open('out.csv', 'w')
    data = csv.writer(f)
    data.writerow(['X1', 'Y1', 'X2', 'Y2'])
    for l in lines:
        data.writerow(l)
