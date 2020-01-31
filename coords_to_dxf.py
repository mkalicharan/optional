import ezdxf
import csv
import os

def coords_to_dxf(text, lines, dpi, height, dxfpath):
    """
    Outputs a dxf file with text at coordinates given by the csv file
    
    Arguments:
        text {[(int, int, int, int, str)]} -- List of tuples containing text boxes
        lines {[(int, int, int, int)]} -- List of tuples containing line coordinates
        dpi {int} -- DPI of the image
        height {int} -- Height of the image in pixels
        dxfpath {str} -- Path to the DXF file
    """    
    print("Running 'coords_to_dxf' function")
    
    doc = ezdxf.readfile(dxfpath)
    ms = doc.modelspace()

   #Add text to DXF file
    for l in text:
        ms.add_text(l[4], dxfattribs={
                 'style': 'LiberationSerif',
                 'height': abs(l[3]-l[1])/(3)}).set_pos((l[0]/1, (height-l[3])/1), align='LEFT')    
    #Add lines to DXF file
    for l in lines:
        points = [(l[0]/1, (height-l[1])/1), (l[2]/1, (height-l[3])/1)]
        ms.add_line(points[0], points[1])

    working_dir = os.path.abspath(os.path.dirname(__file__))
    doc.saveas(dxfpath)
    print("Finished 'coords_to_dxf' function")
if __name__ == '__main__':
    coords_to_dxf("C:\\Users\\kartik.gokte\\Desktop\\BrewCAD stuff\\Drawings\\Output\\out_0_082-0267-120-054-01.pdf\\boxes_out_0_082-0267-120-054-01.pdf.csv", "C:\\Users\\kartik.gokte\\Desktop\\BrewCAD stuff\\out.csv", 96, 3296)