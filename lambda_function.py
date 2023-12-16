import os
import sys
import logging
import json
import base64
import pandas as pd
import io
import psycopg2

from requests_toolbelt.multipart import decoder
logging.getLogger().setLevel(logging.DEBUG)

def handler(event, context):
    logging.warning(f"ℹ️🤖LLM Inference generator...")
    logging.info(f'ℹ️🔔' +  sys.version + '!' )
    logging.info(f'Body is: {event}')
    _uploadFiles(event['body-json'])
    return {'statusCode': 200}



def _uploadFiles(base64Files):
    _decodeBase64Files(base64Files)


def _decodeBase64Files(base64Files):
    decoded_data = base64.b64decode(base64Files)
    decoded_string = decoded_data.decode("utf-8")
    boundary = str(decoded_string.split('\r')[0])[2:]
    if '\r\n' not in decoded_string: decoded_string = decoded_string.replace('\n', '\r\n')
    decoded_string = decoded_string.encode()
    logging.info(f'🔔Ready Encode')
    content_type = f"multipart/form-data; boundary={boundary}"
    multipart_data = decoder.MultipartDecoder(content=decoded_string, content_type=content_type)
    logging.info(f'🔔Ready multipart')
    for part in multipart_data.parts:
        _toDF(_getFileName(part.headers),part.text)

def _getFileName(headers):
  logging.info(f'Headers: {headers}') 
  logging.info(f'Headers type: {type(headers)}')
  try:
        content_disposition = headers[b'Content-Disposition'].decode('utf-8')
        filename_start = content_disposition.find('filename="') + len('filename="')
        filename_end = content_disposition.find('"', filename_start)
        filename = content_disposition[filename_start:filename_end]
        logging.info(f'🟠filename: {filename}')
        return filename
  except Exception as e:
        logging.error(f'🚨Error: {e}')
  return None


def _toDF(filename,text):
    logging.info(f'🔔To DF... filename: {filename}')
    data = io.StringIO(text)
    df = pd.read_csv(data,dtype='str')
    logging.info(f'🔔DF shape: {df.shape}')
    return df    


def _saveToDB(filename,df):
    
    conn = psycopg2.connect(
            dbname=os.environ.get("DB_NAME"), 
            user=os.environ.get("DB_USER"), 
            password=os.environ.get("DB_PASSWORD"), 
            host=os.environ.get("DB_HOST"), 
            port=os.environ.get("DB_P0RT")
        )
    
    cursor = conn.cursor()
    
    if filename.contains("hired_employees"):
        insert_query = os.environ.get("INSERT_QUERY_HIRED_EMPL")
    
    elif filename.contains("departments"):
        insert_query = os.environ.get("INSERT_QUERY_DEPT")
        
    elif filename.contains("jobs"):
        insert_query = os.environ.get("INSERT_QUERY_JOBS")
    
    data_to_insert = [tuple(x) for x in df.values]
    
    try:
        batch_size = 1000
        for i in range(0, len(data_to_insert), batch_size):
            batch = data_to_insert[i:i+batch_size]
            cursor.executemany(insert_query, batch)
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        logging.error("Error:", e)

    finally:
        cursor.close()
        conn.close()











# def _getFileName(headers):
#   logging.info(f'Headers: {headers}') 
#   logging.info(f'Headers type: {type(headers)}')
#   try:
#         content_disposition = headers[b'Content-Disposition'].decode('utf-8')
#         logging.info(f'🟠content_disposition: {content_disposition}')
#         filename_start = content_disposition.find('filename="') + len('filename="')
#         logging.info(f'🟠filename_start: {filename_start}')
#         filename_end = content_disposition.find('"', filename_start)
#         logging.info(f'🟠filename_end: {filename_end}')
#         filename = content_disposition[filename_start:filename_end]
#         logging.info(f'🟠filename: {filename}')
#         return filename
#   except Exception as e:
#         logging.error(f'🚨Error: {e}')
          
# #   content_disposition = headers[b'Content-Disposition'].decode('utf-8')
# #   filename_start = content_disposition.find('filename="') + len('filename="')
# #   filename_end = content_disposition.find('"', filename_start)
# #   filename = content_disposition[filename_start:filename_end]
# #   return filename
#   return "🫠"