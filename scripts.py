import re, os, json, codecs, math

def write_data (path, data): #Запись в json-файл
    json_data = json.dumps(data, ensure_ascii=False, indent=1)  
    json_file = codecs.open(path, 'w', 'utf-8')
    json_file.write (json_data)
    json_file.close()
def read_data (path): #Чтение из json-файла
    data_file = codecs.open(path, 'r', 'utf-8')
    data = json.load(data_file)
    data_file.close()
    return data


#Создание частотных списков финитных глаголов и существительных 
def get_VN_freq_lists(inpath, min_V, min_N):  
    re_is_finite = re.compile("^Vmi")
    index = 0
    freq_dict_V = {}
    freq_dict_N = {}
    for k in os.walk(inpath):
        if k[2]:
            for j in k[2]:
                file_path = k[0] + os.sep + j
                file = open(file_path, "r", encoding="utf-8")
                for i in file:
                    parts = i.split()
                    if parts and len(parts) == 8:
                        index += 1
                        if re_is_finite.search(parts[5]):
                            if parts[3] in freq_dict_V:
                                freq_dict_V[parts[3]] += 1
                            else:
                                freq_dict_V.update({parts[3]:1})
                        elif parts[4] == "N":
                            if parts[3] in freq_dict_N:
                                freq_dict_N[parts[3]] += 1
                            else:
                                freq_dict_N.update({parts[3]:1})
                file.close()
                print("Обработан файл ", file_path)
                print("Текущий объем корпуса ", index, " словоформ.")
    print("Все файлы обработаны. Объем корпуса ", index, " словоформ.")
    print("Начинается запись результатов в файлы.")

    new_dict = {}
    for i in freq_dict_V:
        if freq_dict_V[i] >= min_V:
            new_dict.update({i:freq_dict_V[i]})
    write_data(inpath + os.sep + "V_freq_list_" + str(min_V) + ".json", new_dict)
    print("Результаты по глаголам записаны.")

    new_dict = {}
    for i in freq_dict_N:
        if freq_dict_N[i] >= min_N:
            new_dict.update({i:freq_dict_N[i]})
    write_data(inpath + os.sep + "N_freq_list_" + str(min_N) + ".json", new_dict)
    print("Результаты по существительным записаны.")
    print("Конец")


#Извлечение коллокаций из базы оконным методом
def get_database_collocs_window(inpath, verb_freq_path, min_V, noun_freq_path, min_N):
    re_is_finite = re.compile("^Vmi")
    re_is_word = re.compile("[А-Яа-я]")
    window_collocs = {}
    index = 0
    current_num = 0
    current_sent = []
    verb_freq = read_data(verb_freq_path)
    noun_freq = read_data(noun_freq_path)
    for k in os.walk(inpath):
        if k[2]:
            for j in k[2]:
                file_path = k[0] + os.sep + j
                file = open(file_path, "r", encoding="utf-8")
                verb_index = []
                noun_index = []
                word_index = -1
                for i in file:
                    parts = i.split()
                    if not parts:
                        continue
                    try:
                        flag = int(parts[0])
                    except:
                        continue
                    if not re_is_word.search(parts[2]):
                        continue
                    index += 1
                    if parts[0] == current_num:
                        word_index += 1
                        current_sent.append(parts)
                        if re_is_finite.search(parts[5]) and parts[3] in verb_freq:
                            verb_index.append(len(current_sent) - 1)
                        elif parts[4] == "N" and parts[3] in noun_freq:
                            noun_index.append(len(current_sent) - 1)
                                
                    elif parts[0] != current_num and current_sent:
                        if verb_index and noun_index:
                            window_collocs = get_sent_bow(current_sent, verb_index, noun_index, window_collocs, verb_freq)
                        verb_index = []
                        noun_index = []                                     
                        current_sent = [parts]
                        current_num = parts[0]
                        if re_is_finite.search(parts[5]):
                            verb_index.append(len(current_sent) - 1)
                        elif parts[4] == "N":
                            noun_index.append(len(current_sent) - 1)#
                                
                    else:
                        verb_index = []
                        noun_index = []
                        current_sent = [parts]
                        current_num = parts[0]
                        if re_is_finite.search(parts[5]):
                            verb_index.append(len(current_sent) - 1)#int(parts[1]))
                        elif parts[4] == "N":
                            noun_index.append(len(current_sent) - 1)#int(parts[1]))

                file.close()
                print("Обработан файл ", file_path)
                print("Текущий объем корпуса ", index, " словоформ.")
    
    print("Все файлы обработаны. Объем корпуса ", index, " словоформ.")
    print("Начинается запись данных в файл.")

    bow_file = open(inpath + os.sep + "collocs_bow.txt", "a", encoding = "utf-8")
    for i in window_collocs:
        word = i.split("\t")[0]
        new_string = "\t".join([i, str(window_collocs[i]), str(verb_freq[word])])
        new_string += "\n"
        bow_file.write(new_string)
    bow_file.close()
    print("Запись в файл закончена.")
    print("Конец")

#Извлечение коллокаций из предложения оконным методом        
def get_sent_bow(current_sent, verb_index, noun_index, window_collocs, verb_freq): 
    collocs = []
    for i in verb_index:
        for j in noun_index:
            if i - j >= -5 and i - j <= 5 and current_sent[i][3] in verb_freq:
                collocs.append("\t".join([current_sent[i][3], "NULL", current_sent[j][3], current_sent[j][5][4]]))
    for i in collocs:
        if i in window_collocs:
            window_collocs[i] += 1
        else:
            window_collocs.update({i:1})
    return window_collocs


#Фильтр по частоте
def freq_filter(inpath, outpath, freq_list, min_freq, pos):
    a = open(inpath, "r", encoding="utf-8")
    b = open(outpath, "a", encoding="utf-8")
    index = 0
    for i in a:
        parts = i.split()
        if parts[pos] in freq_list:
            if freq_list[parts[pos]] >= min_freq:
                b.write(i)
    a.close()
    b.close()
    
#Перевод файла в другую схему представления
def change_desr(inpath, outpath, verb_freq, noun_freq):
    a = open(inpath, "r", encoding="utf-8")
    b = open(outpath, "a", encoding="utf-8")
    collocs = {}
    bad_words = []
    index = 0
    for i in a:
        try:
            parts = i.split()
            res = "\t".join([parts[0], parts[5], parts[2], str(noun_freq[parts[2]]), parts[3]])
            if res in collocs:
                collocs[res] += int(parts[4])
            else:
                collocs.update({res:int(parts[4])})
        except:
            bad_words.append(parts[2])
    for i in collocs:
        b.write(i + "\t" + str(collocs[i]) + "\n")
        index += 1
    a.close()
    b.close()
    bad_words = list(set(bad_words))
    print("По частоте отсеяно ", len(bad_words), " слов")
    print(index)

#Создание частотного списка падежей
def case_freq(inpath):
    res = {}
    a = open(inpath, "r", encoding="utf-8")
    for i in a:
        parts = i.split()
        if parts[4] in res:
            res[parts[4]] += 1
        else:
            res.update({parts[4]:1})
    return res

#Создание частотного списка сочетаний падежа и глагола
def verb_case_freq(inpath):
    res = {}
    a = open(inpath, "r", encoding="utf-8")
    for i in a:
        parts = i.split()
        if parts[0] in res:
            if parts[4] in res[parts[0]]:
                res[parts[0]][parts[4]] += 1
            else:
                res[parts[0]].update({parts[4]:1})
        else:
            res.update({parts[0]:{parts[4]:1}})
    return res

#Вычисление Pointwise Mutual Information
def calc_pmi(x_freq, y_freq, xy_freq, normalizator):
    return log2((xy_freq/normalizator)/((x_freq/normalizator) * (y_freq/normalizator)))
#Вычисление LogDice
def calc_logdice(x_freq, y_freq, xy_freq):
    return 14 + log2(calc_dice(x_freq, y_freq, xy_freq))
#Вычисление критерия Дайса
def calc_dice(x_freq, y_freq, xy_freq):
    return (2 * xy_freq) / (x_freq + y_freq)

#Вычисление статистических критериев для коллокаций из файла
def calc_file_measures(inpath, outpath, normalizator_c, normalizator_cv):
    file = open(inpath, "r", encoding="utf-8")
    out_file = open(outpath, "a", encoding="utf-8")
    for i in file:
        parts = i.split()
        x = normalizator_cv[parts[0]][parts[4]]
        y = N_freq_data[parts[2]]
        z = int(parts[5])
        logdice_freq = calc_logdice(x, y, z)
        pmi_freq = calc_pmi(int(parts[1]), int(parts[3]), int(parts[5]), normalizator_c[parts[4]])
        
        parts.append(str(pmi_freq))
        parts.append(str(logdice_freq))
        res = "\t".join(parts)
        res += "\n"
        out_file.write(res)


#Ключ для сортировки по PMI
def sortByPMI(parts):
    return (float(parts[6]))
#Ключ для сортировки по LogDice
def sortByDice(parts):
    return (float(parts[7]))

#Сортировка коллокаций из файлов по статистическим результатам
def sort_collocs(inpath, outpathPMI, outpathDice):
    a = open(inpath, "r", encoding="utf-8")
    b = open(outpathPMI, "a", encoding="utf-8")
    c = open(outpathDice, "a", encoding="utf-8")
    collocs = []
    for i in a:
        parts = i.split()
        collocs.append(parts)
    a.close()
    print("Файл прочитан.")
    collocs.sort(key=sortByPMI)
    collocs.reverse()
    for i in collocs:
        res = "\t".join(i)
        res += "\n"
        b.write(res)
    b.close()
    collocs.sort(key=sortByDice)
    collocs.reverse()
    for i in collocs:
        res = "\t".join(i)
        res += "\n"
        c.write(res)
    c.close()

#Выделение из списка коллокаций со вхождениями больше определенного порога
def get_freq_collocs(inpath, num):
    a = open(inpath, "r", encoding="utf-8")
    path_parts = inpath.split(".")
    outpath = ".".join([path_parts[0] + "_min" + str(num), path_parts[1]])
    f2 = open(outpath, "a", encoding="utf-8")

    for i in a:
        parts = i.split()
        if int(parts[5]) > num:
            f2.write(i)
        else:
            continue
    a.close()
    f2.close()

#Получение топ-N коллокаций списка
def get_topN(path, n):
    res = []
    index = 0
    file = open(path, "r", encoding="utf-8")
    new_path = path.split(".")
    new_path = new_path[0] + "_top" + str(n) + "." + new_path[1]
    new_file = open(new_path, "a", encoding="utf-8")
    for i in file:
        index += 1
        if index <= n:
            new_file.write(i)
        else:
            break
    file.close()
    new_file.close()

#Создание сравнительных списков выделенных существительных для глаголов+падежей для двух методов
def evaluate_pairs(path1, path2, outpath):
    verb_list = {}
    file = open(path1, "r", encoding="utf-8")
    for i in file:
        parts = i.split()
        if parts[0] in verb_list:
            if parts[4] in verb_list[parts[0]]:
                if parts[2] not in verb_list[parts[0]][parts[4]][1]:
                    verb_list[parts[0]][parts[4]][1].append(parts[2])
            else:
                verb_list[parts[0]].update({parts[4]:{1:[parts[2]], 2:[]}})
        else:
            verb_list.update({parts[0]:{parts[4]:{1:[parts[2]], 2:[]}}})
    file.close()

    file = open(path2, "r", encoding="utf-8")
    for i in file:
        parts = i.split()
        if parts[0] in verb_list:
            if parts[4] in verb_list[parts[0]]:
                if parts[2] not in verb_list[parts[0]][parts[4]][2]:
                    verb_list[parts[0]][parts[4]][2].append(parts[2])
            else:
                verb_list[parts[0]].update({parts[4]:{1:[],2:[parts[2]]}})
        else:
            verb_list.update({parts[0]:{parts[4]:{1:[], 2:[parts[2]]}}})
    file.close()
    file = open(outpath, "a", encoding="utf-8")
    full_result = []
    for i in verb_list:
        result = ""
        result += i
        for j in verb_list[i]:
            fix_result1 = result
            result += "," + j
            nouns = []
            for k in verb_list[i][j]:
                nouns.append(verb_list[i][j][k])
                result += ","
                result += " ".join(sorted(verb_list[i][j][k]))
            add_data = calc_eval_data(nouns)
            add_data = ",".join(add_data)
            result = result + "," + add_data + "\n"
            full_result.append(result)
            result = fix_result1
    for i in full_result:
        file.write(i)
    file.close()


#Подсчет параметров для сравнения результатов относительно коллокаций, выделенных синтаксическим методом
def calc_eval_data(nouns):
    nouns1 = set(nouns[0])
    first = len(nouns1)
    nouns2 = set(nouns[1])
    second = len(nouns2)
    only_first = sorted(list(nouns1 - nouns2))
    only_second = sorted(list(nouns2 - nouns1))
    TP = len(nouns1 & nouns2)
    FP = len(only_second)
    FN  = len(only_first)
    if TP > 0:
        precision = TP/(TP+FP)
        recall = TP/(TP+FN)
        fmeasure = 2*(precision*recall)/(precision + recall)
    else:
        precision = -1
        recall = -1
        fmeasure = -1
    only_first = " ".join(only_first)
    only_second = " ".join(only_second)
    return [only_first, str(first), only_second, str(second), str(TP), str(FN), str(FP), str(precision), str(recall), str(fmeasure)]


#Сравнение количества выделенных существитеьных для глаголов двумя методами
def compare_evaluation_res(path, first, second):
    a = open(path, "r", encoding="utf-8")
    a1 = open(first, "a", encoding="utf-8")
    a2 = open(second, "a", encoding="utf-8")
    index1 = 0
    index2 = 0
    index_eq = 0
    for i in a:
        parts = i.split(",")
        first = int(parts[5])
        second = int(parts[7])
        if first > second:
            a1.write(i)
            index1 += 1
        elif second > first:
            a2.write(i)
            index2 += 1
        else:
            index_eq += 1
    a.close()
    a1.close()
    a2.close()
    print("Синтаксическим методом выделено больше для ", index1, " глаголов")
    print("Линейным методом выделено больше для ", index2, " глаголов")
    print("Количество коллокаций равны для ", index_eq, " глаголов")
