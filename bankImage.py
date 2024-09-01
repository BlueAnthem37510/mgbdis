import os, png, glob, numpy
from  PIL import Image

def toInt(bytes):
    return int.from_bytes(bytes, "big")
def toBytes(intt, num=1):
    return intt.to_bytes(num, byteorder='big')  
def toHex(intOrBytes, num=1):
    if isinstance(intOrBytes, int):
        return hex(intOrBytes)[2:]
    else:
        return intOrBytes.hex()
def Hex(hexstring):
    return int("0x"+hexstring, 16)
def swap(bytes, num=1):
    hexx = toHex(bytes, 1)
    return Hex(hexx[num:] + hexx[:num])



class ImageData():
    def __init__(self, path, outputPath):
        self.path = path
        self.outputPath = outputPath
        self.data =None
       
        with open(path, "rb") as f:
            self.data = f.read()
        self.imageSize = toInt(toBytes(self.data[1])+toBytes(self.data[0]))
        self.compressedValue = self.data[2]
        self.data = self.data[3:]
        self.uncompressed = self.uncompress()
       
    def uncompress(self):
        newImageData = bytearray()
        imageLength = self.imageSize
        address = 0
        self.dataSize = 3
        while(imageLength > 0):
            
            b = self.data[address]
            if b != self.compressedValue:
                newImageData.append(b)
                imageLength -= 1
                address += 1
                self.dataSize += 1
            else:
                newImageData, address, imageLength = self.compressed_section(newImageData, address, imageLength)
                        
        return newImageData
    def compressed_section(self,newImageData, address, imageLength):        
    
        vramStartAddress = Hex("8000") #change to 8000 just for testing
        address += 1
        byte2 = self.data[address]
        address += 1
        byte1 = self.data[address]
        address += 1
        self.dataSize += 3
        #first 4 bits of repeatCount + initialTargetAddress is target address
        initialTargetAddress = toInt(toBytes(swap(byte1 & Hex("f0") )) + toBytes(byte2))
        #second 4 bits of repeatCount + 4 = repeatCount
        repeatCount = (byte1 & Hex("0f")) + Hex("04")
        if repeatCount == 19:
            repeatCount = self.data[address]
            address += 1
            self.dataSize +=1
            repeatCount = repeatCount + 19            

        targetAddress = initialTargetAddress
        while repeatCount > 0:             
            imageRow = 0
            if vramStartAddress + targetAddress > vramStartAddress + len(self.data):
                temp = bytearray(initialTargetAddress)
                targetAddress = toInt(toBytes(temp[0] + Hex("f0")) + toBytes(byte2))
                if targetAddress > vramStartAddress:
                    imageRow = 0
                    targetAddress = initialTargetAddress
                else:
                
                    imageRow = newImageData[targetAddress] # should be data from address
            else:
               
                imageRow = newImageData[targetAddress] # should be data from address
            
            newImageData.append(imageRow)
            targetAddress += 1
            imageLength -= 1
            if imageLength <= 0:
                break
            repeatCount -= 1
                            
        return newImageData, address, imageLength
    def to_png(self):
        #replace this later
        
        write_image(basename= "",output=self.outputPath, data=self.uncompressed)
def compress_binary(data):
    minCopyLength = 4
    length = len(data).to_bytes(2)[::-1]
    compression_value = get_compression_value(data)
    output = bytearray()
    output.extend(length)
    output.append(compression_value)
    
    i = 0
    while i < len(data):
        group = group = data[i:i+4]
        nextIndex = i + 3 
        range_ = data[:i]
        nextValue = None
        while(True):
            nextIndex += 1
            if nextValue != None:
                group.append(nextValue)
            if nextIndex < len(data):    
                nextValue = data[nextIndex]
            else:
                nextIndex = None
            zeroSequence = len(list(filter(lambda x : x != 0, group)))
            if (zeroSequence == 0):
                if (nextValue != 0 or nextIndex == None) and group + bytearray([nextValue]) not in range_:
                    output.append(compression_value)
                    length  =  len(group)-minCopyLength
                    if length > 15:
                        output.append(255 - length-minCopyLength)
                        output.append (15)
                        output.append (length-15)
                    else:
                        output.append(255)
                        output.append(240 + len(group)-minCopyLength)
                    i += len(group)
                    break 
                else:
                    continue

            if len(group) > i or len(group) + i > len(data) or group not in range_:
                output.append(data[i])
                i += 1
                break
            
            if group + bytearray([nextValue]) not in range_ or (group in range_ and nextIndex == None):
                output.append(compression_value)
                length = len(group)-minCopyLength
                if nextIndex == None:
                    length += i %8
                test = data.index(group)
                if test > 255: 
                    print("Too big: " + str(test))
                output.append(test)
                output.append(length)
                i += len(group)
                break  
    return output   
  
def get_compression_value(data):
    check = 1
    while(True):
        if (not any([check == x for x in data])):
            return check
        check += 1
def read_image(path):
    image =  Image.open(path)
    pixel_data = [[] for i in range(image.height)]
    for y in range(image.height):
        
        for x in range(image.width):
            pixel_data[y].append(image.getpixel((x,y)))
    bin = convert_image_to_binary(pixel_data)
    data = compress_binary(bin)
def convert_image_to_binary(pixel_data):
    width = int(len(pixel_data[0])/8)
    height = int(len(pixel_data)/8)
    data = bytearray()
    for y in range(height):
        for x in range(width):
            for z in range(8):
                row = pixel_data[(y*8)+z][(x*8):(x*8)+8]
                byte1 = 0
                byte2 = 0
                for i in range(8):
                    pixel = row[i]
                    match(pixel):
                        case 0: continue
                        case 1: byte1 = set_bit(byte1, i)
                        case 2: byte2 = set_bit(byte2, i)
                        case 3: byte1, byte2  = (set_bit(byte1, i),set_bit(byte2, i))
                data.append(byte1)
                data.append(byte2)
    return data

def set_bit(value, bit):
    bit = 7-bit
    return value | (1<<bit)
def abort(message):
    print("FATAL: ", message)
    os._exit(1)
def write_image( basename, output, data):

    # defaults
    width = 128
    palette = 0xe4
    bpp = 2


    image_output_path = os.path.join(output)

    relative_path = os.path.join(output, basename + '.' + "{}bpp".format(bpp))
    path = os.path.join(output, basename + '.png')

    bytes_per_tile_row = bpp  # 8 pixels at 1 or 2 bits per pixel
    bytes_per_tile = bytes_per_tile_row * 8  # 8 rows per tile

    num_tiles = len(data) // bytes_per_tile
    tiles_per_row = width // 8

    # if we have fewer tiles than the number of tiles per row, or if an odd number of tiles
    if (num_tiles < tiles_per_row) or (num_tiles & 1):
        # then just make a single row of tiles
        tiles_per_row = num_tiles
        width = num_tiles * 8

    tile_rows = (num_tiles / tiles_per_row)
    if not tile_rows.is_integer():
        print('Invalid length ${:0x} or width {} for image block: {}'.format(len(data), width, basename))
        return

    height = int(tile_rows) * 8

    pixel_data = convert_to_pixel_data(data, width, height, bpp)
    rgb_palette = convert_palette_to_rgb(palette, bpp)
    #test = Image.open("C:\Users\Erika\Documents\live2d\CubismSdkForWeb-5-r.1\Samples\Resources\102001\model.1024")
    image = Image.new(mode ="P", size = [len(pixel_data[0]), len(pixel_data)])
    image = image.convert("P",palette=Image.ADAPTIVE, colors=4)
    image.putpalette(rgb_palette)
    for x in range(len(pixel_data)):
        for y in range(len(pixel_data[0])):
            image.putpixel((y,x), pixel_data[x][y])
    with open(output, "wb+") as f:
        image.save(f)
    return relative_path


def convert_to_pixel_data(data, width, height, bpp):
    result = []
    for y in range(0, height):
        row = []
        for x in range(0, width):
            offset = coordinate_to_tile_offset(x, y, width, bpp)

            if offset < len(data):
                # extract the color from the one or two bytes of tile data at the offset
                shift = (7 - (x & 7))
                mask = (1 << shift)
                if bpp == 2:
                    color = ((data[offset] & mask) >> shift) + (((data[offset + 1] & mask) >> shift) << 1)
                else:
                    color = ((data[offset] & mask) >> shift)
            else:
                color = 0

            row.append(color)
        result.append(row)

    return result


def coordinate_to_tile_offset( x, y, width, bpp):
    bytes_per_tile_row = bpp  # 8 pixels at 1 or 2 bits per pixel
    bytes_per_tile = bytes_per_tile_row * 8  # 8 rows per tile
    tiles_per_row = width // 8

    tile_y = y // 8
    tile_x = x // 8
    row_of_tile = y & 7

    return (tile_y * tiles_per_row * bytes_per_tile) + (tile_x * bytes_per_tile) + (row_of_tile * bytes_per_tile_row)


def convert_palette_to_rgb( palette, bpp):
    col0 = 255 - (((palette & 0x03)     ) << 6)
    col1 = 255 - (((palette & 0x0C) >> 2) << 6)
    col2 = 255 - (((palette & 0x30) >> 4) << 6)
    col3 = 255 - (((palette & 0xC0) >> 6) << 6)
    if bpp == 2:
        return [
            col0, col0, col0,
            col1, col1, col1,
            col2, col2, col2,
            col3, col3, col3
        ]
    else:
        return [
            col0, col0, col0,
            col3, col3, col3
        ]
    

files = glob.glob("./disassembly/sprites/*.bin")
for f in files:
    print(f)
    input = f.replace(".bin", ".png")
    read_image(input)
    #img = ImageData(f, f.replace(".bin", ".png"))
    #img.ToPng()
    
    