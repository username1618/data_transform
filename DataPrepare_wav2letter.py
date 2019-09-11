# -*- coding: utf-8 -*-
import sys
import os, shutil
import pandas as pd
from math import ceil
from random import shuffle 

""" 
    Сoздаем файл с токенами - наименьшими составными частями языка (фонемы, графемы, ..)
    # tokens.txt
    
    Для каждого звукового файла создаем файл с id.
    # 000004076.id
    # file_id	4076
    
    Для каждого звукового файла создаем файл с текстовой расшифровкой фрагмента
    # 000004076.wrd
    # rub them through a tammy and mix

    Для каждого звукового файла создаем файл с токенами (фонемы, графемы, ..) [Для пробела нужен отдельный символ. Символ пропуска необходим для работы CTC]
    # 000004076.tkn
    # r u b | t h e m | t h r o u g h | a | t a m m y | a n d | m i x
    
    Создаем файл с лексиконом - файл со списком уникальных слов и их представлением в виде токенов
    # lexicon.txt
    # a a |
    # able  a b l e |
"""


# Создаем текстовое имя для файла из числа (дополняем нулями до указанной длины)
def num2str(num,length=9):
    return str(num).rjust(length,'0')

# Оставляем в пути только название файла
def path2fname(path):
    return path[path.replace('\\','/').rfind('/')+1:]

# Оставляем в пути название файла с расширением и предыдущий каталог
def path2ffname(path):
    path=path.split('/')
    return os.path.join(path[-2],path[-1])

# Создаем файл с id
def creat_ind(folder, name, indx):
    with open(os.path.join(folder, name+'.id'), 'tw', encoding='utf-8') as f:
        f.write('file_id	'+str(indx))

# Создаем файл с wrd (текстовая расшифровка)
def creat_wrd(folder, name, text):
    with open(os.path.join(folder, name+'.wrd'), 'tw', encoding='utf-8') as f:
        f.write(text)

# Представляем текст в виде строки из токенов
def make_tkn(text):
    return " ".join(x for x in list(text.replace(' ', '|')))

# Создаем файл с tkn (файл с токенами - наименьшими составными частями языка)
def creat_tkn(folder, name, text):
    with open(os.path.join(folder, name+'.tkn'), 'tw', encoding='utf-8') as f:
        f.write(text)
    
# Создаем файл с лексиконом (файл со списком уникальных слов и их представлением в виде токенов)
def creat_lexicon(folder, name, train, dev, test):
    lexicon=pd.concat([train["transcript"], dev["transcript"], test["transcript"]]) #.unique()
    lexicon_out=[]
    for elm in lexicon:
        row_txt_uniq = list(set(elm.split(' '))) #быстрый отбор уникальных значений
        lexicon_out.extend(row_txt_uniq)
    lexicon_out=list(set(lexicon_out)) 
    lexicon_out=list(map(lambda x:x+' '+' '.join(y for y in x.replace(' ', '|')) +' |\n',lexicon_out))
    print('Writing lexicon file...')    
    with open(os.path.join(folder, name+'.txt'), 'tw', encoding='utf-8') as f:
        f.writelines(lexicon_out[1:]) # не записываем первую строчку, в которой находится только пробел
    
# Переименовываем файлы
def renameANDmove_audiofile(folder_in, folder_out, name, path_fromdata):
  try:
      shutil.move(os.path.join( folder_in, path2ffname(path_fromdata) ), # парсим каталог и файл, и соединяем с путем к папке с корпусом данных
                  os.path.join( folder_out,  name+path_fromdata[-4:] ))
      return True
  except Exception as e:
      print('\nException: '+ str(e)+'\n')   
      return False

# Подготавливаем облегченную версию датасета (из уже обработанного)
def creatLightDataset(folder_in, folder_out, audio_format='wav', percent_begin=0, percent_end=0.1, shuf=False, log=False):
    def getListFromFolder(Path):
        return [fn[0:-4] for fn in os.listdir(Path) if fn[-3:]=='wrd']

    for ds_type in ['train','dev','test']:
        if log:
            print('Start a directory:',ds_type)
        if not os.path.exists(os.path.join(folder_out, ds_type)):
            os.makedirs(os.path.join(folder_out, ds_type))
        
        # Собираем список из файлов
        ds = getListFromFolder(os.path.join(folder_in, ds_type))
        
        # Перемешиваем список с файлами
        if shuf:
            shuffle(ds)
            
        # Устанавливаем новый размер корпуса и копируем отобранные файлы в новую директорию
        limit_begin = ceil(len(ds)*percent_begin)
        limit_end = ceil(len(ds)*percent_end)
        ds_lite = ds[limit_begin:limit_end]
        
        lendsl=len(ds_lite)
        for i,f in enumerate(ds_lite):
            if log:
                print('\rProgress: %1f%% ' % ((i+1)/lendsl*100), end='')
            fname = num2str(i)
            shutil.copy(os.path.join(folder_in, ds_type, f+'.'+audio_format), os.path.join(folder_out, ds_type, fname+'.'+audio_format))
            shutil.copy(os.path.join(folder_in, ds_type, f+'.id'),  os.path.join(folder_out, ds_type, fname+'.id' ))
            shutil.copy(os.path.join(folder_in, ds_type, f+'.wrd'), os.path.join(folder_out, ds_type, fname+'.wrd'))
            shutil.copy(os.path.join(folder_in, ds_type, f+'.tkn'), os.path.join(folder_out, ds_type, fname+'.tkn'))
        print('New "',ds_type,'" audio files count = ', lendsl)




if __name__ == "__main__":
    log=False
    creatLDonly=False
    lex_only=False
    percent_begin=0  # [0..1]
    percent_end=1    # [0..1]
    minlength=20
    maxlength=500

    # Считываем из командной строки пути к папкам    
    for i, param in enumerate(sys.argv):
            if (param == "--in" or  param == "-i"):
                in_folder = sys.argv[i+1] # Путь к папке с корпусом данных (к папкам с train, dev, test)
            elif (param == "--out" or  param == "-o"):
                out_folder =  sys.argv[i+1] # Путь к папке с выходными данным
                out_f = out_folder
            elif (param == "--train" or  param == "-tr"):
                train_csv =  sys.argv[i+1] # Путь к тренировочным данным (csv)
            elif (param == "--test" or  param == "-te"):
                test_csv =  sys.argv[i+1] # Путь к тестовым данным (csv)
            elif (param == "--dev" or  param == "-dv"):
                dev_csv =  sys.argv[i+1] # Путь к проверочным данным (csv)
            elif (param == "--log" or  param == "-l"):
                log =  True # выводить логи на экран
            elif (param == "--lexfold" or  param == "-lf"):
                lex_folder =  sys.argv[i+1] # Путь к выходному файлу с лексиконом (txt)
            elif (param == "--creatLD" or  param == "-cld"):
                creatLDonly =  True # Создаем только облегченный датасет
            elif (param == "--beginpercent" or  param == "-bpct"):
                percent_begin =  float(sys.argv[i+1]) # Процент файлов в итоговом датасете от числа входных данных [0..1]
            elif (param == "--endpercent" or  param == "-epct"): #                                                           =>  [percent_begin..percent_end]
                percent_end =  float(sys.argv[i+1]) # Процент файлов в итоговом датасете от числа входных данных [0..1]
            elif (param == "--minlength" or  param == "-mnlen"):
                minlength =  int(sys.argv[i+1]) # Минимальная длина строки с текстом            
            elif (param == "--maxlength" or  param == "-mxlen"):
                maxlength =  int(sys.argv[i+1]) # Минимальная длина строки с текстом   

    if not creatLDonly:
        # Создаем папку с выходными данными
        if not os.path.exists(out_folder):
            os.makedirs(out_folder)
       
      
        # Загружаем данные из CSV
        if log:
            print('\nLoading files from folder: '+in_folder)
        train = pd.read_csv(os.path.join(in_folder,train_csv), sep=',') #, header=None) 
        test = pd.read_csv(os.path.join(in_folder,test_csv), sep=',') 
        dev = pd.read_csv(os.path.join(in_folder,dev_csv), sep=',') 
        
        # Проверяем длину текстового описания каждого файла
        print('\nChecking words length..')
        dev["transcript_len"]=dev["transcript"].str.len() # добавляем столбец с количеством символов в тексте 
        dev=dev.loc[(dev["transcript_len"] >= minlength) & (dev["transcript_len"] <= maxlength)] # оставляем записи удовлетворяющие граничным значениям (min/max)
        dev=dev.drop(columns=['transcript_len'])
        test["transcript_len"]=test["transcript"].str.len()
        test=test.loc[(test["transcript_len"] >= minlength) & (test["transcript_len"] <= maxlength)]
        test=test.drop(columns=['transcript_len'])    
        train["transcript_len"]=train["transcript"].str.len()
        train=train.loc[(train["transcript_len"] >= minlength) & (train["transcript_len"] <= maxlength)]
        train=train.drop(columns=['transcript_len'])    
        
           
#        # Устанавливаем новый размер корпуса
#        limit = ceil(len(dev)*percent_end)
#        dev = dev[0:limit]
#        
#        limit = ceil(len(test)*percent_end)
#        test = test[0:limit]
#        
#        limit = ceil(len(train)*percent_end)
#        train = train[0:limit]   
        
        
        # Всего файлов в корпусе и размерность этого количества
        data_count=len(dev)+len(train)+len(test)
        data_len=len(str(data_count))
          
    
        # Создаем файл с лексиконом
        print('Creating lexicon file..')
        creat_lexicon(lex_folder,'lexicon',train,dev,test)
       
         # Индекс для нумерации выходных данных
        glob_indx=0 
        glbind=0
        # Подготавливаем данные
        for i, dataset in enumerate([train, dev, test]): # Цикл по типам dataset'ов
            if i == 0:
                out_folder=os.path.join(out_f,'train')
            else:
                out_folder=os.path.join(out_f,'dev') if i == 1 else os.path.join(out_f,'test')
            
            if log:
                print('\nStart prepare a folder: '+out_folder)
     
            glbind=glbind+glob_indx
            glob_indx=0 
            # Цикл по строкам i-го dataset'а
            for element in dataset.iterrows(): 
                # Имя для выходных файлов
                fname = num2str(glob_indx)  # ,data_count)
                # Переименовываем файл с аудио и помещаем его в папку с выходными данными  
                move_status = renameANDmove_audiofile(in_folder,out_folder, fname, element[1]['wav_filename'])
                
                if move_status: # Если успешно переместили аудиофайл, то создаем доп. файлы(id,wrd,tkn)
                    # Создаем файл id    
                    creat_ind(out_folder, fname, glob_indx)
                    # Создаем файл wrd  
                    creat_wrd(out_folder, fname, element[1]['transcript'])
                    # Создаем файл tkn  
                    creat_tkn(out_folder, fname, make_tkn(element[1]['transcript']))  # make_tkn представляет текст в виде строки из токенов  
                    glob_indx+=1
                    
                if log:
                    print('\rProgress: %1f%% ' % ((glob_indx+glbind)/data_count*100), end='')
                    
    # Создаем облегченный датасет из уже имеющихся данных (копируем файлы)            
    else:
        if log:
            print('Start ctreating light dataset..')
        creatLightDataset(in_folder, out_folder, 'wav', percent_begin, percent_end, False, log)

