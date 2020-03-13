# -*- coding: utf-8 -*-
# SPO针对实体处理了一下
# 9.5所作的工作都是对关系更加地over-special
# 对主语和宾语的修改仅有：
#  寻找ATT时，当时为了防止postag为动词的ATT；
#  我们做了一个约束self.get_entity_num_between(item,item1(or item2),sentence)>0将第二个参数，
#  由之前的entity1和entity2（即，主语和宾语）全都改成（item.head_word），
#  即在这里，原先是判断该修饰词与主语或宾语（这取决于该修饰词是主语的ATT，还是宾语的ATT）之间没有实体；
#  全都改成该词性为v的修饰词与该修饰词的head_word之间没有实体存在；
#  依然可以杜绝“颐和园是始建于乾隆年间的皇家园林”抽取出（颐和园，是，始建皇家园林）
#  正确结果：['颐和园', '始建于', '乾隆年间'], ['颐和园', '是', '皇家园林']
# 9.6的工作是：加上3个约束
# import pynlpir
from pyltp import Segmentor, Postagger, NamedEntityRecognizer, Parser
import os

from LTPNLP.core.GraphvizOutput import outputAsGraphForList
from LTPNLP.core.mapEntity import mapEntity, getAttWord
from entity_verb.entity_verb_new import entity_verb_new
import sys
import datetime

sys.path.append("..")  # 跳出当前目录
from LTPNLP.bean.word_unit import WordUnit
from LTPNLP.bean.sentence_unit import SentenceUnit
from LTPNLP.core.entity_combine import EntityCombine
import json,re


class DSFN:
    """进行自然语言处理，包括分词，词性标注，命名实体识别，依存句法分析
    Attributes：
        default_user_dict_dir:str，用户自定义词典目录
        default_model_dir：str，ltp模型文件目录
    """

    entity_verb_new = entity_verb_new()
    all_entity = entity_verb_new.readAllEntity("../../entity_verb//entity_verb_result\\all_entity.json")
    default_model_dir = 'D:\python-file\knowledge_extraction-master-tyz\\ltp_data_v3.4.0\\'  # LTP模型文件目录
    location_entity = ["中和殿", "太庙", "人文地理", "亚运村", "九龙壁", "圆明园", "古典建筑", "庑殿顶", "天井", "无量殿", "慈宁宫", "三希堂", "居庸关", "延寿寺", "排云殿", "东桥", "圜丘", "南天门", "垂花门", "西六宫", "配楼", "柳荫街", "中国四大名园", "午门", "乾东五所", "建筑管理", "世界博物馆", "西什库教堂", "晚清", "万泉河", "东暖阁", "储秀宫", "西华门", "院落", "地安门东大街", "御路", "知鱼桥", "清宁宫", "金水河", "景山前街", "司马台长城", "景山公园", "乐寿堂", "东六宫", "延陵", "宜芸馆", "芍药居", "承乾宫", "琉璃瓦", "湘江", "敌楼", "安定门外大街", "三音石", "崇文门", "天坛路", "台基", "东城区", "外朝", "武备", "全国重点文物保护单位", "房山石", "静园", "香山", "中东", "坤宁宫", "彩画", "江南园林", "北河沿大街", "岳阳楼", "丽景轩", "巴黎圣母院", "钟表馆", "戏楼", "白银", "红海", "中原", "明长城", "神乐署", "瀛洲", "码头", "百度地图", "旋子彩画", "乾西五所", "天圆地方", "琉璃厂文化街", "广岛", "御沟", "井亭", "古柏林", "石坊", "北京故宫", "宝云阁", "甬道", "熙和门", "乾清门", "北京城", "暖温带", "沥粉贴金", "安定路", "北齐长城", "减柱造", "宅园", "清华园", "天坛东门站", "西苑", "土山", "温带季风气候", "宫古", "东直门", "美国国务卿", "北海", "中华梦石城", "东门站", "天坛公园", "江山", "谐趣园", "修宅", "苏堤", "玉泉", "牌坊", "蓟镇", "高速公路", "钟粹宫", "无梁殿", "政治家", "牌楼", "波斯", "西内", "老龙头", "阴阳石", "三神山", "丹陛桥", "中国第一历史档案馆", "建筑艺术", "四川", "护城河", "文华殿", "静宜园", "乐峰", "永和宫", "金砖", "清漪园", "安定门", "宫殿", "梵华楼", "龙井", "水街", "东华门", "歇山式顶", "斋宫", "渤海镇", "仁和", "白浮村", "建筑风格", "买卖街", "藻鉴堂", "寿安宫", "奉先殿", "后海", "宋", "承德避暑山庄", "前门站", "寿安山", "八达岭", "棂星门", "经幢", "泰山", "后三宫", "天桥商场", "维新派", "拙政园", "北京十六景", "南湖岛", "山寨", "东海", "寺庙", "图书馆", "西山", "延禧宫", "九土", "十七孔桥", "鹊桥", "石鼓", "样式雷", "礼乐", "圆石", "动物园", "西湖", "齐长城遗址", "京畿", "正脊", "神武门", "洛神赋图", "绿地面积", "暖阁", "多宝塔", "磨砖对缝", "湖心亭", "崇楼", "五谷丰登", "养性殿", "关山", "砖雕", "北境", "凤凰墩", "金殿", "永定路", "世界遗产", "古柏", "郡王府", "慕田峪", "皇舆全览图", "古典园林", "坐北朝南", "皇极殿", "皇家园林", "东四十条", "京西", "黄花镇", "通惠河", "宁寿宫", "旅游局", "大角楼", "昆明湖", "后溪", "东堤", "汉白玉石", "皇史宬", "湖心岛", "长春宫", "玉澜堂", "紫檀", "玉泉山", "玉山", "茶楼", "敌台", "乾清宫", "巴县", "藕香榭", "斗拱", "苏州街", "紫禁城", "颐和轩", "皇穹宇", "南方", "智慧海", "八小部洲", "拱券", "门楣", "太和殿", "銮仪卫", "法门寺地宫", "清音阁", "龙王庙", "城岛", "皇陵", "筒瓦", "天地坛", "张古", "建筑史", "武英殿", "北长街", "天坛", "云山", "大石桥", "北平", "宫殿建筑", "山东", "博物馆", "昆明池", "交道口南大街", "平流村", "聊城", "三大殿", "清晏舫", "墀头", "养心殿", "御道", "百花园", "翊坤宫", "神道", "落地罩", "渔村", "丹陛", "歇山顶", "畅音阁", "漱芳斋", "黄鹤楼", "柱础", "嘉乐堂", "庆长", "档案", "保定", "上海", "佛香阁", "望柱", "德和园", "天桥", "北京旅游网", "祈年殿", "颐和园", "攒尖顶", "香岩宗印之阁", "分界线", "大杂院", "交泰殿", "太和门", "南郊", "健翔桥", "瓮山", "勤政殿", "云南", "景仁宫", "小山村", "金水桥", "保和殿", "寄畅园", "珍妃井", "德和园大戏楼", "正房", "第一批全国重点文物保护单位", "三合院", "万寿山", "厉家菜", "玉峰塔", "藻井", "恭王府花园", "文昌阁", "景山", "前门东大街", "端门", "代王府", "万寿亭", "景阳宫", "东四环", "景明楼", "祈谷坛", "大戏楼", "安佑宫", "石舫", "流杯亭", "行宫", "法华寺", "圜丘坛", "正义路", "居庸关长城", "箭扣长城", "石牌坊", "回音壁", "和玺彩画", "二龙戏珠", "北四环", "玉龙", "广州", "盛京", "四合院", "曲尺", "谷仓", "永定门", "宝顶", "苏式彩画", "皇宫", "寿康宫"]
    def __init__(self, model_dir=default_model_dir, all_entity=all_entity):
        self.default_model_dir = model_dir
        # 加载ltp模型
        #
        default_model_dir = 'D:\python-file\knowledge_extraction-master-tyz\\ltp_data_v3.4.0\\'  # LTP模型文件目录
        self.segmentor_user = Segmentor()
        user_dict = "..\\source\\user.txt"
        segmentor_flag_user = self.segmentor_user.load_with_lexicon(os.path.join(default_model_dir, 'cws.model'), user_dict)
        self.segmentor = Segmentor()
        segmentor_flag = self.segmentor.load(os.path.join(default_model_dir, 'cws.model'))
        # 词性标注模型
        self.postagger = Postagger()
        postag_flag = self.postagger.load(os.path.join(self.default_model_dir, 'pos.model'))
        # 命名实体识别模型
        self.recognizer = NamedEntityRecognizer()
        ner_flag = self.recognizer.load(os.path.join(self.default_model_dir, 'ner.model'))
        # 依存句法分析模型
        self.parser = Parser()
        parser_flag = self.parser.load(os.path.join(self.default_model_dir, 'parser.model'))

        if segmentor_flag or postag_flag or ner_flag or parser_flag or segmentor_flag_user:  # 可能有错误
            print('load model failed')

    def segment(self, sentence, segmentor, entity_postag=dict()):
        words = segmentor.segment(sentence)
        lemmas = []
        for lemma in words:
            lemmas.append(lemma)
        return lemmas

    def getPostag(self):
        return self.postagger

    def postag(self, lemmas):
        """
        Parameters
        ----------
        lemmas : List，分词后的结果
        entity_dict：Set，实体词典，处理具体的一则判决书的结构化文本时产生
        Returns
        -------
        words:WordUnit List，包括分词与词性标注的结果
        """
        words = []
        # 词性标注
        postags = self.postagger.postag(lemmas)
        for i in range(len(lemmas)):
            # 存储分词与词性标记后的词单元WordUnit，编号从1开始
            word = WordUnit(i + 1, lemmas[i], postags[i])
            words.append(word)
        # self.postagger.release() #释放
        return words

    def get_postag(self, word):
        """获得单个词的词性标注
        Args:
            word:str,单词
        Returns:
            pos_tag:str，该单词的词性标注
        """
        pos_tag = self.postagger.postag([word])
        return pos_tag[0]

    def netag(self, words):
        """
        命名实体识别，并对分词与词性标注后的结果进行命名实体识别与合并
        Parameters
            words : WordUnit list，包括分词与词性标注结果
        Returns
            words_netag：WordUnit list，包含分词，词性标注与命名实体识别的结果
        """
        lemmas = []  # 存储分词后的结果
        postags = []  # 存储词性标注结果
        for word in words:
            lemmas.append(word.lemma)
            postags.append(word.postag)
        # 命名实体识别
        netags = self.recognizer.recognize(lemmas, postags)
        words_netag = EntityCombine().combine(words, netags)
        return words_netag

    def parse(self, words):
        """
        对分词，词性标注与命名实体识别后的结果进行依存句法分析（命名实体识别可选）
        Args:
            words_netag：WordUnit list，包含分词，词性标注与命名实体识别结果
        Returns
            *：sentenceUnit 句子单元
        """
        lemmas = []  # 分词结果
        postags = []  # 词性标注结果
        for word in words:
            lemmas.append(word.lemma)
            postags.append(word.postag)
        # 依存句法分析
        arcs = self.parser.parse(lemmas, postags)
        for i in range(len(arcs)):
            words[i].head = arcs[i].head
            words[i].dependency = arcs[i].relation
        return SentenceUnit(words)

    def close(self):
        """
        关闭与释放
        """
        # pynlpir.close()
        self.postagger.release()
        self.recognizer.release()
        self.parser.release()

    def splitSentence(self,text):
        pattern = r'。|！|？|；|='
        result_list = re.split(pattern, text)
        result_list = list(filter(self.not_empty, result_list))
        #    print(result_list)
        return result_list

    def splitSentenceByComma(self,text):
        pattern = r'，'
        result_list = re.split(pattern, text)
        result_list = list(filter(self.not_empty, result_list))
        final_list = []
        for sentence in result_list:
            if len(sentence) <= 40:
                final_list.append(sentence)
        return final_list

    def not_empty(self,s):
        return s and "".join(s.split())

    def dsfn1_2_3_4COO(self, sentence, item1, item2,flagCOOATT):
        allTripes = []

        """
        判断两个实体是否属于DSFN1的情况，并输出三元组
        """
        # print(item1.lemma)
        # print(item2.lemma)
        # print(flagCOOATT)

        if flagCOOATT == False:
            location_position_list = getAttWord()
            # print(location_position_list)
            if  self.dsfnConstraints3(sentence,item1,item2) and (item1.dependency == "ATT" ):
                AttWord = item1.head_word
                AttWordDict = dict()
                AttWordStr = ""
                while AttWord.ID < item2.ID:
                    AttWordDict[AttWord.ID] = AttWord.lemma
                    # print(AttWord.lemma)
                    # AttWordStr += AttWord.lemma
                    if (AttWord.dependency == "ATT" ):
                        AttWord = AttWord.head_word
                    else:
                        break

                if (AttWord.ID == item2.ID):
                    flag = True
                    while flag:
                        len1 = len(AttWordDict)
                        AttList = AttWordDict.keys()
                        for id in range(item1.ID + 1, item2.ID):
                            item = sentence.get_word_by_id(id)
                            if item.head_word != None and item.head_word.ID in AttList and (item.dependency == "ATT" ):
                                AttWordDict[item.ID] = item.lemma
                                # print(item.lemma)
                        if len1 == len(AttWordDict):
                            flag = False
                        else:
                            flag = True
                    AttWordDict = sorted(AttWordDict.items(), key=lambda item: item[0])
                    AttWordStr = ""
                    for i in AttWordDict:
                        AttWordStr += i[1]
                    # print("三元组：（" + item1.lemma + "，" + AttWordStr + "，" + item2.lemma + "）")

                    if AttWordStr in location_position_list:
                        allTripes.append([item1.lemma+"DSFN1", AttWordStr, item2.lemma])
                        # print(allTripes)
                        # print("-------------------------")
                    # else:
                    #     for attWord in location_position_list:
                    #         if attWord in AttWordStr:
                    #             allTripes.append([item1.lemma, AttWordStr, item2.lemma])
                    #             print(allTripes)
                    #
                    #             print("-------------------------")


        """
        考虑DSFN2的情况
        """
        if item1.dependency == "SBV" and item1.head_word.postag == "v":
            pred1 = item1.head_word
            predDict = dict()
            predDict[pred1.ID] = pred1.lemma
            """
            Constraint4:如果E1是一个动词的主语，那么E1和该动词之间应该没有其他词也作为主语，修饰该动词
            """
            constraint4 = True
            for word in sentence.words:
                if word!=None and word.ID>item1.ID and word.ID <=pred1.ID and word.dependency == "SBV" and word.head_word.ID == pred1.ID:
                    constraint4 = False
            if constraint4 == True \
                and item2.dependency == "VOB" and item2.head_word.postag == "v":
                pred2 = item2.head_word
                predDict[pred2.ID] = pred2.lemma
                if (len(predDict) == 1):
                    objDict = dict()
                    wordAfterOBJ = sentence.get_word_by_id(item2.ID + 1)
                    """
                    考虑“1961年中华人民共和国国务院公布故宫为全国重点文物保护单位”
                    """
                    if wordAfterOBJ != None and wordAfterOBJ.lemma == '为'  \
                            and wordAfterOBJ.postag == 'v' and wordAfterOBJ.dependency == 'COO' and wordAfterOBJ.head_word.ID == pred1.ID:
                        predDict[wordAfterOBJ.ID] = wordAfterOBJ.lemma
                        print("是不是走这一步了呢")
                        for word in sentence.words:
                            if word.dependency == "VOB" and word.head_word.ID == wordAfterOBJ.ID:
                                objDict[word.ID] = word.lemma
                        print(objDict)
                        flagLoop = True
                        while flagLoop == True:
                            len1 = len(objDict)
                            for word in sentence.words:
                                if word.head_word != None and (word.dependency == "ATT" or word.dependency == "FOB") \
                                        and word.head_word.ID in objDict:
                                    objDict[word.ID] = word.lemma
                                if len1 != len(objDict):
                                    flagLoop = True
                                else:
                                    flagLoop = False
                    PredWordStr = ""
                    for i in predDict:
                        PredWordStr += predDict[i]
                    objectDict = sorted(objDict.items(), key=lambda item: item[0])
                    objectStr = ""
                    for objectItem in objectDict:
                        objectStr += objectItem[1]
                    # print("DSFN2三元组：（" + item1.lemma + "，" + PredWordStr + "，" + item2.lemma + "）")
                    allTripes.append([item1.lemma, PredWordStr + "" + objectStr, item2.lemma])

                    # PredWordStr = ""
                    # for i in predDict:
                    #     PredWordStr += predDict[i]
                    # # print("DSFN2三元组：（" + item1.lemma + "，" + PredWordStr + "，" + item2.lemma + "）")
                    # allTripes.append([item1.lemma, PredWordStr, item2.lemma])
                    """
                    新加，为了考虑“习近平视察和访问上海”的情况
                    """
                if len(predDict) ==2:
                    num = self.get_entity_num_between(pred1,pred2,sentence)
                    flagSBV = True
                    flagVOB = True
                    print("111222333"+pred2.lemma)
                    for word in sentence.words:
                        if word.dependency == "SBV" and (word.head_word.ID == pred2.ID
                                                         or (word.ID != item1.ID and pred2.dependency == "COO" and word.head_word.ID == pred2.head_word.ID)):
                            """
                            word.ID != item1.ID
                            即pred1和pred2也可能是COO关系
                            """
                            flagSBV = False
                        if (word.dependency == "VOB" and word.head_word.ID == pred1.ID)  or (word.dependency == "POB" \
                                and word.head_word.dependency == "ADV" and word.head_word.head_word.ID == pred1.ID) or \
                                (word.dependency == "POB" \
                                and word.head_word.dependency == "CMP" and word.head_word.head_word.ID == pred1.ID):
                            flagVOB = False
                    flagCMP= True
                    if pred1!=None and pred1.dependency == "CMP" and pred1.head_word.ID == pred2.ID:
                        flagCMP = False
                    if pred2!=None and pred2.dependency == "CMP" and pred2.head_word.ID == pred1.ID:
                        flagCMP = False
                    flagCOO = True
                    if pred1 != None and pred1.dependency == "COO" and pred1.head_word.ID == pred2.ID:
                        flagCOO = False
                    if pred2 != None and pred2.dependency == "COO" and pred2.head_word.ID == pred1.ID:
                        flagCOO = False

                    # print("pred1:"+pred1.lemma+",pred2:"+pred2.lemma+",num:"+str(num))
                    if num == 0 :
                        if flagCMP == False :
                            if flagVOB == True and flagSBV == True:
                                allTripes.append([item1.lemma, pred1.lemma + "" +pred2.lemma, item2.lemma])
                        if flagCOO == False:
                            if flagVOB == True and flagSBV == True:
                                allTripes.append([item1.lemma, pred1.lemma + "" +pred2.lemma, item2.lemma])
                        else:
                            if flagVOB == True:
                                allTripes.append([item1.lemma, pred1.lemma, item2.lemma])
                            if flagSBV == True:
                                allTripes.append([item1.lemma, pred2.lemma, item2.lemma])



        """
        DSFN3.0
        """
        pred = None
        constraint4 = True
        constraint5 = True
        if item1.dependency == "SBV" and item1.head_word.postag == "v" and item2.dependency == "POB":
            pred = item1.head_word
            """
                    Constraint4:如果E1是一个动词的主语，那么E1和该动词之间应该没有其他词也作为主语，修饰该动词
            """
            constraint4 = True
            for word in sentence.words:
                if word!=None and word.ID > item1.ID and word.ID <= pred.ID and word.dependency == "SBV" and word.head_word.ID == pred.ID:
                    constraint4 = False
            # """
            # constraint5:在DSNF3中，介词短语选择离动词最近的一个
            # """
            # constraint5 = True
            # for eachWord in sentence.words:
            #     if eachWord!=None and eachWord.ID > item2.ID and eachWord.ID <=  pred.ID and eachWord.dependency == "POB" \
            #             and eachWord.head_word.dependency == "ADV" and eachWord.head_word.head_word.ID == pred.ID \
            #             and eachWord.postag != 'v':
            #         constraint5 = False
            prep = item2.head_word
        elif item1.dependency == "FOB" and item2.dependency == "POB":  # 考虑介词为“被”的情况，如 “小王被小明所陷害”
            pred = item1.head_word
            prep = item2.head_word
            constraint4 = True
            for word in sentence.words:
                if word.ID > item1.ID and word.ID <= pred.ID and word.dependency == "SBV" and word.head_word.ID == pred.ID:
                    constraint4 = False
            # """
            # constraint5:在DSNF3中，介词短语选择离动词最近的一个
            # """
            # # print("!!!!!!!!---------------"+item1.lemma)
            # constraint5 = True
            # for eachWord in sentence.words:
            #
            #     if eachWord!=None and eachWord.ID > item2.ID and eachWord.ID <= pred.ID and eachWord.dependency == "POB" \
            #             and eachWord.head_word.dependency == "ADV" and eachWord.head_word.head_word.ID == pred.ID \
            #             and eachWord.postag != 'v':
            #         # print("..................." + eachWord.lemma)
            #         constraint5 = False
            c = item1
            item1 = item2
            item2 = c
            # print("constraint5:"+" "+str(constraint5))


        if constraint5== True and constraint4 == True and pred != None and prep != None:
            if prep.dependency == "ADV":
                if prep.head_word.ID == pred.ID:
                    pred2 = None
                    object = None
                    objectForPred2 = None
                    flagVOB = False
                    objectDict = dict()
                    for i in range(pred.ID + 1, len(sentence.words) + 1):
                        item = sentence.get_word_by_id(i)

                        if item.dependency == "VOB" and item.head_word.ID == pred.ID:
                            object = item

                            flagVOB = True
                            objectDict[object.ID] = object
                            flagLoop = True
                            while flagLoop == True:
                                len1 = len(objectDict)
                                for word in sentence.words:
                                    if word.head_word != None and( word.dependency == "ATT")and word.head_word.ID in objectDict:
                                        objectDict[word.ID] = word
                                    if len1 != len(objectDict):
                                        flagLoop = True
                                    else:
                                        flagLoop = False
                    if flagVOB == True:
                        objectDict = sorted(objectDict.items(), key=lambda item: item[0])
                        objectStr = ""
                        for objectItem in objectDict:
                            objectStr += objectItem[1].lemma
                        allTripes.append([item1.lemma, pred.lemma + "" + objectStr, item2.lemma])
                    if flagVOB==False:
                        for i in range(pred.ID + 1, len(sentence.words) + 1):
                            item = sentence.get_word_by_id(i)

                            if item.dependency == "CMP" and item.head_word.ID == pred.ID:
                                object = item
                                objectDict = dict()
                                objectDict[object.ID] = object
                                for word in sentence.words:
                                    if word.head_word != None and (word.dependency == "VOB" or word.dependency == "POB")\
                                            and word.head_word.ID == object.ID:
                                        objectDict[word.ID] = word
                                flagLoop = True
                                while flagLoop == True:
                                    len1 = len(objectDict)
                                    for word in sentence.words:
                                        if word.head_word != None and word.dependency == "ATT" and word.head_word.ID in objectDict:
                                            objectDict[word.ID] = word
                                        if len1 != len(objectDict):
                                            flagLoop = True
                                        else:
                                            flagLoop = False
                                objectDict = sorted(objectDict.items(), key=lambda item: item[0])
                                objectStr = ""
                                for objectItem in objectDict:
                                    objectStr += objectItem[1].lemma
                                allTripes.append([item1.lemma, pred.lemma + "" + objectStr, item2.lemma])


                    if object == None:
                        hasPOB = False
                        for i in range(pred.ID + 1, len(sentence.words) + 1):
                            item = sentence.get_word_by_id(i)
                            if item.dependency == "POB" and item.head_word.dependency == "CMP" and item.head_word.head_word.ID == pred.ID:
                                hasPOB = True
                                allTripes.append([item1.lemma, pred.lemma + "" + item.head_word.lemma + "" + item.lemma, item2.lemma])
                        # print("DSFN3三元组：（" + item1.lemma + "，" + pred.lemma + "，" + item2.lemma + "）")
                        if hasPOB == False:
                            allTripes.append([item1.lemma, pred.lemma , item2.lemma])
        """
        DSFN4
        """
        pred = None
        prep = None
        prep1 = None
        pred2 = None
        if item1.dependency == "SBV" and item2.dependency == "POB":
            pred = item1.head_word
            """
                    Constraint4:如果E1是一个动词的主语，那么E1和该动词之间应该没有其他词也作为主语，修饰该动词
            """
            constraint4 = True
            for word in sentence.words:
                if word!=None and  word.ID > item1.ID and word.ID <= pred.ID and word.dependency == "SBV" and word.head_word.ID == pred.ID:
                    constraint4 = False
            prep = item2.head_word
            if constraint4 == True and prep.dependency == "CMP":
                pred2 = prep.head_word
                if pred2.ID == pred.ID:
                    # print("DSFN4三元组：（" + item1.lemma + "，" + pred.lemma + "" + prep.lemma + "，" + item2.lemma + "）")
                    allTripes.append([item1.lemma, pred.lemma + "" + prep.lemma, item2.lemma])
                else :
                    num = self.get_entity_num_between(pred, pred2, sentence)
                    flagSBV = True
                    flagVOB = True
                    for word in sentence.words:
                        if word.dependency == "SBV" and word.head_word.ID == pred2.ID:
                            flagSBV = False
                        if (word.dependency == "VOB" and word.head_word.ID == pred.ID) or (word.dependency == "POB" \
                                and word.head_word.dependency == "ADV" and word.head_word.head_word.ID == pred.ID):
                            flagVOB = False
                    # print("pred1:"+pred1.lemma+",pred2:"+pred2.lemma+",num:"+str(num))
                    if num == 0 :
                        flag = True
                        for word in sentence.words:
                            if word.dependency == "CMP" and word.head_word.ID == pred.ID:
                                prep1 = word
                        if prep1 != None:
                            if flagVOB == True:
                                # print("DSFN4三元组：（" + item1.lemma + "，" + pred.lemma + "" + prep1.lemma + "，" + item2.lemma + "）")
                                allTripes.append([item1.lemma, pred.lemma + "" + prep1.lemma, item2.lemma])
                            # print("DSFN4三元组：（" + item1.lemma + "，" + pred2.lemma + "" + prep.lemma + "，" + item2.lemma + "）")
                            if flagSBV == True:
                                allTripes.append([item1.lemma, pred2.lemma + "" + prep.lemma, item2.lemma])
                        else:
                            if flagVOB == True:
                                # print("DSFN4三元组：（" + item1.lemma + "，" + pred.lemma + "，" + item2.lemma + "）")
                                allTripes.append([item1.lemma, pred.lemma, item2.lemma])
                            if flagSBV == True:
                            # print("DSFN4三元组：（" + item1.lemma + "，" + pred2.lemma + "" + prep.lemma + "，" + item2.lemma + "）")
                                allTripes.append([item1.lemma, pred2.lemma + "" + prep.lemma, item2.lemma])

        """
        DSFN5
        """
        # self.dsfn5and6(rawSentence,sentence,item1,item2)
        return allTripes

    def get_entity_num_between(self,verb1,verb2,sentence):
        """
        获得两个动词之间的实体数量
        Parameters
        ----------
        entity1 : WordUnit，动词1
        entity2 : WordUnit，动词2
        Returns：
            num：int，两动词间的实体数量
        """
        if verb1.ID > verb2.ID:
            c = verb1
            verb1 = verb2
            verb2 = c
        num = 0
        i = verb1.ID
        while i < verb2.ID-1:
            if self.is_entity(sentence.words[i]):
                num +=1
            i +=1
        return num

    def is_entity(self,entry):
        """判断词单元是否是实体
        Args：
            entry：WordUnit，词单元
        Returns：
            *:bool，实体（True），非实体（False）
        """
        #候选实体词性列表
        entity_postags = ['nh','ni','ns','nz','j','n','v','m']
        # print(entry.lemma+" : "+entry.postag)
        if entry.postag in entity_postags:
            return True
        else:
            return False
    def dsfnAttCOO(self,sentence,item1,item2):
        item1Att = item1
        item2Att = item2
        while item1Att.dependency == "ATT":
            item1Att = item1Att.head_word

        allTripe = self.dsfn1_2_3_4COO(sentence,item1Att,item2)
        if allTripe == None or len(allTripe) == 0:
            while item2Att.dependency == "ATT":
                item2Att = item2Att.head_word
            allTripe = self.dsfn1_2_3_4COO(sentence,item1,item2Att)
        if allTripe == None or len(allTripe) == 0:
            allTripe = self.dsfn1_2_3_4COO(sentence,item1Att,item2Att)
        for tripe in allTripe:
            if tripe[0] == item1Att.lemma:
                tripe[0] = item1.lemma
            if tripe[2] == item2Att.lemma:
                tripe[2] = item2.lemma
        return allTripe

    def dsfn5COO(self, sentence, item1, item2):
        if item1.dependency == "COO":
            item1COO = item1.head_word
            allTripes1 = self.dsfn1_2_3_4COO(sentence,item1COO,item2,True)
            # print(allTripes1)
            for tripe in allTripes1:
                if tripe[0] == item1COO.lemma:
                    tripe[0] = item1.lemma
                elif tripe[2] == item1COO.lemma:
                    tripe[2] = item1.lemma
            return allTripes1
            # print("allTripes1"+str(allTripes1))
    def dsfn6COO(self,sentence,item1,item2):
        if item2.dependency == "COO":
            item2COO = item2.head_word
            allTripes2 = self.dsfn1_2_3_4COO(sentence,item1,item2COO,True)
            for tripe in allTripes2:
                if tripe[2] == item2COO.lemma:
                    tripe[2] = item2.lemma
                elif tripe[0] == item2COO.lemma:
                    tripe[0] = item2.lemma
            return allTripes2
    def dsfn5and6COO(self,sentence,item1,item2):
        if item1.dependency == "COO":
            item1COO = item1.head_word
            if item2.dependency == "COO":
                item2COO = item2.head_word
                allTripe = self.dsfn1_2_3_4COO(sentence,item1COO,item2COO,True)
                for tripe in allTripe:

                    if tripe[0] == item1COO.lemma and tripe[2] == item2COO.lemma:
                        tripe[0] = item1.lemma
                        tripe[2] = item2.lemma
                    if tripe[2] == item1COO.lemma and tripe[0] == item2COO.lemma:
                        tripe[2] = item1.lemma
                        tripe[0] = item2.lemma
                return allTripe
    def dsfnStart(self, rawSentence,segmentor, entity1, entity2,all_entity):
        location_position_list = getAttWord()
        nounRelatedWithPosition = ['主席','总理','教授','校长']
        resultList = []
        lemmas = dsfn.segment(rawSentence,segmentor)
        words = dsfn.postag(lemmas)
        words_netag = dsfn.netag(words)
        sentence = dsfn.parse(words_netag)
        # print(sentence.to_string())
        Rawitem1 = None
        Rawitem2 = None
        item1 = None
        item2 = None
        Rawitem1Index = -1
        Rawitem2Index = -1
        indexList = [-1,-1]
        for item in sentence.words:
            # print(str(item.ID) + " " +item.lemma )
            if (item.lemma == entity1):
                Rawitem1 = item
            if (item.lemma == entity2):
                Rawitem2 = item
            if Rawitem1 != None and Rawitem2 != None and (Rawitem1.ID!=Rawitem1Index or Rawitem2.ID!=Rawitem2Index):
                Rawitem1Index = Rawitem1.ID
                Rawitem2Index = Rawitem2.ID
                # print(str(Rawitem1Index) +" " +str(Rawitem2Index))
                # if item1 == None or item2 == None:
                #     return None
                item1 = Rawitem1
                item2 = Rawitem2
                if item1.ID > item2.ID:
                    c = item1
                    item1 = item2
                    item2 = c
                # print(str(item1.ID) + "   " + str(item2.ID))
                itemCopy1 = item1
                itemCopy2 = item2
                # print(item1.lemma)
                # print(item2.lemma)
                # print(self.dsfnConstraints2(sentence,item1,item2,all_entity))
                if self.dsfnConstraints2(sentence,item1,item2,all_entity) == False:

                    continue
                allTripes = self.dsfnStartCOO2(sentence,item1,item2,False)

                # print("111"+item2.lemma)
                # print(allTripes)
                if allTripes == None or (allTripes!=None and len(allTripes) == 0):
                    # print("我要走ATT的部分了")
                    item1AttDict = dict()
                    item2AttDict = dict()

                    while item1.dependency == "ATT":
                        item1AttDict[item1.ID] = item1
                        item1 = item1.head_word

                    item1AttDict[item1.ID] = item1

                    # for attForItem1 in sentence.words:
                    #     if attForItem1.dependency == "ATT" and attForItem1.head_word.ID == item1.ID:
                    #         item1AttDict[attForItem1.ID] = attForItem1
                    flag = True
                    while flag == True:
                        len1 = len(item1AttDict)
                        for item in sentence.words:
                            if item.head_word != None:
                                SUBList = item1AttDict.keys()
                                if item.head_word.ID in SUBList and (item.dependency == "ATT"):
                                    if item.dependency == "ATT" and item.postag == "v":
                                        if self.get_entity_num_between(item, item.head_word, sentence) > 0:
                                            continue
                                        else:
                                            SUBATT = item
                                            item1AttDict[SUBATT.ID] = SUBATT
                                    else:
                                        SUBATT = item
                                        item1AttDict[SUBATT.ID] = SUBATT

                            if len(item1AttDict) != len1 :
                                flag = True
                            else:
                                flag = False



                    while item2.dependency == "ATT":
                        item2AttDict[item2.ID] = item2
                        item2 = item2.head_word
                    item2AttDict[item2.ID] = item2
                    # for attForItem2 in sentence.words:
                    #     if attForItem2.dependency == "ATT" and attForItem2.head_word.ID == item2.ID:
                    #         item2AttDict[attForItem2.ID] = attForItem2

                    flag = True
                    while flag == True:
                        len2 = len(item2AttDict)
                        for item in sentence.words:
                            if item.head_word != None:
                                OBJList = item2AttDict.keys()
                                if item.head_word.ID in OBJList and (item.dependency == "ADV" or item.dependency == "ATT" or item.dependency == "VOB"
                                or item.dependency == "POB"
                                        or (item.dependency == "COO" and item.head_word.ID != item2.ID)):
                                    # print(item.lemma + "---111111")
                                    if item.dependency == "ATT" and item.postag == "v":
                                        if self.get_entity_num_between(item,item.head_word,sentence)>0:
                                            # print(item.lemma+"---救命啊")
                                            continue
                                        else:
                                            OBJATT = item
                                            item2AttDict[OBJATT.ID] = OBJATT
                                    else:
                                        OBJATT = item
                                        item2AttDict[OBJATT.ID] = OBJATT
                                        # print(OBJATT.lemma)

                            if len(item2AttDict) != len2:
                                flag = True
                            else:
                                flag = False #一直循环，直到找不到新的修饰词


                    allTripes = self.dsfnStartCOO2(sentence, item1, item2,True)

                    item1AttDict = sorted(item1AttDict.items(), key=lambda item: item[0])
                    item1AttStr = ""
                    for item1AttItem in item1AttDict:
                        item1AttStr += item1AttItem[1].lemma


                    item2AttDict = sorted(item2AttDict.items(), key=lambda item: item[0])
                    item2AttStr = ""
                    for item2AttItem in item2AttDict:
                        item2AttStr += item2AttItem[1].lemma

                    flagATT1 = False

                    item1ID = item1.ID
                    beforeItem1Word = sentence.get_word_by_id(item1ID - 1)
                    count = 0
                    for item1AttID in range(item1ID - 1, -1, -1):
                        item1Att = sentence.get_word_by_id(item1AttID)

                        if item1Att == None:
                            break
                        if count == 0:
                            if item1Att.dependency == "ATT" and item1Att.head_word.ID == item1.ID and \
                                    item1Att.lemma in location_position_list:
                                count = count + 1
                                # print("count=0：" + item1Att.lemma)
                            else:
                                break

                        elif count == 1:
                            # print("123" + item1Att.lemma)
                            if item1Att.dependency == "ATT" and item1Att.head_word.head_word.ID == item1.ID:
                                # print("123"+item1Att.lemma)
                                if item1Att.lemma in self.all_entity:
                                    # if item1Att.lemma in ["德国","默克尔","美国","奥巴马"]:
                                    count = count + 1
                                    flagATT1 = True
                                    # print("count=1"+item1Att.lemma)
                            elif item1Att.lemma == '的':
                                pass
                            else:
                                break

                    flagATT2 = False

                    item2ID = item2.ID
                    beforeItem1Word = sentence.get_word_by_id(item2ID - 1)
                    count = 0
                    for item2AttID in range(item2ID - 1, -1, -1):
                        item2Att = sentence.get_word_by_id(item2AttID)

                        if item2Att == None:
                            break
                        if count == 0:
                            if item2Att.dependency == "ATT" and item2Att.head_word.ID == item2.ID and \
                                    item2Att.lemma in location_position_list:
                                count = count + 1
                                # print("123" + item2Att.lemma)
                            else:
                                break

                        elif count == 1:
                            # print("123" + item1Att.lemma)
                            if item2Att.dependency == "ATT" and item2Att.head_word.head_word.ID == item2.ID:
                                # print("123"+item1Att.lemma)
                                if item2Att.lemma in self.all_entity:
                                    count = count + 1
                                    flagATT2 = True
                                    # print("123"+item1Att.lemma)
                            elif item2Att.lemma == '的':
                                pass
                            else:
                                break

                    if len(allTripes) != 0:
                        for tripe in allTripes:
                            if tripe[1] != "":
                                """
                        DSFN1的情况，无需用ATT替换（乾隆，宠臣，和珅） --->（乾隆，宠臣，乾隆宠臣和珅）
                                """
                                if "DSFN1" in tripe[0]:
                                    tripe[0] = tripe[0][:-5]
                                    resultList.append(tripe)

                                elif flagATT1 == True and flagATT2 == False:
                                    if tripe[0] == item2.lemma:
                                        tripe[0] = item2AttStr
                                    elif tripe[2] == item2.lemma:
                                        tripe[2] = item2AttStr
                                    resultList.append(tripe)
                                    print("123三元组" + str(tripe))

                                elif flagATT1 == False and flagATT2 == True:
                                    if tripe[0] == item1.lemma:
                                        tripe[0] = item1AttStr
                                    elif tripe[2] == item1.lemma:
                                        tripe[2] = item1AttStr
                                    resultList.append(tripe)
                                    print("456三元组" + str(tripe))

                                elif flagATT1 == True and flagATT2 == True:
                                    resultList.append(tripe)
                                    print("789三元组" + str(tripe))

                                else:
                                    if tripe[0] == item1.lemma:
                                        tripe[0] = item1AttStr
                                    elif tripe[2] == item1.lemma:
                                        tripe[2] = item1AttStr

                                    if tripe[0] == item2.lemma:
                                        tripe[0] = item2AttStr
                                    elif tripe[2] == item2.lemma:
                                        tripe[2] = item2AttStr
                                    resultList.append(tripe)
                    #     for tripe in allTripes:
                    #         if tripe[1]!= "":
                    #             if tripe[0] == item1.lemma:
                    #                 tripe[0] = item1AttStr
                    #
                    #             elif tripe[2] == item1.lemma:
                    #                 tripe[2] = item1AttStr
                    #
                    #             if tripe[0] == item2.lemma:
                    #                 tripe[0] = item2AttStr

                                # elif tripe[2] == item2.lemma:
                                #     tripe[2] = item2AttStr
                                # resultList.append(tripe)






                else:
                    item1AttDict = dict()
                    item1AttDict[item1.ID] = item1
                    flag = True
                    while flag == True:
                        len1 = len(item1AttDict)
                        for item in sentence.words:
                            if item.head_word != None:
                                SUBList = item1AttDict.keys()
                                if item.head_word.ID in SUBList and (
                                        item.dependency == "ATT" ):
                                    if item.dependency == "ATT" and item.postag == "v":
                                        if self.get_entity_num_between(item, item.head_word, sentence) > 0:
                                            continue
                                        else:
                                            SUBATT = item
                                            item1AttDict[SUBATT.ID] = SUBATT
                                    else:
                                        SUBATT = item
                                        item1AttDict[SUBATT.ID] = SUBATT

                            if len(item1AttDict) != len1:
                                flag = True
                            else:
                                flag = False

                    item2AttDict = dict()
                    item2AttDict[item2.ID] = item2

                    flag = True
                    while flag == True:
                        len2 = len(item2AttDict)
                        for item in sentence.words:
                            if item.head_word != None:
                                OBJList = item2AttDict.keys()
                                if item.head_word.ID in OBJList and (
                                        item.dependency == "ADV" or item.dependency == "ATT" or item.dependency == "VOB"\
                                        or item.dependency == "POB"
                                        or (item.dependency == "COO" and item.head_word.ID != item2.ID)):
                                    if item.dependency == "ATT" and item.postag == "v":
                                        if self.get_entity_num_between(item, item.head_word, sentence) > 0:
                                            continue
                                        else:
                                            OBJATT = item
                                            item2AttDict[OBJATT.ID] = OBJATT
                                    else:
                                        OBJATT = item
                                        item2AttDict[OBJATT.ID] = OBJATT
                                        # print(OBJATT.lemma)

                            if len(item2AttDict) != len2:
                                flag = True
                            else:
                                flag = False  # 一直循环，直到找不到新的修饰词


                    item1AttDict = sorted(item1AttDict.items(), key=lambda item: item[0])
                    item1AttStr = ""
                    for item1AttItem in item1AttDict:
                        item1AttStr += item1AttItem[1].lemma

                    item2AttDict = sorted(item2AttDict.items(), key=lambda item: item[0])
                    item2AttStr = ""
                    for item2AttItem in item2AttDict:
                        item2AttStr += item2AttItem[1].lemma
                    # print(item1.lemma)
                    # print(item1AttStr)
                    # print("-------------")
                    # print(item2.lemma)
                    # print(item2AttStr)
                    """
                    考虑到 厉善麟 ---祖父 ---> 厉子嘉
                    与 厉善麟祖父厉子嘉 --- 任内务府都督--->同治时期
                    """
                    flagATT1 = False

                    item1ID = item1.ID
                    beforeItem1Word = sentence.get_word_by_id(item1ID-1)
                    count = 0
                    for item1AttID in range(item1ID-1,-1,-1):
                        item1Att = sentence.get_word_by_id(item1AttID)

                        if item1Att == None:
                            break
                        if count == 0 :
                            if item1Att.dependency == "ATT" and item1Att.head_word.ID == item1.ID and \
                            item1Att.lemma in location_position_list:
                                count = count+1
                                # print("count=0：" + item1Att.lemma)
                            else:
                                break

                        elif count == 1:
                            # print("123" + item1Att.lemma)
                            if item1Att.dependency == "ATT" and item1Att.head_word.head_word.ID == item1.ID:
                                # print("123"+item1Att.lemma)
                                if item1Att.lemma in self.all_entity:
                                # if item1Att.lemma in ["德国","默克尔","美国","奥巴马"]:
                                    count = count+1
                                    flagATT1 = True
                                    # print("count=1"+item1Att.lemma)
                            elif item1Att.lemma == '的':
                                pass
                            else:
                                break

                    flagATT2 = False

                    item2ID = item2.ID
                    beforeItem1Word = sentence.get_word_by_id(item2ID-1)
                    count = 0
                    for item2AttID in range(item2ID-1,-1,-1):
                        item2Att = sentence.get_word_by_id(item2AttID)

                        if item2Att == None:
                            break
                        if count == 0 :
                            if item2Att.dependency == "ATT" and item2Att.head_word.ID == item2.ID and \
                            item2Att.lemma in location_position_list:
                                count = count+1
                                # print("123" + item2Att.lemma)
                            else:
                                break

                        elif count == 1:
                            # print("123" + item1Att.lemma)
                            if item2Att.dependency == "ATT" and item2Att.head_word.head_word.ID == item2.ID:
                                # print("123"+item1Att.lemma)
                                if item2Att.lemma in self.all_entity:
                                    count = count+1
                                    flagATT2 = True
                                    # print("123"+item1Att.lemma)
                            elif item2Att.lemma == '的':
                                pass
                            else:
                                break


                    for tripe in allTripes:
                        if tripe[1]!="":
                            """
                    DSFN1的情况，无需用ATT替换（乾隆，宠臣，和珅） --->（乾隆，宠臣，乾隆宠臣和珅）
                            """
                            if "DSFN1" in tripe[0]:
                                tripe[0] = tripe[0][:-5]
                                resultList.append(tripe)

                            elif flagATT1 == True and flagATT2 == False:
                                if tripe[0] == item2.lemma:
                                    tripe[0] = item2AttStr
                                elif tripe[2] == item2.lemma:
                                    tripe[2] = item2AttStr
                                resultList.append(tripe)
                                print("123三元组"+str(tripe))

                            elif flagATT1 == False and flagATT2 == True:
                                if tripe[0] == item1.lemma:
                                    tripe[0] = item1AttStr
                                elif tripe[2] == item1.lemma:
                                    tripe[2] = item1AttStr
                                resultList.append(tripe)
                                print("456三元组"+str(tripe))

                            elif flagATT1 == True and flagATT2 == True:
                                resultList.append(tripe)
                                print("789三元组"+str(tripe))

                            else:
                                if tripe[0] == item1.lemma:
                                    tripe[0] = item1AttStr
                                elif tripe[2] == item1.lemma:
                                    tripe[2] = item1AttStr

                                if tripe[0] == item2.lemma:
                                    tripe[0] = item2AttStr
                                elif tripe[2] == item2.lemma:
                                    tripe[2] = item2AttStr
                                resultList.append(tripe)
                                print("！！！三元组" + str(tripe))
                    # if len(resultList) > 0:
                    #     return np.array(set([tuple(t) for t in resultList]))
        if item1 == None or item2 == None:
            return None
        if len(resultList) > 0:
            # return np.array(set([tuple(t) for t in resultList]))
            # print("输出结果1"+str(resultList))
            return resultList
    def dsfnStartCOO2(self, sentence, item1, item2,flagCOOATT):
        nounRelatedWithPosition = ['主席', '总理', '教授', '校长']
        resultList = []
        itemCopy1 = item1
        itemCopy2 = item2
        """
        来解决ATT依赖的名词，如 李克强[ATT] <----- 总理[SBV]
        """
        # print(item1.lemma)
        # print(item2.lemma)
        allTripes = self.dsfn1_2_3_4COO(sentence, item1, item2,flagCOOATT)
        if len(allTripes) == 0:
            print("11111111")
            allTripes = self.dsfn5COO(sentence, item1, item2)
            if allTripes == None or len(allTripes) == 0:
                print("2222222")
                allTripes = self.dsfn6COO(sentence, item1, item2)
                if allTripes == None or len(allTripes) == 0:
                    print("3333333")
                    allTripes = self.dsfn5and6COO(sentence, item1, item2)
                    # if allTripes == None or len(allTripes) == 0:
                    #     print("44444444444")
                    #     allTripes = self.dsfnAttCOO(sentence,item1,item2)
        print("第一次"+str(allTripes))
        if allTripes != None and len(allTripes) != 0:
            for tripe in allTripes:
                resultList.append(tripe)
        # print("第二次")
        pred1 = None
        subForCoo = None
        for item in sentence.words:
            if item.postag == "v" and item.dependency == "COO":
                pred1 = item.head_word

                for word in sentence.words:
                    if word.dependency == "SBV" and word.head_word.ID == pred1.ID:
                        for phrase in sentence.words:
                            if phrase.dependency == "SBV" and phrase.head_word.ID == item.ID:
                                subForCoo = phrase
                                """
                                清代皇帝鉴赏所用印章，也大多藏在故宫。
                                考虑到，两个动词之间不能有实体存在
                                """
                        if (subForCoo == None or (
                                subForCoo != None and subForCoo.ID == word.ID)):  # 处理动词COO的情况，必须要保证此并列动词没有额外主语。
                            # 考虑到：习近平主席视察厦门，李克强总理访问香港
                            print(word.lemma+"????????"+item.lemma+"---"+pred1.lemma)
                            word.head_word = item
                            print(sentence.to_string())
                            print("<--->")
                            # print(sentence.to_string())
                            # print(item1.lemma)
                            # print(item2.lemma)
                            allTripes = self.dsfn1_2_3_4COO(sentence, item1, item2,flagCOOATT)
                            if len(allTripes) == 0:
                                # print("11111111")
                                allTripes = self.dsfn5COO(sentence, item1, item2)
                                if allTripes == None or len(allTripes) == 0:
                                    # print("2222222")
                                    allTripes = self.dsfn6COO(sentence, item1, item2)
                                    if allTripes == None or len(allTripes) == 0:
                                        # print("3333333")
                                        allTripes = self.dsfn5and6COO(sentence, item1, item2)
                                        # if allTripes == None or len(allTripes) == 0:
                                        #     allTripes = self.dsfnAttCOO(sentence,item1,item2)
                            # print("第二次"+str(allTripes))
                            word.head_word = pred1
                            print(sentence.to_string())
                            if allTripes != None and len(allTripes) != 0:
                                for tripe in allTripes:
                                    resultList.append(tripe)
        # print(np.array(set([tuple(t) for t in resultList])))
        return resultList

    def dsfnConstraints1(self,rawSentence,maxLength):
        """
        :param rawSentence: 原句子
        :param maxLength: 句子的最大长度
        :return: 小于maxLength的长度
        """
        newSentence = []

        if len(rawSentence) <= maxLength:
            newSentence.append(rawSentence)
            return newSentence
        else:
            newSentence = self.splitSentenceByComma(rawSentence)
            return newSentence

    def dsfnConstraints2(self,sentence,item1,item2,allEntities):
        countEntity = 0
        countChar = 0
        for index in range(item1.ID+1, item2.ID):
            word = sentence.get_word_by_id(index)
            countChar += len(word.lemma)
            if word.lemma in allEntities:
                countEntity +=1
        # print(countEntity)
        # print(countChar)
        if countEntity > 3:
            return False
        elif countChar > 12:
            # print(countChar)
            return False
        else:
            return True

    def dsfnConstraints3(self,sentence,item1,item2):
        countChar = 0
        for index in range(item1.ID+1, item2.ID):
            word = sentence.get_word_by_id(index)
            countChar += len(word.lemma)
        if countChar > 5:
            return False
        else:
            return True

    def getSPO(self,sentence,segmentor):
        location_position_list = getAttWord()
        all_result = []
        raw_sentence = []
        RawSentence = sentence
        lemmas = self.segment(sentence,segmentor)
        words = self.postag(lemmas)
        words_netag = self.netag(words)
        sentence = self.parse(words_netag)
        # print(sentence.to_string())
        for itemWord in sentence.words:
            #来找到一个动词，这个动词要么是一句话的HED，要么与一句话的HED是COO的依存关系
            if (itemWord.head_word == None and itemWord.postag == "v" ) or (itemWord.postag == "v" and
                                                                  itemWord.dependency == "COO" and itemWord.head_word.head_word == None)\
                     or (itemWord.postag == "v") :
                relation_verb = itemWord   #将找到的这个动词，作为relation_verb
                relationString = relation_verb.lemma
                # print(relationString)
                if itemWord.head_word==None:
                    # print("1")
                    verbId = itemWord.ID   # 关系动词的ID
                    verbId2 = None
                elif itemWord.head_word.head_word == None:
                    # print("2")

                    verbId = itemWord.ID   #该关系动词的ID
                    if (itemWord.dependency == "COO" ) \
                            or self.get_entity_num_between(itemWord,itemWord.head_word,sentence)==0:
                        verbId2 = itemWord.head_word.ID  # 这句话的HED，用来找SUB
                    else:
                        verbId2 = None
                else:
                    # print("3")
                    verbId = itemWord.ID   #该关系动词的ID
                    if (itemWord.dependency == "COO" )\
                            or self.get_entity_num_between(itemWord,itemWord.head_word,sentence)==0:
                        verbId2 = itemWord.head_word.ID  # 这句话的HED，用来找SUB
                    else:
                        verbId2 = None
                O_dict = dict() #存储所有的Object
                S_dict = dict() #存储所有的Subject
                verb_dict = dict() #存储所有的verb，主要考虑的情况为：习近平主席在北京大学发表演讲
                OBJ = None
                SUB = None
                DSFN3 = dict()
                for item in sentence.words:
                    if item.dependency == "SBV" and item.head_word.ID == verbId: #寻找这个动词的主语
                        # if SUB == None or SUB.lemma != entity:
                        """
                        Constraint4:如果E1是一个动词的主语，那么E1和该动词之间应该没有其他词也作为主语，修饰该动词
                        """
                        constraint4 = True
                        for word in sentence.words:
                            if word != None and word.ID > item.ID and word.ID <= verbId and word.dependency == "SBV" and word.head_word.ID ==verbId:
                                constraint4 = False
                        if constraint4 == True:
                            SUB = item #找到主语
                            S_dict[SUB.ID] = SUB.lemma #将主语加入到字典中

                    if (item.dependency == "VOB" and item.head_word.ID == verbId and item.postag!= "v"):
                        # 找到这个动词的宾语，其中包括：直接宾语，介词宾语（该宾语依赖POB---->介词(词性为p)--ADV or CMP-->动词）
                        OBJ = item
                        O_dict[OBJ.ID] = OBJ.lemma
                        relationString = relation_verb.lemma
                        objDict = dict()
                        wordAfterOBJ = sentence.get_word_by_id(OBJ.ID+1)
                        if wordAfterOBJ!=None and wordAfterOBJ.lemma == '为' and wordAfterOBJ.postag == "v" and \
                            wordAfterOBJ.dependency == 'COO' and wordAfterOBJ.head_word.ID == verbId:
                            for word in sentence.words:
                                if word.dependency == "VOB" and word.head_word.ID == wordAfterOBJ.ID:
                                    objDict[word.ID] = word.lemma
                            flagLoop = True
                            while flagLoop == True:
                                len1 = len(objDict)
                                for word in sentence.words:
                                    if word.head_word!=None and (word.dependency=="ATT" or word.dependency == "FOB")\
                                        and word.head_word.ID in objDict:
                                        objDict[word.ID] = word.lemma
                                    if len1!=len(objDict):
                                        flagLoop = True
                                    else:
                                        flagLoop = False
                            objDict = sorted(objDict.items(),key=lambda item:item[0])
                            objectStr = ""
                            for objItem in objDict:
                                objectStr+=objItem[1]

                            verb_dict[OBJ.ID] = relationString + wordAfterOBJ.lemma+objectStr
                        else:
                            verb_dict[OBJ.ID] = relationString


                    if (item.dependency == "POB" and item.head_word.postag == "p" and item.head_word.dependency == "CMP"
                                and item.head_word.head_word.ID== verbId ) :
                        # 找到这个动词的宾语，其中包括：直接宾语，介词宾语（该宾语依赖POB---->介词(词性为p)--ADV or CMP-->动词）
                        OBJ = item
                        O_dict[OBJ.ID] = OBJ.lemma
                        relationString = relation_verb.lemma + "" + item.head_word.lemma
                        verb_dict[OBJ.ID] = relationString

                    if (item.dependency == "POB" and (item.head_word.postag == "p" or item.head_word.postag == 'd')\
                            and item.head_word.dependency == "ADV" and item.head_word.head_word.ID == verbId \
                            and item.postag!='v'):
                        # 找到这个动词的宾语，其中包括：直接宾语，介词宾语（该宾语依赖POB---->介词(词性为p)--ADV or CMP-->动词）

                        """
                        constraint5:在DSNF3中，介词短语选择离动词最近的一个                
                        """
                        constraint5 = True
                        # for eachWord in sentence.words:
                        #     if eachWord.ID > item.ID and eachWord.ID <= verbId and eachWord.dependency == "POB" \
                        #         and eachWord.head_word.dependency == "ADV" and eachWord.head_word.head_word.ID == verbId \
                        #         and item.postag!='v':
                        #             constraint5 = False

                        if constraint5==True:

                            OBJ = item
                            O_dict[OBJ.ID] = OBJ.lemma
                            verbObj = None
                            DSFN3[OBJ.ID] = True
                            objectDict = dict()
                            relationString = relation_verb.lemma
                            flagCMP = True
                            for eachWord in sentence.words:
                                if eachWord.dependency == "VOB" and eachWord.head_word.ID == relation_verb.ID:
                                    # relationString = relation_verb.lemma + "" + eachWord.lemma
                                    verbObj = eachWord
                                    objectDict[verbObj.ID] = verbObj
                                    flagCMP = False
                                    """
                                    考虑“颐和园经国家旅游局正式批准为国家5A级旅游景区”
                                    """
                            if flagCMP == True:
                                for eachWord in sentence.words:
                                    if eachWord.dependency == "CMP" and eachWord.head_word.ID == relation_verb.ID:
                                        # relationString = relation_verb.lemma + "" + eachWord.lemma
                                        relationString = relation_verb.lemma + "" + eachWord.lemma
                                        verbCMP = eachWord
                                        objectDict[verbCMP.ID] = verbCMP
                                        for eachWord2 in sentence.words:
                                            if (eachWord2.dependency == "VOB" or eachWord2.dependency == "POB")\
                                                    and eachWord2.head_word.ID == verbCMP.ID:
                                                # relationString = relation_verb.lemma + "" + eachWord.lemma
                                                verbObj = eachWord2
                                                objectDict[verbObj.ID] = verbObj

                            if verbObj != None:
                                flagLoop = True
                                while flagLoop == True:
                                    len1 = len(objectDict)
                                    for word in sentence.words:
                                        if word.head_word != None and word.dependency == "ATT" and word.head_word.ID in objectDict:
                                            objectDict[word.ID] = word
                                    if len(objectDict) != len1:
                                        flagLoop = True
                                    else:
                                        flagLoop = False
                                objectDict = sorted(objectDict.items(), key=lambda item: item[0])
                                objectStr = ""
                                for objectItem in objectDict:
                                    objectStr += objectItem[1].lemma
                                relationString = relation_verb.lemma + "" + objectStr

                            else:
                                for eachWord in sentence.words:
                                    if eachWord.dependency == "POB" and eachWord.head_word.dependency == "CMP" and \
                                            eachWord.head_word.head_word.ID == relation_verb.ID:
                                        relationString = relation_verb.lemma + "" + eachWord.head_word.lemma + "" + eachWord.lemma

                            verb_dict[OBJ.ID] = relationString


                if SUB == None:#如果没找到主语，那么就找与该动词并列的verbId2的主语
                    for item in sentence.words:
                        if item.dependency == "SBV" and item.head_word.ID == verbId2:
                            # if SUB == None or SUB.lemma != entity:
                            # if SUB == None or SUB.lemma != entity:
                            """
                            Constraint4:如果E1是一个动词的主语，那么E1和该动词之间应该没有其他词也作为主语，修饰该动词
                            """
                            constraint4 = True
                            for word in sentence.words:
                                if word != None and word.ID > item.ID and word.ID <= verbId2 \
                                        and word.dependency == "SBV" and word.head_word.ID == verbId2:
                                    constraint4 = False
                            if constraint4 == True:
                                SUB = item
                                S_dict[SUB.ID] = SUB.lemma
                # print(verbId2)
                if OBJ == None:
                    verb_coo = None
                    for item in sentence.words:
                        if item.dependency == "COO" and item.head_word.ID == verbId and item.ID > verbId:
                            verb_coo = item
                            break
                    flag = True
                    if verb_coo != None and self.get_entity_num_between(relation_verb,verb_coo,sentence) == 0:

                        for item in sentence.words:
                            if item.dependency == "SBV" and item.head_word.ID == verb_coo.ID:#若verb_COO有自己的主语，那么可能就不适合
                                flag = False
                        if flag!= False:
                            for item in sentence.words:
                                if (item.dependency == "VOB" and item.head_word.ID == verb_coo.ID and item.postag!='v')\
                                        or (item.dependency == "POB" and item.head_word.postag == "p" and item.head_word.dependency == "CMP"
                                and item.head_word.head_word.ID== verb_coo.ID) or (item.dependency == "POB" and item.head_word.postag == "p"\
                        and item.head_word.dependency == "ADV" and item.head_word.head_word.ID== verb_coo.ID):

                                    OBJ = item
                                    O_dict[OBJ.ID] = OBJ.lemma
                # print(S_dict)
                # print(verb_dict)
                # print(O_dict)
                SUB_COO = None
                OBJ_COO = None
                for item in sentence.words:
                    if item.head_word != None:
                        if SUB != None and item.dependency == "COO" and item.head_word.ID  in S_dict: #获得主语的COO
                            SUB_COO = item
                            S_dict[SUB_COO.ID] = SUB_COO.lemma
                    if item.head_word != None and OBJ!=None:
                        if item.dependency == "COO" and item.head_word.ID in O_dict: #获得宾语的COO
                            OBJ_COO = item
                            O_dict[OBJ_COO.ID] = OBJ_COO.lemma
                            if OBJ_COO.head_word.ID in verb_dict:
                                verb_dict[OBJ_COO.ID] = verb_dict[OBJ_COO.head_word.ID]
                S_new = []

                for sub in S_dict:
                    # if sentence.get_word_by_id(sub).postag == 'r':
                    #     continue
                    S_dict2 = dict()  # 存放主语ATT的列表
                    S_dict2[sub] = S_dict[sub]
                    flag = True
                    while flag == True:
                        len1 = len(S_dict2)
                        for item in sentence.words:
                            if item.head_word != None:
                                SUBList = S_dict2.keys()
                                if item.head_word.ID in SUBList and (item.dependency == "ATT"):
                                    if item.dependency == "ATT" and item.postag == "v":
                                        if self.get_entity_num_between(item,item.head_word,sentence)>0:
                                            continue
                                        else:
                                            SUBATT = item
                                            S_dict2[SUBATT.ID] = SUBATT.lemma
                                    else:
                                        SUBATT = item
                                        S_dict2[SUBATT.ID] = SUBATT.lemma

                            if len(S_dict2) != len1 :
                                flag = True
                            else:
                                flag = False

                    S_dict2 = sorted(S_dict2.items(), key=lambda item: item[0])
                    print(S_dict2)
                    if len(S_dict2)==3 and S_dict2[0][1] in self.all_entity:
                        if S_dict2[1][1] in location_position_list:
                            if S_dict2[2][1] in self.all_entity:
                                S_dict2 = [[S_dict2[2][0],S_dict2[2][1]]]

                    if len(S_dict2)==4 and S_dict2[0][1] in self.all_entity:
                        if (S_dict2[1][1] in location_position_list and S_dict2[2][1] in location_position_list)\
                                or S_dict2[1][1]+S_dict2[1][1] in location_position_list:
                            if S_dict2[3][1] in self.all_entity:
                                S_dict2 = [[S_dict2[3][0],S_dict2[3][1]]]



                    Subject = ""
                    for i in S_dict2:
                        Subject += i[1]
                    S_new.append(Subject)

                O_new = []
                V_new = []
                for obj in O_dict:
                    # if sentence.get_word_by_id(obj).postag == 'r':
                    #     continue
                    O_dict2 = dict()  # 存放宾语ATT的列表
                    O_dict2[obj] = O_dict[obj]
                    if verb_dict!=None:
                        if obj in verb_dict:
                            relationString2  = verb_dict[obj]
                        else:
                            relationString2 = relation_verb.lemma
                    else:
                        relationString2 = relation_verb.lemma
                    V_new.append(relationString2)
                    flag = True
                    while flag == True:
                        len2 = len(O_dict2)
                        for item in sentence.words:
                            if item.head_word != None:
                                OBJList = O_dict2.keys()
                                if item.head_word.ID in OBJList and \
                                        (item.dependency == "ADV" or item.dependency == "ATT" or item.dependency == "VOB" or item.dependency == "POB"
                                        or (item.dependency == "COO" and item.head_word.ID != obj)):
                                    if item.dependency == "ATT" and item.postag == "v":
                                        print("1232312132131"+item.lemma)
                                        if self.get_entity_num_between(item,sentence.get_word_by_id(item.head_word.ID),sentence)>0:
                                            continue
                                        else:
                                            OBJATT = item
                                            O_dict2[OBJATT.ID] = OBJATT.lemma
                                    else:
                                        OBJATT = item
                                        O_dict2[OBJATT.ID] = OBJATT.lemma
                                        # print(OBJATT.lemma)

                            if len(O_dict2) != len2:
                                flag = True
                            else:
                                flag = False #一直循环，直到找不到新的修饰词
                    O_dict2 = sorted(O_dict2.items(), key=lambda item: item[0])

                    print(O_dict2)
                    if len(O_dict2) == 3 and O_dict2[0][1] in self.all_entity:
                        if O_dict2[1][1] in location_position_list:
                            if O_dict2[2][1] in self.all_entity:
                                O_dict2 = [[O_dict2[2][0], O_dict2[2][1]]]
                    if len(O_dict2)==4 and O_dict2[0][1] in self.all_entity:
                        if (O_dict2[1][1] in location_position_list and O_dict2[2][1] in location_position_list)\
                                or O_dict2[1][1]+O_dict2[1][1] in location_position_list:
                            if O_dict2[3][1] in self.all_entity:
                                O_dict2 = [[O_dict2[3][0],O_dict2[3][1]]]
                    Object = ""
                    for i in O_dict2:
                        Object += i[1]
                    flag = False
                    # if obj in DSFN3:
                    #     for location in self.location_entity:
                    #         if location in Object :
                    #             flag = True
                    #     if flag == True:
                    #         O_new.append(Object)
                    #     if flag == False:
                    #         O_new.append("")
                    # else:
                    O_new.append(Object)
                # print(O_dict)
                # print(O_new)

                for sub in S_new:
                    for i in range(0,len(O_new)):
                        obj = O_new[i]
                        relationWord = V_new[i]
                        if obj != "":
                            # print(RawSentence)
                            # print((sub, relationWord, obj))
                            all_result.append([sub,relationWord,obj])
                            raw_sentence.append(RawSentence)

        return all_result,raw_sentence

    def hasEntity(self,word,allEntity):
        for entity in allEntity:
            if entity in word:
                # print(entity)
                return True
        return False

    def PostProcessSPO(self,rawSentence,allTripes,allEntity):
        output_list = []
        for i in range(0,len(allTripes)):
            tripe = allTripes[i]
            sub = tripe[0]
            obj = tripe[2]
            # print(sub)
            # print(obj)
            if self.hasEntity(sub,allEntity) and self.hasEntity(obj,allEntity):
                output_list.append(tripe)
        return output_list



"""
考虑到一句话越长，则LTP的效果越不好
"""
if __name__ == '__main__':
    dsfn = DSFN()

    # 分词测试
    print('***' + '分词测试' + '***')
    allSentence = []
    outputDict = dict()
    fileList = ['5A_恭王府.txt',"5A_北京故宫博物院.txt","5A_颐和园.txt","5A_天坛公园.txt","5A_慕田峪长城.txt"]
    for fileName in fileList:
        f = open('D:\python-file\北京市旅游知识图谱\\verb-entity\\bj_travel\\' + fileName
                 , 'r', encoding='utf-8')
        file = f.read()
        #    print(file)
        json_file = json.loads(file)  # 转化为json格式
        text = json_file.get("text")  # 读取text
        sentence_list = dsfn.splitSentence(text)  # 将text分为句子列表
        # print(sentence_list)

        f = open('..\\..\\entity_verb\\entity_verb_result\\' + "all_entity.json"
                 , 'r', encoding='utf-8')
        file = f.read()
        all_entity = json.loads(file)['all_entity']
        new_sentence = []
        # sentence_list = ["德国总统高克访问上海，并在同济大学发表演讲","乔丹是美国职业篮球运动员，出生在纽约","托马斯在肯德基吃早餐",
        #                  "牙买加运动员博尔特击败了美国选手加特林，在里约奥运会再次夺得金牌"]
        # all_entity = ['德国','高克','上海','同济大学',"乔丹","运动员","纽约","托马斯","肯德基","牙买加","博尔特","美国","加特林","里约奥运会",]

        sentence_list = ["燔柴炉是举行冬至祭天大典望燎仪时焚烧祭祀正位（皇天上帝）供奉物用的",
                         # "中国国家主席习近平访问埃及"
                         ]
        # # # #
        # all_entity = ["中国","习近平","小王","埃及"]

        count = 0
        allTripesForGraph = []
        noBlankInSentence = []
        for sentence in sentence_list:
            if " " in sentence:
                splitSentence = sentence.split(" ")
                for eachSentence in splitSentence:
                    if len(eachSentence)!=0:
                        noBlankInSentence.append(eachSentence)
            else:
                noBlankInSentence.append(sentence)
        for sentence in noBlankInSentence:

            sentenceListConstraint1 = dsfn.dsfnConstraints1(sentence,40)
            for sentenceConstraint1 in sentenceListConstraint1:

                print(sentenceConstraint1)
                final_result_tripe = []

                b = sentenceConstraint1.split()
                sentenceConstraint1 = "".join(b)
                # print(dsfn.dsfnStart(sentenceConstraint1, "颐和园", "万寿山", all_entity))
                for index1 in range(0, len(all_entity)):
                    if all_entity[index1] not in sentenceConstraint1:
                        continue
                    for index2 in range(index1 + 1, len(all_entity)):
                        if all_entity[index2] not in sentenceConstraint1:
                            continue
                        print(all_entity[index1])
                        print(all_entity[index2])
                        print("-------------------------")
                        tripesDSFNUser = dsfn.dsfnStart(sentenceConstraint1,dsfn.segmentor_user, all_entity[index1], all_entity[index2],all_entity)
                        print(tripesDSFNUser)
                        # tripesDSFNNo = dsfn.dsfnStart(sentenceConstraint1,dsfn.segmentor, all_entity[index1], all_entity[index2],all_entity)
                        # print("----------------------")
                        # print(all_entity[index1])
                        # print(all_entity[index2])
                        # print(tripesDSFNUser)
                        # print("-----------------------------------------")
                        # print(tripesDSFNNo)
                        if tripesDSFNUser != None and len(tripesDSFNUser)!= 0:
                            # print(tripes)
                            result_tripe = []
                            for tripe in tripesDSFNUser:
                                result_tripe.append(tripe[0])
                                result_tripe.append(tripe[1])
                                result_tripe.append(tripe[2])
                                final_result_tripe.append(tripe)

                        # if tripesDSFNNo != None and len(tripesDSFNNo)!= 0:
                        #     # print(tripes)
                        #     result_tripe = []
                        #     for tripe in tripesDSFNNo:
                        #         result_tripe.append(tripe[0])
                        #         result_tripe.append(tripe[1])
                        #         result_tripe.append(tripe[2])
                        #         final_result_tripe.append(tripe)
                allTripes_user, raw_sentence = dsfn.getSPO(sentenceConstraint1,dsfn.segmentor_user)
                # allTripes_no_user, raw_sentence = dsfn.getSPO(sentenceConstraint1, dsfn.segmentor)
                print("SPO产生的结果"+str(allTripes_user))
                PostTripes_user = dsfn.PostProcessSPO(raw_sentence, allTripes_user, all_entity)
                if PostTripes_user!=None and len(PostTripes_user)!=0:
                    for tripe in PostTripes_user:
                        final_result_tripe.append(tripe)
                # PostTripes_no_user = dsfn.PostProcessSPO(raw_sentence, allTripes_no_user, all_entity)
                # if PostTripes_no_user != None and len(PostTripes_no_user) != 0:
                #     for tripe in PostTripes_no_user:
                #         final_result_tripe.append(tripe)
                    # print(sentenceConstraint1)
                    # print(PostTripes)
                # print("最终结果")
                if len(final_result_tripe) != 0:
                    # print(sentenceConstraint1)
                    # print("----------------------------------------------------")
                    # print(allTripes_user)
                    # print(allTripes_no_user)


                    # result = set([tuple(t) for t in final_result_tripe])


                    # if len(result) == 3:
                    # result = removeTheSame2(result)
                    for result in final_result_tripe:
                        allTripesForGraph.append(result)
                    # outputAsGraph(result)
                    # print(result.shape)
                    # print(final_result_tripe)
                    # print(len(str(result)))
                    # count += len(str(result))
        # print(count)
        print(allTripesForGraph)



        outputDict['result'+fileName] = allTripesForGraph



    now = str(datetime.datetime.now().year) + "" + str(datetime.datetime.now().month) \
          + str(datetime.datetime.now().day) + str(datetime.datetime.now().hour) + str(
        datetime.datetime.now().minute) + str(datetime.datetime.now().second) \
          + str(datetime.datetime.now().microsecond)
    # with open('outputTripes\\带所有修饰-all-9.6-constraints4-inverse-SPOVerbDict-' + now+".json", 'w',
    #           encoding='utf-8') as json_file:
    #     json_file.write(json.dumps(outputDict, ensure_ascii=False))
    # outputAsGraphForList(allTripesForGraph)
    # outputAsGraphForList(allTripesForGraph)
    # print(mapEntity(allTripesForGraph,all_entity))
    # outputAsGraphForSet(mapEntity(allTripesForGraph,all_entity))
    # print(len(mapEntity(allTripesForGraph,all_entity)))
    dsfn.close()