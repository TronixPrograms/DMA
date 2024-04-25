import pickle
import sys
import os
import warnings
import time
warnings.filterwarnings("ignore")
import deepmultilingualpunctuation 
try:
    res_path=sys.argv[1]
    if not os.path.exists(res_path+'mlp.bin'): #Si no existe el objeto binario
        #Lo crea
        punctuation_model = deepmultilingualpunctuation.PunctuationModel()
        objeto_serializado = pickle.dumps(punctuation_model)
        with open(res_path+'mlp.bin', 'wb') as file:
            file.write(objeto_serializado)
    else:
        #Deserializar
        punctuation_model = pickle.loads(open(res_path+'mlp.bin', 'rb').read()) 
    print("importado")  
    sys.stdout.flush()       
except Exception as e:
    print("Error",e)  
    sys.stdout.flush()       
while True:
    # Lee el comando de entrada desde el stdin
    texto = sys.stdin.readline().strip()
    # Verifica el comando y ejecuta la función correspondiente
    if len(texto)>5:
        try:
            texto=punctuation_model.restore_punctuation(texto)
            print(texto)
            sys.stdout.flush()
        except Exception as e:
            print(e)            
    elif texto=="-":
        break  
    time.sleep(3)    
punctuation_model=None