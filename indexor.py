import logging
import sqlite3
import socket                   # get host name
import time                    # sleep, timestamp
import pathlib, hashlib
import multiprocessing as mp
from datetime import datetime, timezone
import sys, re                       
import json                     
import exifread
import docx
import pikepdf
import eyed3
from magika import Magika

m = Magika()

# create logger
logger = logging.getLogger('monitorMain')
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

configData = {}
configFile = sys.argv[1]
with open(configFile, 'r') as f:
    configData = json.load(f)
database_url = configData["DBPATH"].replace("sqlite:///","")
logger.info(f'Hello opening db {database_url} ')
conn = sqlite3.connect(database_url, timeout=20)
cursor = conn.cursor()
hostname = "fs_{}_{}".format(socket.gethostname(),datetime.now().strftime("%Y%m"))
hostname = hostname.replace('-','')


def create_table(hostname):
    logger.debug(f'create_table cursoor :  {cursor} ')
    sql_crTable_pre = "CREATE TABLE IF NOT EXISTS {} (".format(hostname)
    sql_crTable_post = """ 
                sha256  VARCHAR(255) NOT NULL,
                path  VARCHAR(255) NOT NULL,
                file  VARCHAR(255) NOT NULL,
                extention CHAR(25) NOT NULL,
                size int NOT NULL,
                mtime real,
                month CHAR(25) NOT NULL,
                year int NOT NULL,
                all_author CHAR(250),
                img_camera CHAR(250),
                img_focallengh CHAR(250),
                mp3_title CHAR(250),
                mp3_album CHAR(250),
                meta VARCHAR(50000)
            ); """
    sql_crTable = sql_crTable_pre + sql_crTable_post
    logger.debug(sql_crTable)
    cursor.execute(sql_crTable)

def sha256sum(filename):
    h  = hashlib.sha256()
    b  = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        for n in iter(lambda : f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()

def getMetaData(doc):
    metadata = {}
    prop = doc.core_properties
    metadata["author"] = prop.author
    metadata["category"] = prop.category
    metadata["comments"] = prop.comments
    metadata["content_status"] = prop.content_status
    metadata["created"] = prop.created
    metadata["identifier"] = prop.identifier
    metadata["keywords"] = prop.keywords
    metadata["last_modified_by"] = prop.last_modified_by
    metadata["language"] = prop.language
    metadata["modified"] = prop.modified
    metadata["subject"] = prop.subject
    metadata["title"] = prop.title
    metadata["version"] = prop.version
    return metadata

def GetfromMp3(fullfile):
    audio = eyed3.load(fullfile)
    mp3info= {}
    mp3info['artist'] = audio.tag.artist
    mp3info['album']  = audio.tag.album
    mp3info['title']  = audio.tag.title
    return mp3info

def GetfromPdf(fullfile):
    pdf = pikepdf.Pdf.open(fullfile)
    docinfo = pdf.docinfo
    objReturn = {}
    for key, value in docinfo.items():
        objReturn[key] = value
    #print("pdf", objReturn)
    return objReturn
    
def GetfromDoc(fullfile):
    doc = docx.Document(fullfile) 
    metadata_dict = getMetaData(doc)
    #print("Docx", metadata_dict)
    return metadata_dict

def GetfromExif(fullfile):
    return_exif = {}
    try :
        f = open(fullfile, 'rb')        # open for meta
    except :
        return ''
    try:
        tags = exifread.process_file(f, details=False)
        if 'JPEGThumbnail' in tags.keys():
            tags["JPEGThumbnail"] = ''
        for tag in tags.keys():
            #print(tag, "\t",str(tags[tag])[:30])
            if tag != 'JPEGThumbnail' : 
                tag_key = tag.replace(' ','_')
                return_exif[tag_key] = str(tags[tag])[:100]  
        #print("exif", return_exif)     
        return return_exif
    except :
        return False

def dateFromExif(exifObj):
    dayfolder = ''
    for tag in exifObj:
        if 'DateTimeOriginal' in tag:
            #print('  date found in exif', tag, "\t",str(exifObj[tag]))
            datestr = str(exifObj[tag])
            if datestr.find("/") > 0:
                dayfolder = datestr.replace('/','_').replace(' ', '-')
            else:
                dayfolder = datestr.replace(':','_').replace(' ', '-')
    return dayfolder

def dateFromMtime(mtimeFile):
    #print('  date from mtime ', mtimeFile, "\t")
    dateTimeFile = datetime.fromtimestamp(mtimeFile, tz=timezone.utc)
    return dateTimeFile.strftime("%Y_%m")

def isImage(extention) :
    extImage = ['jpg','jpeg','png', 'gif']
    if  extention  in extImage:
        return True
    else :
        return False

def isMp3(extention) :
    extMp3 = ['mp3', 'wav']
    if  extention  in extMp3:
        return True
    else :
        return False

def isPdf(extention) :
    extPdf = ['pdf']
    if  extention  in extPdf:
        return True
    else :
        return False

def isDoc(extention) :
    extDoc = ['docx']
    if  extention  in extDoc:
        return True
    else :
        return False

def AddEntry(cursor, sha256, path, file, extention, size, mtime, \
                month, year, all_author, img_camera, img_focallengh, mp3_title, mp3_album, meta):
    cursor.execute('''INSERT INTO {} (sha256, path, file, extention, size, mtime, month, year, all_author, img_camera, img_focallengh, mp3_title, mp3_album, meta)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''.format(hostname),    (sha256, path, file, extention, size, mtime, month, year, all_author, img_camera, img_focallengh, mp3_title, mp3_album, meta))
    conn.commit()

def myWork(filePath):
    logger.debug(f'START PATH {str(filePath)}')
    metaStr = ''
    appModel = ''
    focalLengh = ''
    author = ''
    exif = ''
    mp3_album= ''
    mp3_title= ''
    DocObj = ''
    PdfObj = ''
    Mp3Obj = ''
    mtime = filePath.stat().st_mtime
    folderdate= dateFromMtime(mtime)
    extention = filePath.suffix.lower().replace('.', '')
    filename = filePath.name
    foldername = str(filePath.parent)
    size = filePath.stat().st_size
    #logger.debug(f'  META {str(filePath)} ')
    try:
        if isImage(extention) :
            exif = GetfromExif(str(filePath))
            folderdate = dateFromExif(exif)
            if 'Image_Model' in exif.keys():
                appModel = exif['Image_Model']
                appModel = re.sub(r"\s+", "_", appModel)
                appModel = re.sub(r"_$", "", appModel)
                appModel = re.sub(r"[^0-9A-Za-z\-_]+", "", appModel)
                appModel = appModel[:30]
            if 'EXIF_FocalLengthIn35mmFilm' in exif.keys():
                focalLengh = exif['EXIF_FocalLengthIn35mmFilm']

        if isDoc(extention) :
            DocObj=GetfromDoc(str(filePath))
            if 'author' in DocObj.keys():
                author = DocObj['author']
        if isPdf(extention) :
            PdfObj=GetfromPdf(str(filePath))
            if '/Creator' in PdfObj.keys():
                author = str(PdfObj['/Creator']) 
            if '/Author' in PdfObj.keys():
                author = str(PdfObj['/Author']) 
        if isMp3(extention) :
            Mp3Obj=GetfromMp3(str(filePath))
            if 'artist' in Mp3Obj.keys():
                author = Mp3Obj['artist']
            if 'album' in Mp3Obj.keys():
                mp3_album = Mp3Obj['album']
            if 'title' in Mp3Obj.keys():
                mp3_title = Mp3Obj['title']
    except :
        print("Error on metadata extraction")
    logger.debug(f'  SHA {str(filePath)} ')
    sha256 = sha256sum(str(filePath))
    month = folderdate[:7]
    year = folderdate[:4]
    metaStr=str(exif) + str(DocObj) + str(PdfObj) + str(Mp3Obj)
    #sha256, path, file, extention, size, mtime, month, year, all_author, img_camera, img_focallengh, mp3_title, mp3_album, meta
    #logger.debug(f'  INSERT {str(filePath)} ')
    AddEntry(cursor, sha256,foldername, filename, extention,size,mtime,\
            month,year, author, appModel, focalLengh,\
            mp3_title, mp3_album, metaStr) 

def get_all_path(directory):
    logger.info(f'   _get_all_path from {directory} ')
    Todo = []
    for path in sorted(pathlib.Path(directory).rglob('*')):
        if path.is_file() :
            Todo.append(path)
    return Todo

def main():
    create_table(hostname)
    pool = mp.Pool(mp.cpu_count())  
    while (1):
        start = time.perf_counter()
        global_Todo =  get_all_path(configData["INDEXOR_PATH"])
        logger.info(f'BIG LIST :  {len(global_Todo)} items')
        results = pool.map(myWork, [row for row in global_Todo], 2)
        finish = time.perf_counter()
        logger.info(f'Finished in {round(finish-start, 2)} second(s) for : {len(global_Todo)} items')
        time.sleep(configData["INDEXOR_SLEEP"])
        

if __name__ == '__main__':
    sys.exit(main())