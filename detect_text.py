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
import re
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

#!!!COMPILE THIS WITH -O ARGUMENT TO REMOVE ALL DEBUGING FEATURES!!!#
# Average memory usage on 3100x5200 image: 4GB
# Before running, close most programs otherwise the computer RAM usage MIGHT TOUCH 100%, causing it to brick.
def detect_text(image_path=None, img_in_memory=False, img=None, img_name=None):
    """
    Detects and extracts text from images.

    This function uses EAST detection and PyTesseract to extract lines 
    of text from a drawing or picture. The output folder includes the original
    image with the regions of detected text highlighted on it, an image 
    with only the highlighted regions of text, and a CSV file containing the
    coordinates of the region of text found, and the text extracted from that region.

    Format of CSV:
    (Top left X coordinate, Top left Y coordinate, Bottom right X coordinate,
    Bottom right Y coordinate, Text in the region)
    
    Keyword Arguments:
        image_path {str} -- Path to the specified image in the system (default: {None})
        img_in_memory {bool} -- If True, image_path will be ignored and img will be used as the image (default: {False})
        img {np.ndarray} -- numpy representation of the input image (default: {None})
        img_name {str} -- Original filename of the numpy image (default: {None})
    
    Raises:
        TypeError: Raised if img is not a numpy ndarray
    
    Returns:
        [(int, int, int, int, str)] -- X1, Y1, X2, Y2, Text
    """    

    try:
        # Figure out current working directory        
        working_dir = os.path.abspath(os.path.dirname(__file__))
        tessdir = os.path.join(working_dir, 'Tesseract-OCR\\tesseract.exe')
        pytesseract.pytesseract.tesseract_cmd = tessdir
        
        const_EAST_SIZE_FACTOR = 32
        const_SCALE = 1.0
        const_EAST_BOX_THRESHOLD = 0.3
        const_EAST_SCALE_FACTOR = 4.0
        const_BOUNDING_BOX_PADDING = 5
        const_GREEN = (0, 255, 0)
        # Start the timer
        start = perf_counter()
        # Configure the logging module
        
        #if image path is not provided, provide a default filename
        if img_in_memory:
            logging.debug('Image passed into function in numpy form.')
        else:
            logging.debug('Image path passed into function.')
        # Figure out pretrained model location
        netpath = os.path.join(working_dir, 'lib')
        netpath = os.path.join(netpath, 'frozen_east_text_detection.pb')
        
        working_dir = os.path.join(working_dir, 'output') 
        try:
            if not os.path.exists(working_dir):
                os.mkdir(working_dir)
            if not img_in_memory:
                filename_temp = os.path.splitext(os.path.basename(image_path))[0]
            else:
                filename_temp = 'out_' + img_name
            logging.debug(filename_temp)
            working_dir = os.path.join(working_dir, filename_temp)
            if not os.path.exists(working_dir):
                os.mkdir(working_dir)
        except:
            logging.error("Error making working directory. Please try again.")
            raise
        
        if not img_in_memory:
            filename_temp = os.path.splitext(os.path.basename(image_path))[0]
        else:
            filename_temp = img_name

        # Load image into memory
        try:
            if not img_in_memory:
                img = cv2.imread(image_path)
            if type(img) is not np.ndarray:
                raise TypeError
            logging.info('Image loaded into memory...')
        except:
            logging.error('Error loading image into memory.')
            raise

        # Construct output filenames using original image filename
        filename_csv = 'boxes_' + filename_temp + '.csv'
        filename_jpg = 'output_' + filename_temp + '.jpg'
        filename_th = 'th_' + filename_temp + '.jpg'
        filename_csv = os.path.join(working_dir, filename_csv)
        filename_jpg = os.path.join(working_dir, filename_jpg)
        filename_th = os.path.join(working_dir, filename_th)

        # Figure out directory where segmented images will be placed
        # !!!DEBUG ONLY!!!
        segfile = os.path.join(working_dir, '(debug) segmented images')

        # Make segmented output directory
        # !!!DEBUG ONLY!!!
        if __debug__:
            if os.path.exists(segfile):
                shutil.rmtree(segfile)
            os.mkdir(segfile)
            if os.path.exists(segfile):
                logging.debug('Segmentation directory successfully created...')
            
            # This variable will be used in naming the segmented images in order
            cnt = 1

        # Find the closest multiples of 32 to the image dimensions
        # EAST requires images to be multiples of 32
        logging.debug('Size of image: ' +  str(img.shape))
        (h, w) = img.shape[:2]
        #(ht, wd) = (h, w)
        #print(h, w)
        newh = ceil(img.shape[0]/const_EAST_SIZE_FACTOR) * const_EAST_SIZE_FACTOR
        neww = ceil(img.shape[1]/const_EAST_SIZE_FACTOR) * const_EAST_SIZE_FACTOR
        #print(newh, neww)
        logging.debug('Closest multiples of 32 to the image dimensions: ' + str((newh, neww)))
        
        # Find the amount to crop the image by on both sides
        dh = int((newh - h)/2)
        dw = int((neww - w)/2)
        
        # Pad the image, store the new dimensions
        img = cv2.copyMakeBorder(img, dh, dh, dw, dw, cv2.BORDER_CONSTANT, value=[0, 0, 0])

        (h, w) = img.shape[:2]
        #(ht, wd) = (h, w)
        
        # Fresh image copy to be used during segmentation
        ref = img.copy()
        
        
        logging.debug('Image has been cropped to the nearest multiple of 32')

        # Relevant layers of the EAST neural network to be used for text detection
        layer_names = [
        "feature_fusion/Conv_7/Sigmoid",
        "feature_fusion/concat_3"]

        logging.debug('Loading EAST detector...')
        logging.warning('Memory usage will significantly increase during this step!')
        # Calculate average of all 3 colors in the image
        b = np.average(img[:, :, 0])
        g = np.average(img[:, :, 1])
        r = np.average(img[:, :, 2])

        logging.debug('Average value of 3 color channels: ' + str((r, g, b)))

        # Load pretrained model
        net = cv2.dnn.readNet(netpath)
        
        # Create blob out of image using mean subtraction
        blob = cv2.dnn.blobFromImage(img, const_SCALE, (w, h), (r, g, b), swapRB=True, crop=False)
        #print(len(blob))
        net.setInput(blob)

        # Extract output geometry from the pretrained model
        (scores, geometry) = net.forward(layer_names)
        #print ("geometry: ", geometry)
        #print ("scores: ", scores)
        (numRows, numCols) = scores.shape[2:4]
        rects = []
        confidences = []
        for y in range(0, numRows):
            scoresData = scores[0, 0, y]
            
            xData0 = geometry[0, 0, y]
            xData1 = geometry[0, 1, y]
            xData2 = geometry[0, 2, y]
            xData3 = geometry[0, 3, y]
            anglesData = geometry[0, 4, y]
            for x in range(0, numCols):
                # if our score does not have sufficient probability, ignore it
                if scoresData[x] < const_EAST_BOX_THRESHOLD:
                    continue
                # compute the offset factor as our resulting feature maps will
                # be 4x smaller than the input image
                (offsetX, offsetY) = (x * const_EAST_SCALE_FACTOR, y * const_EAST_SCALE_FACTOR)

                # extract the rotation angle for the prediction and then
                # compute the sin and cosine
                angle = anglesData[x]
                cos = np.cos(angle)
                sin = np.sin(angle)

                # use the geometry volume to derive the width and height of
                # the bounding box
                h = xData0[x] + xData2[x]
                w = xData1[x] + xData3[x]
        
                # compute both the starting and ending (x, y)-coordinates for
                # the text prediction bounding box
                endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
                endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
                startX = int(endX - w)
                startY = int(endY - h)
        
                # add the bounding box coordinates and probability score to
                # our respective lists
                rects.append((startX, startY, endX, endY))
                confidences.append(scoresData[x])
        
        # Get bounding boxes from rects and perform non-max suppression on it
        # to eliminate overlapping boxes
        boxes_orig = non_max_suppression(np.array(rects), probs=confidences)
        logging.info('EAST detection finished...')

        if len(boxes_orig) == 0:
            logging.error("No text found in image.")
            return []
        # Create blank image to draw the bounding boxes on
        th = np.zeros(img.shape)

        # Create output csv file, if it doesn't exist then create it
        try:
            if not os.path.isfile(filename_csv):
                c = open(filename_csv, 'a')
            else:
                c = open(filename_csv, 'w')
        except:
            logging.error("Error creating csv file.")
            raise
        # Pass file handle to the csv writer library
        w = csv.writer(c)
        
        # Merge adjacent boxes into one
        boxes = merge_boxes(boxes_orig.tolist())

        logging.debug('Number of boxes detected: ' + str(len(boxes)))

        logging.info("Segregating text and performing OCR...")
        
        # Write top row in csv file
        w.writerow(('Top left X', 'Top left Y', 'Bottom right X', 'Bottom right Y', 'Text'))
        
        
        # Loop over the bounding boxes

        ret = []
        for lst in boxes:
            startX = lst[0]
            startY = lst[1]
            endX = lst[2]
            endY = lst[3]
            
            # Pad all sides of the box by 5px
            if startX-const_BOUNDING_BOX_PADDING < 0:
                startX = 0
            else:
                startX = startX - const_BOUNDING_BOX_PADDING
            if startY-const_BOUNDING_BOX_PADDING < 0:
                startY = 0
            else:
                startY = startY - const_BOUNDING_BOX_PADDING
            if endX+const_BOUNDING_BOX_PADDING >= neww:
                endX = neww-1
            else:
                endX = endX + const_BOUNDING_BOX_PADDING
            if endY+const_BOUNDING_BOX_PADDING > newh:
                endY = newh-1
            else:
                endY = endY + const_BOUNDING_BOX_PADDING
            
            # Get segmented text region
            tmp = ref[startY:endY, startX:endX]
        
            # Run Tesseract OCR on the region and extract a string of text
            config = ("-l eng --oem 1 --psm 13 -c tessedit_char_whitelist= ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
            text = pytesseract.image_to_string(tmp, config=config)
            
            text = re.sub('-*—-*', '-', text)
            text = re.sub('[^a-zA-Z0-9\-\"\'./,\n\s]', '', text)
            
            # Prepare row to write in the csv file
            row = [startX, startY, endX, endY, text]
            ret.append(row)

            # Write the row in the csv file
            w.writerow(row)

            # Save region of text and the text detected in the segmentation file
            # !!!DEBUG ONLY!!!
            if __debug__:
                path_img = '\\seg{0}.jpg'.format(cnt)
                path_txt = '\\seg{0}.txt'.format(cnt)
                path_img = segfile + path_img
                path_txt = segfile + path_txt
                cnt += 1
                cv2.imwrite(path_img, tmp)
                f = open(path_txt, 'a')
                f.write(str(row))
                f.close()
            
            # Use green color rectangle if not in debug mode
            color = const_GREEN

            # If using debug mode, randomize the color of the rectangle drawn
            # for extra readability
            # !!!DEBUG ONLY!!!
            if __debug__:
                idx = random.randint(0, 6)
                r = idx % 2
                idx = idx // 2
                g = idx % 2
                idx = idx // 2
                b = idx % 2
                cl = [0, 0, 0]
                if r:
                    cl[0] = 255
                if g:
                    cl[1] = 255
                if b:
                    cl[2] = 255
                color = (cl[0], cl[1], cl[2])

            # Draw the bounding box on:
            # The original image
            cv2.rectangle(img, (startX, startY), (endX, endY), color, 2)
            # The blank image
            cv2.rectangle(th, (startX, startY), (endX, endY), color, 2)
            

        logging.info("Text segmentation and OCR completed...")
        logging.info("Writing images to file...")
        # Close csv file
        c.close()
        
        try:
            # Write the original image with bounding boxes to file
            cv2.imwrite(filename_jpg, img)
            # Write the blank file with bounding boxes to file
            cv2.imwrite(filename_th, th)
        except:
            logging.error("Error writing images to file.")
            raise
        # End the timer
        end = perf_counter()

        # Calculate time elapsed and convert it to mm:ss format
        time = end - start
        t = '{0:0>2d}:{1:0>2d}'.format(int(time//60), int(time%60))
        logging.info('Time elapsed: ' + t)
        return ret

    except:
        error_present = 1
        logging.error('Error in "detect_text" function : ')
        error_message = PrintException()
        logging.error(error_message)
        raise

def return_first(elem):
    '''
    Auxiliary function for use in Python's sort function
    '''
    return elem[0]



def return_coords(elem):
    """
    Returns a dictionary containing all critical elements of the input rectangle.
    
    Arguments:
        elem {[(int, int, int, int)]} -- Coordinates describing a bounding box
    
    Returns:
        {str:(int, int)} - A dictionary containing midpoints, corners and the center of a rectangle
    """    
   
    ret = {}
    ret['topleft'] = (elem[0], elem[1])
    ret['topright'] = (elem[2], elem[1])
    ret['bottomleft'] = (elem[0], elem[3])
    ret['bottomright'] = (elem[2], elem[3])
    ret['leftwall'] = (int((ret['topleft'][0] + ret['bottomleft'][0]) / 2), int((ret['topleft'][1] + ret['bottomleft'][1]) / 2))
    ret['rightwall'] = (int((ret['topright'][0] + ret['bottomright'][0]) / 2), int((ret['topright'][1] + ret['bottomright'][1]) / 2))
    ret['topwall'] = (int((ret['topleft'][0] + ret['topright'][0])/2), int((ret['topleft'][1] + ret['topright'][1])/2))
    ret['bottomwall'] = (int((ret['bottomleft'][0] + ret['bottomright'][0])/2), int((ret['bottomleft'][1] + ret['bottomright'][1])/2))
    ret['center'] = (int((ret['topwall'][0] + ret['bottomwall'][0]) / 2), int((ret['topwall'][1] + ret['bottomwall'][1]) / 2))
    return ret

def merge_boxes(boxes):
    """
    Merges bounding boxes near each other
    
    Arguments:
        boxes {[(int, int, int, int)]} -- A list of tuples containing coordinates of the rectangles to be merged.
    
    Returns:
        [(int, int, int, int)] -- A list of tuples containing coordinates of the merged boxes
    """    
   
    const_HORIZONTAL_THRESHOLD = 60
    const_VERTICAL_THRESHOLD = 10
    logging.debug('Merging boxes...')

    # Sort the boxes by top left X coordinate
    boxes.sort(key=return_first)

    # List of booleans used to determine if box has been merged or not
    touched = []
    sz = len(boxes)
    for i in range(sz):
        touched.append(False)
    
    ret = []
    for i in range(sz):
        if not touched[i]:
            # if this box has not been touched, then this box will be the starting point
            # for a new box
            touched[i] = True
            top_left_x = boxes[i][0]
            top_left_y = boxes[i][1]
            bottom_right_x = boxes[i][2]
            bottom_right_y = boxes[i][3]
            for j in range(i+1, sz):
                # Iterate through all boxes ahead
                coord1 = return_coords((top_left_x, top_left_y, bottom_right_x, bottom_right_y))
                coord2 = return_coords(boxes[j])
                # If the 2 boxes are less than 60px apart horizontally
                # and less than 5px vertically then set the rightmost 
                # coordinate of the original box to the current box
                if (abs(coord1['rightwall'][0] - coord2['leftwall'][0]) <= const_HORIZONTAL_THRESHOLD) and (abs(coord1['rightwall'][1] - coord2['leftwall'][1]) <= const_VERTICAL_THRESHOLD):
                    touched[j] = True
                    top_left_y = min(top_left_y, coord2['topleft'][1])
                    bottom_right_x = coord2['bottomright'][0]
                    bottom_right_y = max(bottom_right_y, coord2['bottomright'][1])
            
            # Add box to output when all the merging is done
            ret.append((top_left_x, top_left_y, bottom_right_x, bottom_right_y))
    return ret

if __name__ == '__main__':
    """
    for testing
    """
    #print(detect_text(image_path='C:\\Users\\kartik.gokte\\Desktop\\python tut\\test1.jpg'))
    img = cv2.imread('test.jpg')
    print(detect_text(img_in_memory=True, img=img, img_name='test.jpg'))
