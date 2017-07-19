# -*- coding: utf-8 -*-  
import MySQLdb
import os  
import sys
reload(sys)
sys.setdefaultencoding('utf-8')   
import pyltp
from pyltp import SentenceSplitter
from pyltp import Segmentor
from pyltp import Postagger
from pyltp import NamedEntityRecognizer
from pyltp import Parser
from pyltp import SementicRoleLabeller
import jieba
import jieba.analyse
import operator
import json
import pynlpir
import gensim
model = gensim.models.Word2Vec.load("wiki.zh.text.model")

conn= MySQLdb.connect(
        host='localhost',
        port = 3306,
        user='root',
        passwd='1',
        db ='liverpool_player_info',
        charset="utf8"
        )
cur = conn.cursor()



def NamedRecognize(question,final_div_list,postags):
    recognizer=NamedEntityRecognizer()
    recognizer.load('/home/sherry/ltp/ltp_data/ner.model')
    netags=recognizer.recognize(final_div_list,postags)
    #print '|'.join(netags)
    #print '|'.join(postags)
    recognizer.release()
    pynlpir.open()
    key_words_nlpir=pynlpir.get_key_words(question,weighted=True)
    pynlpir.close()
    
    key_words=[]
    '''
    for i in range(len(netags)):
        if netags[i] != 'O' or postags[i]=='nh' or postags[i]=='ns':
            key_words.append(final_div_list[i])
    
    
    if len(key_words)>0:
        for key_word in key_words: 
            print key_word
    '''
    
    if len(key_words_nlpir)>0:
        for key_word in key_words_nlpir: 
            if key_word[1]>=1:
                key_words.append(key_word[0].encode('utf-8'))
                #print key_word[0]
    return key_words




def SearchRelateNews(key_words):

    title_invert_index=[]
    content_invert_index=[]

    root = os.getcwd() 
    
    #----------------------------------------读倒排索引-----------------------------------------#
    file_object=open(root+'/title_invert_index.txt','r')
    s=file_object.read().split('\n')[:-1]
    for line in s:
        key_word = line.split('|')[0]
        #print key_word
        index_num = line.split('|')[1][1:-1]
        #print index_num
        index_num_final=[]
        if index_num!='':
            if ',' in index_num:
                index_num=index_num.split(',')
                for i in range(len(index_num)):
                    index_num_final.append(int(index_num[i]))
            else:
                index_num_final.append(int(index_num))
        #print index_num_final
        title_invert_index.append([key_word,index_num_final])
    file_object.close()


    file_object=open(root+'/content_invert_index.txt','r')
    s=file_object.read().split('\n')[:-1]
    for line in s:
        key_word = line.split('|')[0]
        #print key_word
        index_num = line.split('|')[1][1:-1]
       
        index_num_final=[]
        if index_num!='':
            index_num=index_num.split(')')[:-1]
           
            for i in range(len(index_num)):
                 if i ==0:
                     index_num_final.append((int(index_num[i].strip('(').split(',')[0]),int(index_num[i].strip('(').split(',')[1])))
                 else:
                     index_num_final.append((int(index_num[i].strip(', (').split(',')[0]),int(index_num[i].strip(', (').split(',')[1].strip())))
        #print index_num_final
        content_invert_index.append([key_word,index_num_final])
    file_object.close()
    

    #----------------------------获取可能包含问题答案的的文章编号--------------------------------------------------------#
    possible_title_index=[]
    possible_content_index=[]
    for word in key_words:
        for i in range(len(title_invert_index)):
            if key_word_simi(word,title_invert_index[i][0]) and title_invert_index[i][1]!=[]:
                for j in range(len(title_invert_index[i][1])):
                    possible_title_index.append(title_invert_index[i][1][j])
     
        for i in range(len(title_invert_index)):
            if key_word_simi(word,content_invert_index[i][0]) and content_invert_index[i][1]!=[]:
                for j in range(len(content_invert_index[i][1])):
                    possible_content_index.append(content_invert_index[i][1][j][0])
    
    possible_title_index.extend(possible_content_index)
    possible_title_index.sort()
    #print possible_title_index
    if len(possible_title_index)==0:
        answer = '找不到'
        return answer

    elif len(possible_title_index)==1:
        possible_article_index=possible_title_index

    else:
        possible_article_score={}
        count=1
        for i in range(1,len(possible_title_index)):
            if possible_title_index[i]!=possible_title_index[i-1]:
                possible_article_score[possible_title_index[i-1]]=count
                count=1
            else:
                count=count+1
        possible_article_score[possible_title_index[i]]=count
        #print possible_article_score
        possible_article_score=sorted(possible_article_score.items(), key=lambda item:item[1], reverse=True)
        #print possible_article_score

        possible_article_index=[]
        if len(possible_article_score)>3:
            for i in range(3):
                possible_article_index.append(possible_article_score[i][0])
        else:
            for i in range(len(possible_article_score)):
                possible_article_index.append(possible_article_score[i][0])
    #print possible_article_index
    
    #-----------------------------------在可能包含答案的文章中寻找最有可能的答句-----------------------------#

    info_total = []
    filename = 'liverpool.json'
    for line in open(filename, 'r'):
        info_total.append(json.loads(line))

    content_list=[]
    for info_ in info_total:
        list_detail=[]
        for info_detail in info_['content']:
            
            sentenses = info_detail.encode('utf-8').split('\xe3\x80\x82')
            
            for sentense in sentenses:
                if sentense!='':
                    #print sentense
                    list_detail.append(name_based_sag(sentense.strip())[1])
                    #print '|'.join(name_based_sag(sentense.strip())[1])            
        content_list.append(list_detail)


    possible_answer_list=[]
    for index in possible_article_index:
        for i in range(len(content_list[index])):
             possible_answer_list.append(''.join(content_list[index][i]))
             #print ''.join(content_list[index][i])

    answer_score=[]
    for i in range(len(possible_answer_list)):
         count=0
         for word in key_words:
             if word.decode('utf-8') in model:
                 possible_answer_sag = name_based_sag(possible_answer_list[i])[1]
                 for sag in possible_answer_sag:
                      if sag.decode('utf-8') in model:
                          if key_word_simi(sag,word):
                              count=count+1
                              break
             else:
                 if word in possible_answer_list[i]:
                    count=count+1
         answer_score.append(count)
    #print answer_score
    max_score_index=[]
    for i in range(len(answer_score)):
        if answer_score[i]==max(answer_score):
            max_score_index.append(i)
    
    if max(answer_score)>=2:
        answer=''
        #answer_list=[]
        for i in max_score_index:
            if '\xc2\xa0' in possible_answer_list[i]:
                temp_answer=possible_answer_list[i].split('\xc2\xa0')[1]
            elif ' ' in possible_answer_list[i]:
                temp_answer=possible_answer_list[i].split(' ')[1]
            else:
                temp_answer=possible_answer_list[i]
            answer += temp_answer+'，'
            #answer_list.append(possible_answer_list[i])
        #print answer
        answer=answer[:-3]    
        answer = delete_redundance(answer)
    else:
        answer = '找不到'
    return answer  



def key_word_simi(stra,strb):
    if stra.decode('utf-8') in model and strb.decode('utf-8') in model:
        simi = model.similarity(stra.decode('utf-8'),strb.decode('utf-8'))
        if simi>0.6:
            return True
        else:
            return False
    else:
        if stra==strb:
            return True
        else:
            return False




def simi_sentence(sent1, sent2):
    if sent1==sent2:
       return True
    else:
       return False







def name_based_sag(question):
    name_keys=[]
    name_appear =[]
    name_count =0
    root = os.getcwd()
    path = os.listdir(root+'/'+'name')
    for line in path:
        strr = root +'/'+ 'name' +'/'+line
        file_object=open(strr,'r')
        s=file_object.read()
        name_keys.append(s)
        file_object.close()
    #print name_keys
    exist_name = []
    len_exist_name=len(exist_name)
    for keys in name_keys:
        pos=question.find(keys)
        if (pos != -1):
            exist_name_flag=0
            for i in range(len_exist_name):
                if exist_name[i]==keys:
                    exist_name_flag =1
                    break
            if exist_name_flag ==0:
                name_count = name_count+1
                name_appear.append([keys,pos])
                exist_name.append(keys)
            
            
    if len(name_appear)==0:
       flag_name = 0
    else:
       flag_name = name_count
    
    #print flag_name
    
    if flag_name !=0:
        name_appear.sort(key=operator.itemgetter(1))
        #print name_appear
        readyTodiv = question
        ori_div_list=[]
        for names in name_appear:
            ori_div = readyTodiv.split(names[0])
            if len(ori_div)>2:
                new_ori_div=[]
                temp_count = len(ori_div)
                temp_combine = ''
                for i in range(1,temp_count-1):
                    temp_combine = temp_combine+ori_div[i]+names[0]
                temp_combine = temp_combine+ ori_div[-1]
                new_ori_div.append(ori_div[0])
                new_ori_div.append(temp_combine)
                ori_div = new_ori_div
           
            if ori_div[0]!='':
                ori_div_list.append(ori_div[0])
            ori_div_list.append(names[0])
            #print '|'.join(ori_div_list)
            readyTodiv = ori_div[1]
             
        if readyTodiv!='':
            ori_div_list.append(readyTodiv)
        #print  ori_div_list
    
        final_div_list=[]
        for ori_str in ori_div_list:
            flag_is_name=0
            for names in name_appear:
                if ori_str==names[0]:
                    final_div_list.append(ori_str)
                    flag_is_name = 1
                    break

            if flag_is_name==0:
                seg_list = jieba.cut(ori_str)
                words_seg_list=list(seg_list)
                for word in words_seg_list:
                    final_div_list.append( word.encode('utf-8'))
        #print'|'.join(final_div_list)
    
    else:
        final_div_list=[]
        seg_list = jieba.cut(question)
        words_seg_list=list(seg_list)
        for word in words_seg_list:
            final_div_list.append( word.encode('utf-8'))
    
    return (flag_name,final_div_list,name_appear)

     




def delete_redundance(answer):

    if '，' in answer:
        answer_split = answer.split('，')
        new_answer_split=[]
        len_new_answer_split =0
        for sent in answer_split:
            redundance_flag = 0
            for i in range(len_new_answer_split):
                if simi_sentence(sent, new_answer_split[i]):
                    redundance_flag = 1
                    break
            if redundance_flag == 0:
                new_answer_split.append(sent)
   
        new_answer='，'.join(new_answer_split) 
                             
    else:
        new_answer =answer

    return new_answer




def QAprosess(question):
    #-----------------------(1)输入----------------------------------------------------#
    #print ('请输入问题，以回车键结束')
    #question = raw_input()
    
    #question ='拉拉纳身高'
    #print('-----------------------------')
    #print question
    #print [question_decode]
    if question=='':
        answer = '你什么都没问呀！'
        return answer
    #-------------------------(2)判断逻辑问句-------------------------------------------#
    logi_keys=['是否','是不是','吗']
    for keys in logi_keys:
        keys = keys
        #print [keys]
        pos=question.find(keys)
        if (pos != -1):
            flag_logi = 1
            break
        else:
            flag_logi = 0
    #print flag_logi
    
    #------------------------(3)自然语言处理------------------------------------------------#
    
    #------------(b)给予人名的分词----------------------------#
    name_based_sag_return = name_based_sag(question)
    final_div_list = name_based_sag_return[1]
    flag_name = name_based_sag_return[0]
    name_appear = name_based_sag_return[2]
        #print'|'.join(final_div_list)
    
    #------------(b)词性标注---------------------------------#
    postagger=Postagger()
    postagger.load('/home/sherry/ltp/ltp_data/pos.model')
    postags=postagger.postag(final_div_list)
    nh_flag=0
    nh_word_count =-1
    for i in range(len(postags)):
        if postags[i]=='nh':
            nh_flag=1
            nh_word_count=i
            break
    #print '|'.join(postags)
    postagger.release()
    #------------(c)依存句法树---------------------------------#
    parser=Parser()
    parser.load('/home/sherry/ltp/ltp_data/parser.model')
    arcs=parser.parse(final_div_list,postags)
    #print '\t'.join('%d:%s'%(arc.head,arc.relation)for arc in arcs)
    parser.release()

    #-------------------------------(5)条件处理--------------------------------------------#
    if flag_logi==1:
        key_words = NamedRecognize(question,final_div_list,postags)
        answer_find = SearchRelateNews(key_words)
        if answer_find != '找不到':
            answer = answer_find
        else:
            answer='我也不知道是不是呢！'  
        #print answer
        return answer 

    if flag_name==0:
        if nh_flag!=0:
            key_words = NamedRecognize(question,final_div_list,postags)
            answer_find = SearchRelateNews(key_words)
            if answer_find != '找不到':
                answer = answer_find
            else:
                answer = '我不认识%s'%final_div_list[nh_word_count]
            #print answer
            return answer
        else:
            key_words = NamedRecognize(question,final_div_list,postags)
            answer_find = SearchRelateNews(key_words)
            if answer_find != '找不到':
                answer = answer_find
            else:
                answer = '你要问的是什么？'
            #print answer
            return answer

    elif flag_name>1:
        for i in range(len(arcs)):
            if (arcs[i].relation=='SBV'):
                for j in range(len(name_appear)):
                    if final_div_list[i]==name_appear[j][0]:
                        find_name = final_div_list[i]
                if (vars().has_key('find_name')):
                    find_name = find_name
                else:
                    find_name = name_appear[0][0]
                break 
            else:    
                find_name = name_appear[0][0]

    else:
        find_name = name_appear[0][0]      
       
    #print find_name


    #-------------------------------(6)同义词比较--------------------------------------------#
    root = os.getcwd()
    file_tongyici = open(root+'/TongYiCiLin.txt','r')
    tycl=file_tongyici.read()
    file_tongyici.close()
    a=[]
    tycl_list=[]
    line=''
    for i in range(len(tycl)):
        line=line+tycl[i]
        if tycl[i]=='\n':
            tycl_list.append(line[:-2].replace('@','=').replace('#','=').split('= '))
            line=''
    for j in range(len(tycl_list)):
        tycl_list[j][1]= tycl_list[j][1].split(' ') 
    
    
    for i in range(len(arcs)):
        if (arcs[i].relation=='HED'):
            head_count = i
    if postags[head_count]=='v':
        for i in range(len(arcs)):
            if (arcs[i].relation=='VOB'):
                if postags[i]!='r' and postags[i]!='m':
                    info_count = i
                else:
                    for j in range(len(arcs)):
                        if (arcs[j].relation=='SBV') and final_div_list[j]!=find_name:
                            info_count =j
                    
                    if (vars().has_key('info_count')):
                        info_count=info_count
                    else:
                        info_count = head_count
        if (vars().has_key('info_count')):
            info_count=info_count
        else:
            info_count = head_count       
    else:
        info_count = head_count  
    find_info = final_div_list[info_count]
    #print (find_info)    
    


    player_info = {'position':['Di15A','Cb01B01','Di15B'],'name':['Dd15B'],'img':['Dc03A01'],'country':['Di02A','Dd16B07','Ad02A01'],'age':['Ca14A01'],'weight':['Dn01A29','Dn01A20'],'height':['Ea02','Dn01A13','Dn01A08'],'match_data':['Hh07A'],'birth':['Ca26A'],'season_data':['Hh07A'],'link':['Cb08B13'],'name_en':['Dd15B'],'club_num':['Dk04A']}
    index_flag =0
    for i in range(len(tycl_list)):
        for j in range(len(tycl_list[i][1])):
            if find_info==tycl_list[i][1][j]:
                info_index = tycl_list[i][0]
                index_flag=1
                break
        if index_flag==1:
            break
    if (vars().has_key('info_index')):
            info_index=info_index
    else:
            info_index = 'none'
 
    #print info_index
    find_key=[]
    for key in player_info:
        for key_index in player_info[key]:
            if key_index in info_index:
                find_key.append(key)

    #print find_key
    

    #-------------------------------(7)输出--------------------------------------------#

    if len(find_key)>0:

        sqli = "select %s from liverpool where name='%s'"
        aa=cur.execute(sqli % (find_key[0],find_name))
        info = cur.fetchmany(aa)
        for ii in info:
            #print ii[0].encode('utf-8')
            answer = ii[0].encode('utf-8')
        return answer
        
    else:
        key_words = NamedRecognize(question,final_div_list,postags)
        answer_find = SearchRelateNews(key_words)
        if answer_find != '找不到':
            answer = answer_find
        else:
            answer='待我想想看...'
        #print answer
        return answer



def QAforTest():
    #-----------------------(1)输入----------------------------------------------------#
    print ('请输入问题，以回车键结束')
    #question = raw_input()
    
    question ='拉拉纳身高'
    print('-----------------------------')
    print question
    #print [question_decode]
    if question=='':
        answer = '你什么都没问呀！'
        return answer
    #-------------------------(2)判断逻辑问句-------------------------------------------#
    logi_keys=['是否','是不是','吗']
    for keys in logi_keys:
        keys = keys
        #print [keys]
        pos=question.find(keys)
        if (pos != -1):
            flag_logi = 1
            break
        else:
            flag_logi = 0
    #print flag_logi
    
    #------------------------(3)自然语言处理------------------------------------------------#
    
    #------------(b)给予人名的分词----------------------------#
    name_based_sag_return = name_based_sag(question)
    final_div_list = name_based_sag_return[1]
    flag_name = name_based_sag_return[0]
    name_appear = name_based_sag_return[2]
        #print'|'.join(final_div_list)
    
    #------------(b)词性标注---------------------------------#
    postagger=Postagger()
    postagger.load('/home/sherry/ltp/ltp_data/pos.model')
    postags=postagger.postag(final_div_list)
    nh_flag=0
    nh_word_count =-1
    for i in range(len(postags)):
        if postags[i]=='nh':
            nh_flag=1
            nh_word_count=i
            break
    #print '|'.join(postags)
    postagger.release()
    #------------(c)依存句法树---------------------------------#
    parser=Parser()
    parser.load('/home/sherry/ltp/ltp_data/parser.model')
    arcs=parser.parse(final_div_list,postags)
    #print '\t'.join('%d:%s'%(arc.head,arc.relation)for arc in arcs)
    parser.release()

    #-------------------------------(5)条件处理--------------------------------------------#
    if flag_logi==1:
        key_words = NamedRecognize(question,final_div_list,postags)
        answer_find = SearchRelateNews(key_words)
        if answer_find != '找不到':
            answer = answer_find
        else:
            answer='我也不知道是不是呢！'  
        print answer
        return answer 

    if flag_name==0:
        if nh_flag!=0:
            key_words = NamedRecognize(question,final_div_list,postags)
            answer_find = SearchRelateNews(key_words)
            if answer_find != '找不到':
                answer = answer_find
            else:
                answer = '我不认识%s'%final_div_list[nh_word_count]
            print answer
            return answer
        else:
            key_words = NamedRecognize(question,final_div_list,postags)
            answer_find = SearchRelateNews(key_words)
            if answer_find != '找不到':
                answer = answer_find
            else:
                answer = '你要问的是什么？'
            print answer
            return answer

    elif flag_name>1:
        for i in range(len(arcs)):
            if (arcs[i].relation=='SBV'):
                for j in range(len(name_appear)):
                    if final_div_list[i]==name_appear[j][0]:
                        find_name = final_div_list[i]
                if (vars().has_key('find_name')):
                    find_name = find_name
                else:
                    find_name = name_appear[0][0]
                break 
            else:    
                find_name = name_appear[0][0]

    else:
        find_name = name_appear[0][0]      
       
    #print find_name


    #-------------------------------(6)同义词比较--------------------------------------------#
    root = os.getcwd()
    file_tongyici = open(root+'/TongYiCiLin.txt','r')
    tycl=file_tongyici.read()
    file_tongyici.close()
    a=[]
    tycl_list=[]
    line=''
    for i in range(len(tycl)):
        line=line+tycl[i]
        if tycl[i]=='\n':
            tycl_list.append(line[:-2].replace('@','=').replace('#','=').split('= '))
            line=''
    for j in range(len(tycl_list)):
        tycl_list[j][1]= tycl_list[j][1].split(' ') 
    
    
    for i in range(len(arcs)):
        if (arcs[i].relation=='HED'):
            head_count = i
    if postags[head_count]=='v':
        for i in range(len(arcs)):
            if (arcs[i].relation=='VOB'):
                if postags[i]!='r' and postags[i]!='m':
                    info_count = i
                else:
                    for j in range(len(arcs)):
                        if (arcs[j].relation=='SBV') and final_div_list[j]!=find_name:
                            info_count =j
                    
                    if (vars().has_key('info_count')):
                        info_count=info_count
                    else:
                        info_count = head_count
        if (vars().has_key('info_count')):
            info_count=info_count
        else:
            info_count = head_count       
    else:
        info_count = head_count  
    find_info = final_div_list[info_count]
    #print (find_info)    
    


    player_info = {'position':['Di15A','Cb01B01','Di15B'],'name':['Dd15B'],'img':['Dc03A01'],'country':['Di02A','Dd16B07','Ad02A01'],'age':['Ca14A01'],'weight':['Dn01A29','Dn01A20'],'height':['Ea02','Dn01A13','Dn01A08'],'match_data':['Hh07A'],'birth':['Ca26A'],'season_data':['Hh07A'],'link':['Cb08B13'],'name_en':['Dd15B'],'club_num':['Dk04A']}
    index_flag =0
    for i in range(len(tycl_list)):
        for j in range(len(tycl_list[i][1])):
            if find_info==tycl_list[i][1][j]:
                info_index = tycl_list[i][0]
                index_flag=1
                break
        if index_flag==1:
            break
    if (vars().has_key('info_index')):
            info_index=info_index
    else:
            info_index = 'none'
 
    #print info_index
    find_key=[]
    for key in player_info:
        for key_index in player_info[key]:
            if key_index in info_index:
                find_key.append(key)

    #print find_key
    

    #-------------------------------(7)输出--------------------------------------------#

    if len(find_key)>0:

        sqli = "select %s from liverpool where name='%s'"
        aa=cur.execute(sqli % (find_key[0],find_name))
        info = cur.fetchmany(aa)
        for ii in info:
            print ii[0].encode('utf-8')
            answer = ii[0].encode('utf-8')
        return answer
        
    else:
        key_words = NamedRecognize(question,final_div_list,postags)
        answer_find = SearchRelateNews(key_words)
        if answer_find != '找不到':
            answer = answer_find
        else:
            answer='待我想想看...'
        print answer
        return answer

              











