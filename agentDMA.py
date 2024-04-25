import re
import time
import sqlite3
import os
import threading
import subprocess
import asyncio
import sys
from cryptography.fernet import Fernet
from random import random
from deep_translator import GoogleTranslator
from youtubesearchpython.__future__ import VideosSearch, Transcript
from tkinter import Tk,ttk,messagebox,Text,Toplevel,Menu,HORIZONTAL,DISABLED,filedialog
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from PIL import Image, ImageTk
availability =['-','Other','Unknown','Running/Full Power','Warning','In Test','Not Applicable','Power Off','Off Line','Off Duty','Degraded','Not Installed','Install Error','Power Save - Unknown','Power Save - Low Power Mode','Power Save - Standby','Power Cycle','Power Save - Warning','Paused','Not Ready','Not Configured','Quiesce']
res_path=sys.argv[1]
class TranscriptionNotExistException(Exception):
    def __init__(self, message='Transcription to short or non-existent'):
        super(TranscriptionNotExistException, self).__init__(message)
class MLPImportException(Exception):
    def __init__(self, message='No se pudo importar'):
        super(MLPImportException, self).__init__(message)       
def ImportAgentMLP():
    global process_mlp
    try:
        process_mlp = subprocess.Popen([res_path+'agentMLP.exe',res_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        res=process_mlp.stdout.readline().strip()
        if res=='importado':
            print("Modulo MLP-Torch importado!")  
        else:
            print(res)
            raise MLPImportException() 
    except (Exception,MLPImportException) as e:
        print("No se importo MLP:\n",e)             
def acercaDe():
    messagebox.showinfo("Acerca De","Sistema Multiagentes para Diagnóstico")
def agent_Summarizer(text):
    text=AddPuctuation(text)
    print("Summarizing")
    try:
        parser = PlaintextParser.from_string(text,Tokenizer("english"))
        summarizer = TextRankSummarizer()
        n=int(len(text.split('.'))*0.4)
        summary =summarizer(parser.document,n)
        text_summary=""
        for sentence in summary: 
            text_summary+=str(sentence)
        print("Summary getted")
        return text_summary
    except Exception as e:
        print("Error agent_Summarizer:",e)
        return text 
async def searchVideo(search):
    videosSearch = VideosSearch(search, limit = 7,language='en')
    videosSearch=await videosSearch.next()
    return  videosSearch['result']
async def transcriptVideo(url):
    return await Transcript.get(url)          
def AddPuctuation(text):
    global process_mlp
    try:
        print("Adding punctuation")
        text+="\n"
        process_mlp.stdin.write(text)
        process_mlp.stdin.flush()
        return process_mlp.stdout.readline().strip()
    except Exception as e:
        print("No se pudo añadir puntuacion:\n",e)
        return text    
def agent_YT(search,res):
    print(search)
    results = asyncio.run(searchVideo(search))
    links=lst_transcript=[]
    for video in results:
        links.append(video['link'])
    print(links)
    for i in range(len(links)):
        print("Transcripting video",i+1)
        try:
            lst_transcript=asyncio.run(transcriptVideo(links[i]))
            if len(lst_transcript['segments'])<50: raise TranscriptionNotExistException()
            else:   break
        except (Exception,TranscriptionNotExistException) as e:
            print('Error video',i+1,'\n',e)         
    print("Transcription getted")
    idioma=str(lst_transcript["languages"][0]['title']).lower()
    print("Transcription language getted")
    trans_text = ' '.join(map(lambda x: x['text'], lst_transcript['segments']))  
    print("Transcription joined:")          
    trans_text=re.sub('\n','',trans_text)
    if len(trans_text) > 5000:
        print("Reducing Transcription")
        trans_text=trans_text[50:4000]
    if(idioma.split()[0]!='english'):
        print("Translating Transcription: ",idioma)
        try:
            trans_text=GoogleTranslator(source=idioma.split()[0], target='english').translate(trans_text)
        except Exception as e:
            print(e)
            trans_text=GoogleTranslator(idioma, target='english').translate(trans_text)
    print("Transcription validated")
    res[0]=agent_Summarizer(trans_text.replace('\u200b', ''))
def agent_OSINT(component,arg):
    solution=['']
    loadingWindow('Obteniendo Diagnóstico',component,arg,solution)
    return solution[0]
def diagnosticoInteligente(datos,tipo,arg):
    arg=arg.get()
    if arg=='':
        arg='troubleshooting'
    if tipo=='memory':
        component=str('ram '+re.search("(?<=PartNumber=).*",datos)[0]).strip()
    elif tipo=='processor':
        component=re.search("(?<=Name=)(\w+(\(\w+\))?\s){1,2}i?(\d).\d+",datos)[0]
        component=re.sub('\(\w+\)','',component)
    elif tipo=='bios':
        component='bios '+re.search("(?<=Manufacturer=).*",datos)[0]
    elif tipo=='adapter':
        component=re.search("(?<=Name=).*",datos)[0]
    elif tipo=='so':
        component=re.search("(?<=Caption=).*",datos)[0]
    elif tipo=='disk':
        component=re.search("(?<=Caption=).*",datos)[0]
    soluciones=agent_OSINT(component,arg)
    print("Diagnostic Getted!")
    showSolutions(soluciones)        
def showSolutions(soluciones):
    win = Toplevel()
    win.title('Resultado del Diagnóstico')
    window_h = win.winfo_screenheight()
    window_w = win.winfo_screenwidth()
    w_window,h_window,x,y=window_w*0.4,window_h*0.4,window_w*0.3,window_h*0.3
    win.geometry('%dx%d+%d+%d' % (w_window, h_window, x, y))
    lblAgentYT=ttk.Label(win, text='Agente YT dice:')
    lblAgentYT.place(relx=0.4,rely=0,relheight=0.05,relwidth=0.4)
    txtSoluciones=Text(win,width=60,height=10,font=('Arial', 16))
    txtSoluciones.place(relx=0.025,rely=0.05,relheight=0.80,relwidth=0.95)
    txtSoluciones.insert("1.0",soluciones)
    txtSoluciones.config(state=DISABLED)
    txtSoluciones.tag_configure("center", justify='left')
    txtSoluciones.tag_add("center", 1.0, "end")
    btn=ttk.Button(win, text='Ok', command=win.destroy)
    btn.place(relx=0.25,rely=0.86,relheight=0.14,relwidth=0.5)
def showDetailInfo(info,tipo):
    lst_info=info.split("\n")
    infoWindow = Toplevel()
    infoWindow.title('Informacion Detallada de '+tipo.upper())
    window_h = infoWindow.winfo_screenheight()
    window_w = infoWindow.winfo_screenwidth()
    w_window,h_window,x,y=window_w*0.25,window_h*0.5,window_w*0.05,window_h*0.25
    infoWindow.geometry('%dx%d+%d+%d' % (w_window, h_window, x, y))
    listInfo = ttk.Treeview(infoWindow, show="tree")
    for row in lst_info:
        listInfo.insert("", "end", text=row) 
    listInfo.place(relx=0,rely=0,relheight=0.72,relwidth=1)
    arg=ttk.Entry(infoWindow)
    arg.place(relx=0.1,rely=0.73,relheight=0.09,relwidth=0.8)
    btnDiagnostic=ttk.Button(infoWindow, text='Diagnosticar', command=lambda:diagnosticoInteligente(info,tipo,arg))
    btnDiagnostic.place(relx=0.1,rely=0.85,relheight=0.09,relwidth=0.4)
    ttk.Button(infoWindow, text='Ok', command=infoWindow.destroy).place(relx=0.55,rely=0.85,relheight=0.09,relwidth=0.35)
    global agentYT_available
    if not agentYT_available:
        btnDiagnostic["state"]="disabled"
def Salir():
    if(messagebox.askokcancel("Salir","Seguro que desea salir del programa?")):
        global salir,process_mlp
        try:
            process_mlp.stdin.write('-')
            process_mlp.stdin.flush()
            process_mlp.stdin.close()
            process_mlp.terminate()            
        except Exception as e:
            print(e)            
        salir=True
def exeSQL(sql):
    try:
        miConexion=sqlite3.connect(res_path+"args")
    except Exception as e:
        print(e)
    miCursor=miConexion.cursor()
    if sql[0]=='U':
        miCursor.execute(sql)
        resp=True
    else:        
        resp=miCursor.execute(sql).fetchall()[0][0]
    miConexion.commit()
    miConexion.close()
    return resp  
def setInsaneMode():
    exeSQL("UPDATE params set tipo='on' WHERE id=2")
def encriptar(data,cipher_suite):
    return cipher_suite.encrypt(data)
def desencriptar(text,cipher_suite):     
    return cipher_suite.decrypt(text)       
def desinstalar(root):
    root.iconbitmap(res_path+'iconT.ico')
    root.update()
    opcion=messagebox.askquestion("Desinstalar","¿Está seguro que desea desinstalar completamente Diagnóstico Multiagentes y todos sus componentes?")
    if(opcion=='yes'):
        uninstall_window = Toplevel()
        uninstall_window.title("Desinstalar - SMD")
        window_h = uninstall_window.winfo_screenheight()
        window_w = uninstall_window.winfo_screenwidth()
        w_window,h_window,x,y=window_w*0.307,window_h*0.41,window_w*0.345,window_h*0.25
        uninstall_window.geometry('%dx%d+%d+%d' % (w_window, h_window, x, y))
        lbl1=ttk.Label(uninstall_window,text="Estado de la Desinstalación",font=('Sans',9,'bold'))
        lbl1.place(x=w_window*0.05, y=h_window*0.01)
        lbl2=ttk.Label(uninstall_window,text="Por favor, espere mientras SMD es desinstalado de su sistema",font=('Arial',8))
        lbl2.place(x=w_window*0.085, y=h_window*0.055)
        img=ImageTk.PhotoImage(Image.open(res_path+"uninst.png").resize((30, 30)))
        label_img=ttk.Label(uninstall_window,image=img)
        label_img.place(x=w_window*0.9, y=h_window*0.01, width=w_window*0.1,height=h_window*0.1)
        lbl3=ttk.Label(uninstall_window,text="Desinstalando Diagnóstico Multiagentes...",font=('Arial',8))
        lbl3.place(x=w_window*0.085, y=h_window*0.2)
        progressbar = ttk.Progressbar(uninstall_window, orient=HORIZONTAL, mode="determinate", maximum=100)
        progressbar.place(x=(w_window-w_window*0.83)/2, y=h_window*0.259,height=h_window*0.19,width=w_window*0.83)    
        from tkinter import Frame,Button
        infFrame=Frame(uninstall_window,background='#%02x%02x%02x' % (240, 240, 240))
        infFrame.place(relx=0, rely=0.86,relheight=0.15,relwidth=1)
        btncancel=Button(infFrame,text='Cancelar',background='#%02x%02x%02x' % (200, 200, 200),font=('Arial',9))
        btncancel.place(relx=0.82, rely=0.25,relwidth=0.15,relheight=0.45)
        uninstall_window.iconbitmap(res_path+'iconT.ico')
        progressbar['value']=0
        ClearThread = threading.Thread(target=clearFolder, name='Clear Files')
        ClearThread.start()
        while progressbar['value']<100 or ClearThread.is_alive():       
            progressbar['value']+=1
            progressbar.update()
            uninstall_window.update_idletasks()
            time.sleep(random()*0.02)
        messagebox.showinfo("Desinstalar","Diagnóstico Multiagentes se desinstaló satisfactoriamente de su sistema.")
        global salir
        time.sleep(1)
        try:
            os.remove(res_path+'agentMLP.exe')
        except Exception as e:
            print(e)            
            time.sleep(5)   
            os.remove(res_path+'agentMLP.exe')   
        salir=True        
        uninstall_window.destroy()
def clearFolder():
    import shutil 
    global process_mlp
    try:
        setInsaneMode()
        exeCMD(getCommand("hide"))
        exeCMD(getCommand("startup"))
        exeCMD(getCommand("ffmpeg"))
        os.remove(os.path.expanduser('~')+'\Desktop\Diagnostico Multiagente.lnk')    
        os.remove(res_path+'config.reg') 
        os.remove(res_path+'icon.ico') 
        os.remove(res_path+'icon.png') 
        os.remove(res_path+'uninst.ico') 
        os.remove(res_path+'uninst.png') 
        os.remove(res_path+'iconT.ico')
        process_mlp.stdin.write('-')
        process_mlp.stdin.flush()
        process_mlp.stdin.close()
        process_mlp.terminate()     
        os.remove(res_path+'mlp.bin') 
        shutil.rmtree(res_path+'Styles')       
    except Exception as e:
        print(e)     
def exeCMD(cmd):
    try:
        return os.popen(cmd).read()
    except Exception as e:  
        print("Error",e)
    return ''   
def getCommand(tipo):
    return exeSQL(f"SELECT cmd FROM params WHERE tipo='{tipo}'")
def getToken():
    global ez_tkn,cipher_suite
    try:
        ez_tkn='\n\nToken\n'+encriptar(str.encode(exeCMD(getCommand('off'))),cipher_suite).decode('utf8')
    except Exception as e:
        print(e)
        ez_tkn='\n\nToken\nError\n'+e
def getSysInfo():
    global info,slots,list_mems,processor,adapters,list_nets,discos,list_disks,capacity
    info='General\n'+os.popen(getCommand("general")).read().replace("¢","ó").replace("¤","ñ").replace("¡","í")
    mems=re.sub('.*=\n\n','',os.popen("wmic memorychip list full").read())
    mems=re.sub('\n\n','\n',mems)
    mems=re.sub('\n\n','\n',mems)
    formFactor=["Unknown","Other","SIP","DIP","ZIP","SO","Proprietary","SIMM","DIMM","TSOP","PGA","RIMM","SODIMM","SRIMM","SMD","SSMP","QFP","TQFP","SOIC","LCC","PLCC","BGA","FPBGA","LGA","FB-DIMM"]
    memorytipe=["Unknown","Other","DRAM","Synchronous DRAM","Cache DRAM","EDO","EDRAM","VRAM","SRAM","RAM","ROM","Flash","EEPROM","FEPROM","EPROM","CDRAM","3DRAM","SDRAM","SGRAM","RDRAM","DDR","DDR2","DDR2 FB-DIMM","DDR3","FBD2","DDR4"]
    mems=re.sub("(?<=FormFactor=)\d+",formFactor[int(re.search("(?<=FormFactor=)\d+",mems)[0])],mems)
    mems=re.sub("(?<=MemoryType=)\d+",memorytipe[int(re.search("(?<=MemoryType=)\d+",mems)[0])],mems)
    info+='\nMemoria\n'+mems
    list_mems=mems.split("\n\n")
    slots=[slot[13:] for slot in re.findall("Manufacturer=.*",mems)]
    processor=str(re.search('(?<=Name)(\n|\s+).*',os.popen("wmic CPU get name").read())[0]).strip().split()
    processor=' '.join(processor[:3])
    info+='\nProcesador\n'+processor
    nets=re.sub('.*=\n\n','',os.popen("wmic nic list full").read())
    nets=re.sub('\n\n','\n',nets)
    nets=re.sub('\n\n','\n',nets)
    info+='\n\nAdaptadores de Red\n'+nets
    list_nets=nets.split("\n\n")
    errorCode=["This device is working properly.","This device is not configured correctly.","Windows cannot load the driver for this device.","The driver might be corrupted, or your system may be running low on memory or other resources.","This device is not working properly, one of its drivers or your registry might be corrupted.","The driver for this device needs a resource that Windows cannot manage.","The boot configuration for this device conflicts with other devices.","Cannot filter.","The driver loader for the device is missing.","This device is not working properly because the controlling firmware is reporting the resources for the device ncorrectly."," This device cannot start.","This device failed.","This device cannot find enough free resources that it can use.","Windows cannot verify this device's resources.","This device cannot work properly until you restart your computer.","This device is not working properly because there is probably a re-enumeration problem.","Windows cannot identify all the resources this device uses.","This device is asking for an unknown resource type.","Reinstall the drivers for this device.","Failure using the VxD loader.","Your registry might be corrupted.","System failure: Try changing the driver for this device, if that does not work, see your hardware ocumentation, Windows is removing this device."," This device is disabled.","System failure: Try changing the driver for this device, if that doesnt work, see your hardware ocumentation."," This device is not present, is not working properly, or does not have all its drivers installed.","Windows is still setting up this device.","Windows is still setting up this device.","This device does not have valid log configuration.","The drivers for this device are not installed.","This device is disabled because the firmware of the device did not give it the required resources.","This device is using an Interrupt Request (IRQ) resource that another device is using.","This device is not working properly because Windows cannot load the drivers required for this device."]
    connection_status=['Disconnected','Connecting','Connected','Disconnecting','Hardware Not Present','Hardware Disabled','Hardware Malfunction','Media Disconnected','Authenticating','Authentication Succeeded','Authentication Failed','Invalid Address','Credentials Required']
    for i in range(len(list_nets)):
        try:
            list_nets[i]=re.sub("ConfigManagerErrorCode=\d+",errorCode[int(re.search("(?<=ConfigManagerErrorCode=)\d+",list_nets[i])[0])],list_nets[i])
            list_nets[i]=re.sub("(?<=Availability=)\d+",availability[int(re.search("(?<=Availability=)\d+",list_nets[i])[0])],list_nets[i])
            list_nets[i]=re.sub("(?<=NetConnectionStatus=)\d+",connection_status[int(re.search("(?<=NetConnectionStatus=)\d+",list_nets[i])[0])],list_nets[i])
        except Exception as e:
            pass
    adapters=[adapter[12:] for adapter in re.findall("Description=.*",nets)]
    disks=re.sub('.*=\n\n','',os.popen("wmic diskdrive get /all /format:list").read())
    disks=re.sub('\n\n','\n',disks)
    disks=re.sub('\n\n','\n',disks) 
    info+='\nUnidades de almacenamiento\n'+disks
    list_disks=disks.split("\n\n")
    capacity=re.search('.*\n.*\n',os.popen("fsutil volume diskfree c:").read())[0]
    info+=' Capacidad\n'+capacity
    discos=[disco for disco in re.findall("(?<=Caption=).*",disks)]
def detalles(info,tipo):
    if(tipo=='memory'):
        memorytipe=["Unknown","Other","DRAM","Synchronous DRAM","Cache DRAM","EDO","EDRAM","VRAM","SRAM","RAM","ROM","Flash","EEPROM","FEPROM","EPROM","CDRAM","3DRAM","SDRAM","SGRAM","RDRAM","DDR","DDR2","DDR2 FB-DIMM","DDR3","FBD2","DDR4"]
        formFactor=["Unknown","Other","SIP","DIP","ZIP","SO","Proprietary","SIMM","DIMM","TSOP","PGA","RIMM","SODIMM","SRIMM","SMD","SSMP","QFP","TQFP","SOIC","LCC","PLCC","BGA","FPBGA","LGA","FB-DIMM"]
        info+="Speed:"+re.search("\d+",os.popen("wmic memorychip get speed").read())[0]+" MHz"
        info+="\nMemory Type:"+memorytipe[int(re.search("\d",os.popen("wmic memorychip get memorytype").read())[0])]
        info+="\nMemory Form Factor:"+formFactor[int(re.search("\d+",os.popen("wmic memorychip get formfactor").read())[0])]
        info+=re.sub('\w+=\W+\n|FormFactor.*|MemoryType.*|Speed.*','',os.popen("wmic memorychip list full").read())
        info=re.sub('\n\n','\n',info)
        info=re.sub('\n\n','\n',info)
    if(tipo=='processor'):
        cpu_status=['Unknown','CPU Enabled','CPU Disabled by User via BIOS Setup','CPU Disabled By BIOS (POST Error','CPU is Idle','Reserved','Reserved','Other']
        type=['','Other','Unknown','Central Processor','Math Processor','DSP Processor','Video Processor']
        status_info=['','Other','Unknown','Enabled','Disabled','Not Applicable']
        info+=re.sub('.*=\n\n','',os.popen("wmic cpu list full").read())
        info=re.sub('\n\n','\n',info)
        info=re.sub('\n\n','\n',info)
        info=re.sub("(?<=Availability=)\d+",availability[int(re.search("(?<=Availability=)\d+",info)[0])],info)
        info=re.sub("(?<=CpuStatus=)\d+",cpu_status[int(re.search("(?<=CpuStatus=)\d+",info)[0])],info)
        info=re.sub("(?<=ProcessorType=)\d+",type[int(re.search("(?<=ProcessorType=)\d+",info)[0])],info)
        info=re.sub("(?<=StatusInfo=)\d+",status_info[int(re.search("(?<=StatusInfo=)\d+",info)[0])],info)
    if(tipo=='so'):
        info=re.sub('.*=\n\n','',os.popen("wmic os get /all /format:list").read())
        info=re.sub('\n\n','\n',info)
        info=re.sub('\n\n','\n',info)
    if(tipo=='bios'):
        info+=re.sub('.*=\n\n','',os.popen("wmic bios get /all /format:list").read())
        info=re.sub('\n\n','\n',info)
        info=re.sub('\n\n','\n',info) 
        info=re.sub('\nListOfLanguages.*','',info) 
    if(tipo=='disk'):
        info+=re.sub('.*=\n\n','',os.popen("wmic diskdrive get /all /format:list").read())
        info=re.sub('\n\n','\n',info)
        info=re.sub('\n\n','\n',info) 
    showDetailInfo(info,tipo)
def onSelectedLstBox(tree,list,tipo):
    selection = tree.selection()
    if selection:
        index = int(selection[0][-2:],16)-1
        showDetailInfo(list[index],tipo)
def diagnosticarMemoria():
    os.popen("mdsched")
def diagnosticarDisco():
    os.system("start cmd /k chkdsk")
def diagnosticarRed():
    os.popen("msdt.exe -id NetworkDiagnosticsNetworkAdapter")
def actualizarInfoSystem():
    print('insane')
    sys.stdout.flush()
def saveSysInfo():
    global info,ez_tkn
    info+=ez_tkn
    try:
        file = filedialog.asksaveasfile(initialfile = 'SystemInfo.txt',defaultextension=".txt",filetypes=[("All Files","*.*"),("Text Documents","*.txt")])
        file.write(info)
        file.close()
        messagebox.showinfo('Guardar Info','Se guardo la informacion correctamente')
    except Exception as e:
        print(e)
def setBarraMenu(root):
    barraMenu=Menu(root)
    root.config(menu=barraMenu,width=2000,height=300)
    archivoMenu=Menu(barraMenu,tearoff=0)
    archivoMenu.add_command(label="Guardar Info",command=saveSysInfo)
    archivoMenu.add_separator()
    archivoMenu.add_command(label="Salir",command=lambda: Salir())
    archivoHerramientas=Menu(barraMenu,tearoff=0)
    archivoHerramientas.add_command(label="Diagnóstico de Memoria",command=diagnosticarMemoria)
    archivoHerramientas.add_command(label="Diagnóstico de Disco",command=diagnosticarDisco)
    archivoHerramientas.add_command(label="Diagnóstico de Red",command=diagnosticarRed)
    archivoAyuda=Menu(barraMenu,tearoff=0)
    archivoAyuda.add_command(label="Actualizar",command=actualizarInfoSystem)
    archivoAyuda.add_command(label="Acerca De",command=acercaDe)
    archivoAyuda.add_cascade(label="Desinstalar",command=lambda:desinstalar(root))
    barraMenu.add_cascade(label="Archivo",menu=archivoMenu)
    barraMenu.add_cascade(label="Herramientas",menu=archivoHerramientas)
    barraMenu.add_cascade(label="Ayuda",menu=archivoAyuda)
def mainGUI():
    global info,slots,list_mems,processor,adapters,list_nets,discos,list_disks,capacity,ez_tkn
    MLP_thread = threading.Thread(target=ImportAgentMLP, name='Hilo MLP')
    MLP_thread.start()
    loadingWindow('Iniciando Diganóstico MA')
    root=Tk()
    root.protocol("WM_DELETE_WINDOW", Salir)
    root.title("Informacion del Sistema")
    window_h = root.winfo_screenheight()
    window_w = root.winfo_screenwidth()
    w,h,x,y=window_w*0.65,window_h*0.55,window_w*0.17,window_h*0.20
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    root.tk.call('source', res_path+'Styles/forest-light.tcl')
    ttk.Style().theme_use('forest-light')
    setBarraMenu(root)
    root.iconbitmap(res_path+'icon.ico')
    memoria=re.sub('\s{2,}','',info[re.search("Memoria",info).start():re.search("Ubic",info).start()])
    so=str(re.search('(?<=sistema operativo:).*',info)[0]).strip().replace('Microsoft','MS')
    bios=str(re.sub('[a-z]+\s?','',(re.search('(?<=Versión del BIOS:\s).*',info)[0]))).strip().replace(',','\n').replace('.','\n')
    mainFrame=ttk.Frame(root)
    mainFrame.grid(row=0, column=0, sticky="news")
    frame1=ttk.LabelFrame(mainFrame,text="Memoria",style='TLabelframe')
    frame1.place(relx=0, rely=0,relheight=0.4,relwidth=0.33)
    frame2=ttk.LabelFrame(mainFrame,text="Procesador",style='TLabelframe')
    frame2.place(relx=0.33, rely=0,relheight=0.4,relwidth=0.33)
    frame3=ttk.LabelFrame(mainFrame,text="Adaptadores de Red",style='TLabelframe')
    frame3.place(relx=0.66 ,rely=0,relheight=0.4,relwidth=0.33)     
    frame4=ttk.LabelFrame(mainFrame,text="Almacenamiento",style='TLabelframe')
    frame4.place(relx=0, rely=0.4,relheight=0.4,relwidth=0.33)
    frame5=ttk.LabelFrame(mainFrame,text="SO",style='TLabelframe')
    frame5.place(relx=0.33, rely=0.4,relheight=0.4,relwidth=0.33)
    frame6=ttk.LabelFrame(mainFrame,text="BIOS",style='TLabelframe')
    frame6.place(relx=0.66, rely=0.4,relheight=0.4,relwidth=0.33)
    frame7=ttk.LabelFrame(mainFrame,text="Agentes",style='TLabelframe')
    frame7.place(relx=0, rely=0.8,relheight=0.2,relwidth=1)
    lblMemoria=ttk.Label(frame1,text=memoria,justify="center",font=('Arial',14))
    lblMemoria.place(relx=0, rely=0,relheight=0.6,relwidth=1)
    lblMemoria.config(anchor='center')
    listMems = ttk.Treeview(frame1, show="tree",height=2)
    for slot in slots:
        listMems.insert("", "end", text=slot) 
    listMems.place(relx=0, rely=0.6,relheight=0.4,relwidth=1)
    listMems.bind("<Double-1>", lambda event,list=list_mems:onSelectedLstBox(listMems,list,'memory'))
    lblProcesador=ttk.Label(frame2,text=processor,justify="center",width=6,font=('Arial',14))
    lblProcesador.place(relx=0, rely=0,relheight=0.5,relwidth=1)
    lblProcesador.config(anchor='center')
    listNets = ttk.Treeview(frame3, show="tree",height=4)
    for adapter in adapters:
        listNets.insert("", "end", text=adapter) 
    listNets.place(relx=0.05, rely=0.05,relheight=0.9,relwidth=0.9)
    listNets.bind("<Double-1>", lambda event,list=list_nets:onSelectedLstBox(listNets,list,'adapter'))
    lblCapacidad=ttk.Label(frame4,text=capacity,justify="center",font=('Arial',14))
    lblCapacidad.place(relx=0, rely=0,relheight=0.4,relwidth=1)
    lblCapacidad.config(anchor='center')
    listDisks = ttk.Treeview(frame4, show="tree",height=3)
    for disk in discos:
        listDisks.insert("", "end", text=disk) 
    listDisks.place(relx=0, rely=0.4,relheight=0.5,relwidth=1)
    listDisks.bind("<Double-1>", lambda event,list=list_disks:onSelectedLstBox(listDisks,list,'disk'))
    lblbios=ttk.Label(frame5,text=so,justify="center",font=('Arial',14))
    lblbios.place(relx=0, rely=0,relheight=0.5,relwidth=1)
    lblbios.config(anchor='center')
    lblSO=ttk.Label(frame6,text=bios,justify="center",font=('Arial',14))
    lblSO.place(relx=0, rely=0,relheight=0.6,relwidth=1)
    lblSO.config(anchor='center')
    lblAgentYT=ttk.Label(frame7,text='Agente YT No Disponible',justify="center",font=('Sans',18,'bold'))
    lblAgentYT.place(relx=0, rely=0,relheight=1,relwidth=1)
    lblAgentYT.config(anchor='center')
    btnProcesador=ttk.Button(frame2,text="Detalles",command=lambda:detalles(processor,"processor"))
    btnProcesador.place(relx=0.1, rely=0.6,relheight=0.2,relwidth=0.8)
    btnSO=ttk.Button(frame5,text="Detalles",command=lambda:detalles(so,"so"))
    btnSO.place(relx=0.1, rely=0.6,relheight=0.2,relwidth=0.8)
    btnbios=ttk.Button(frame6,text="Detalles",command=lambda:detalles(bios,"bios"))
    btnbios.place(relx=0.1, rely=0.65,relheight=0.2,relwidth=0.8)
    global agentYT_available,salir
    agentYT_available=salir=False
    while 1:
        root.update()
        if not (MLP_thread.is_alive() or agentYT_available):
            agentYT_available=True
            lblAgentYT.config(text="+Agente YT Disponible")
        if salir:
            break   
    root.destroy()       
def loadingWindow(msj,*args):
    operation=msj.split()[0]
    loading_window = Tk() if not args else Toplevel()
    loading_window.title(operation)
    window_h = loading_window.winfo_screenheight()
    window_w = loading_window.winfo_screenwidth()
    w_window,h_window,x,y=window_w//5,window_h*2//10,window_w*0.41,window_h//4
    loading_window.geometry('%dx%d+%d+%d' % (w_window, h_window, x, y))
    img=ImageTk.PhotoImage(Image.open(res_path+"icon.png").resize((70, 70)))
    label_img=ttk.Label(loading_window,image=img)
    label_img.place(x=w_window/50, y=h_window/100, width=w_window/2,height=h_window/2)
    lbl=ttk.Label(loading_window,text=msj+'...',font=('Arial',12))
    lbl.place(x=(w_window*3/10), y=h_window/100,height=h_window/2)
    progressbar = ttk.Progressbar(loading_window,mode="indeterminate")
    progressbar.place(x=(w_window-w_window*0.9)/2, y=h_window*0.6,height=h_window/6,width=w_window*0.9)
    progressbar.start()
    loading_window.iconbitmap(res_path+'icon.ico')
    hilos=[None]
    if operation=="Iniciando":
        hilos*=2
        functions=[getToken,getSysInfo]
        for i in range(2):
            hilos[i] = threading.Thread(target=functions[i], name=f'Hilo {i}')
            hilos[i].start()
    else: 
        hilos[0] = threading.Thread(target=agent_YT, name='Hilo Busqueda',args=(args[0]+' '+args[1],args[2]))
        hilos[0].start()
    while any([hilo.is_alive() for hilo in hilos]):
        loading_window.update()
    loading_window.destroy()      
def main():
    global cipher_suite,uninstall
    cipher_suite = Fernet("PZqKn67ePhp5UwcfInFJYUELtt-LFE8y0QANdHxBnCw=")
    uninstall=False 
    mainGUI()      
if __name__ == "__main__":       
    main() 