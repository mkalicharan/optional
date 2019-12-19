from enum import Enum
import pickle
import io, os, json
import pprint
from google.cloud import vision
from google.cloud.vision import types
from PIL import Image, ImageDraw
import tkinter
import tkinter.filedialog as fd
import os
import datetime
import System_details as sd
TaskName = 'DeTexT'


class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5


def draw_boxes(image, bounds, color):
    """Draw a border around the image using the hints in the vector list."""
    draw = ImageDraw.Draw(image)

    for bound in bounds:
        draw.polygon([
            bound.vertices[0].x, bound.vertices[0].y,
            bound.vertices[1].x, bound.vertices[1].y,
            bound.vertices[2].x, bound.vertices[2].y,
            bound.vertices[3].x, bound.vertices[3].y], None, color)
    return image


def get_document_bounds(image_file, feature, flag):
    """Returns document bounds given an image."""
    # print("hiiii"+ str(type(image_file)) + str(image_file))
    image_file1 = str(image_file[str(image_file).rfind('/'):-4])

    bounds = []
    with io.open(image_file, 'rb') as image_file:
        content = image_file.read()
    image = types.Image(content=content)

    response = client.document_text_detection(image=image)

    ############################################################### this is for line by line detection
    items = []
    lines = {}
    for text in response.text_annotations[1:]:
        top_x_axis = text.bounding_poly.vertices[0].x
        top_y_axis = text.bounding_poly.vertices[0].y
        bottom_y_axis = text.bounding_poly.vertices[3].y
        if top_y_axis not in lines:
            lines[top_y_axis] = [(top_y_axis, bottom_y_axis), []]

        for s_top_y_axis, s_item in lines.items():
            if top_y_axis < s_item[0][1]:
                lines[s_top_y_axis][1].append((top_x_axis, text.description))
                break
    for _, item in lines.items():
        if item[1]:
            words = sorted(item[1], key=lambda t: t[0])
            items.append((item[0], ' '.join([word for _, word in words]), words))

    for i in items:
        if flag == 0:
            print(i[1])
            vals = i[1]
            # print('1: ' + str(type(vals))) #string cheeee
            # vals = vals.encode("utf-8")
            # vals = str(vals,"utf-8")
            # print('2: '+ str(type(vals))) #bytes ma convert thai jai che
            # i need vals to be string
            # su karu?????
            text = text_output + image_file1 + '.txt'
            f = open(text, 'a', encoding='utf-8')
            f.write('\n' + vals)
            f.close()
            # for json output but we dont need json output
            # jsonn = image_file1 +'.json'
            # f = open(jsonn, 'a')
            # f.write(str(response))
            # f.close()
    flag = 1
    ##############################################################
    document = response.full_text_annotation

    # Collect specified feature bounds by enumerating all document features
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    for symbol in word.symbols:
                        if (feature == FeatureType.SYMBOL):
                            bounds.append(symbol.bounding_box)

                    if (feature == FeatureType.WORD):
                        bounds.append(word.bounding_box)

                if (feature == FeatureType.PARA):
                    bounds.append(paragraph.bounding_box)

            if (feature == FeatureType.BLOCK):
                bounds.append(block.bounding_box)

        if (feature == FeatureType.PAGE):
            bounds.append(block.bounding_box)
    # The list `bounds` contains the coordinates of the bounding boxes.
    return bounds, flag


def render_doc_text(filein, fileout):
    flag = 0
    image = Image.open(filein)
    # bounds,flag = get_document_bounds(filein, FeatureType.PAGE, flag)
    # draw_boxes(image, bounds, 'blue')
    # bounds,flag = get_document_bounds(filein, FeatureType.PARA, flag)
    # draw_boxes(image, bounds, 'red')
    bounds, flag = get_document_bounds(filein, FeatureType.WORD, flag)
    draw_boxes(image, bounds, 'yellow')
    fileout = image_output + fileout
    if fileout is not 0:
        image.save(fileout)
    else:
        image.show()


if __name__ == '__main__':
    pp = pprint.PrettyPrinter(indent=4)
    StartDateTime = datetime.datetime.now()
    LoggedInUser = sd.get_logged_in_user()
    MachineName = sd.get_machine_name()
    Country, Location, mail = sd.get_mail_country_and_location()
    AutomationType = 'DATA SCIENCE SCRIPT'
    NoOfUnits = 0
    try:
        file = 'file.pickle'
        with open(file, 'rb') as file:
            data1 = pickle.load(file)
            with open('gjson.json', 'w') as f:
                f.write(data1)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'gjson.json'
            client = vision.ImageAnnotatorClient()
            os.remove('gjson.json')

        root = tkinter.Tk()
        root.withdraw()
        msg = 'Welcome to Photo to Text Converter [o`] \n Add all your images into the input/images folder: \n ' \
              'The output will be generated in the output/image_output/ and output/text_output/ folders respectively\n\n'
        input_dir = os.getcwd()
        input_dir = fd.askdirectory(parent=root, initialdir=input_dir, title='Please select image input directory')
        if len(input_dir) > 0:
            print("You chose input directory as :%s" % input_dir)

        output_dir = os.getcwd()
        output_dir = fd.askdirectory(parent=root, initialdir=output_dir, title='Please select output directory')
        if len(output_dir) > 0:
            print("You chose output directory as :%s" % output_dir)

        input_path = input_dir + '/'
        entries = os.listdir(input_path)
        image_output = output_dir + '/image_output/'
        text_output = output_dir + '/text_output/'

        counter = 0
        print(msg)
        NoOfUnits = len(entries)

        for entry in entries:
            fileout = entry
            print('loading ' + str(counter) + ' image: ' + str(entry))
            print(input_path)
            img = input_path + entry
            # entry = "image.jpg"
            with io.open(img, 'rb') as image_file:
                content = image_file.read()
                render_doc_text(img, fileout)
            print('processing complete for ' + str(counter) + ' image: ' + str(entry))
            print('\n')
            counter = counter + 1
        EndDateTime = datetime.datetime.now()
        Status = "Completed"
    except:
        EndDateTime = datetime.datetime.now()
        Status = "Failed"
    print(TaskName,StartDateTime,EndDateTime,Status,LoggedInUser, MachineName, Country, Location,AutomationType, NoOfUnits)
    sd.storing_in_db(TaskName,StartDateTime,EndDateTime,Status,LoggedInUser, MachineName, Country, Location,AutomationType, NoOfUnits)
