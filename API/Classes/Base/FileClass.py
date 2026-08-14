#import ujson as json
import json

class File:
    @staticmethod
    def readFile(path):
        try:   
            with open(path, mode="r") as f:
                data = json.loads(f.read())
            #cirilica u json file
            #data = json.load(open(path, encoding='utf-8-sig'))
            return data
        except( IndexError):
            raise IndexError
        except(IOError):
            raise IOError
        except OSError:
            raise OSError

    @staticmethod
    def writeFile(data, path):
        try:
            with open(path, mode="w") as f:
                #json
                #f.write(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
                #f.write(json.dumps(data, ensure_ascii=True, indent=4, sort_keys=False))
                #ascii false da zapisemo cirilicu u file
                f.write(json.dumps(data, ensure_ascii=True, indent=4, sort_keys=False))
            #f.write(json.dumps(data))
        # except(IOError, IndexError):
        #     return('File not found or file is empty')
        #ovako prosljedjujemo exception u prethodnom slucaju vracamo response u funkciju koja poziva writeFile
        except(IOError, IndexError):
            raise IndexError
        except OSError:
            raise OSError
        
        #drugi nacin pisanj u file
        #with open(self.hData, mode="w") as f:
        #json.dump(data,f)

    @staticmethod
    def writeFileUJson(data, path):
        try:
            with open(path, mode="w") as f:
                #usjon
                f.write(json.dumps(data))
        except(IOError, IndexError):
            raise IndexError
        except OSError:
            raise OSError

    @staticmethod
    def readParamFile(path):
        try:
            with open(path, mode="r") as f:
                data = json.loads(f.read())
            return data
        except( IndexError):
            raise IndexError
        except(IOError):
            raise IOError
        except OSError:
            raise OSError