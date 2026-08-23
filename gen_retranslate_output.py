# -*- coding: utf-8 -*-
"""生成 need_retranslate_translated.csv 并自检标签多重集合一致性。"""
import csv
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
SRC = BASE / "need_retranslate.csv"
OUT = BASE / "need_retranslate_translated.csv"

# {行号: 译文} —— 所有 [...] 标记逐字保留，{...} 内文字翻译、括号保留
T = {
    14: "等等，是[i]她[/i]放的火？",
    46: "我无意冒昧叨扰您这般有身份的[Player:man/woman]，但您着实令我着迷。您可愿考虑对我施以援手？",
    209: "不。他们知道咱们要来，可料不到来的会是[i]咱们[/i]。",
    985: "平息他们的路只有[i]一条[/i]——[i]献祭。[/i]",
    1023: "[Follower01:Name]揉着[Follower01:his/her]眼睛，像是要把里头的阳光全挤出去似的。",
    1032: "[Random01:Name]伸长[Random01:his/her]脖子，想望过那些棚屋去。",
    1494: "他把[i]你[/i]也算进去了？可——呵。也罢，那便如此吧。",
    1590: "[i]倘若[/i]我们盘算的是通商……",
    1611: "约斯泰因[i]吹牛大王[/i]——这便是旁人惯常对你的称呼。",
    1720: "[Unlucky:Name]总算寻到一处足够稳当的立足点，[Unlucky:he/she]这才得以甩脱[Unlucky:his/her]背上的行囊。",
    1770: "请容许我第一个以您真正的尊号向您致意——[i]陛下[/i]。",
    1846: "[Laugher:Name]放声大笑，[Laugher:he/she]一边为[Stuck:Name]叫好助威。",
    1883: "[Eater:Name]硬是吃完了堆得冒尖的两大份，才仰身靠去，发出一声响亮的呻吟。[Eater:He/She]打了个嗝，那一瞬间的神情，仿佛[Eater:he/she]随时都要吐出来。",
    2049: "[Stuck:Name]在泥淖中奋力挣扎，却无济于事。尽管[Stuck: his/her]使出了浑身解数，[Stuck:Name]还是只在泥里越陷越深。",
    2163: "[Unlucky:He/She]失了[Unlucky:his/her]立足之处，顺着崖壁滑落下去，却在坠入[Unlucky:his/her]死劫之前，死死抓住了一处凸起。",
    2172: "你让[Victim:him/her]把[Victim:himself/herself]擦干，裹着毯子坐了许久，直到众人都准备好继续赶路。",
    2458: "[Eater:Name]呼哧呼哧地喘着粗气，[Eater:he/she]死命把食物往嘴里塞。[Eater:He/She]先瞥了努基一眼，又看向你——[Eater:his/her]脸上满是绝望。",
    2495: "[Query:Name]走到你坐处近旁，[Query:his/her]眉头紧锁。",
    2509: "[Random01:Name]用[Player:his/her]脚尖捅了捅国王的尸身。",
    3082: "[CaptainObvious:Name]低头瞅着[CaptainObvious:his/her]脚，活像[CaptainObvious:he/she]踩着了什么腌臜东西。",
    3154: "[Sherlock:Name]用[Sherlock:his/her]手掩住了[Sherlock:his/her]嘴。",
    3167: "统治者的唯一责任，便是对[Player:his/her]子民负责。",
    3220: "不过转瞬之间，[Rescuer:Name]猛然破水而出，[Victim:Name]被拖在[Rescuer:him/her]身后。",
    3422: "[Joker:Name]冲[Buzzkill:Name]促狭地咧嘴一笑，后者正费劲地够着[Buzzkill:his/her]背上发痒的地方。",
    3694: "[Buzzkill:Name]转过身去，好让[Joker:Name]够到[Buzzkill:his/her]背上发痒的地方。",
    3853: "不幸的是，[Repairer:Name]——[Repairer:his/her]的手艺素来谈不上灵巧——最终弄伤了[Repairer:his/her]手。",
    3943: "仿佛熬过了万古之久，[Rescuer:Name]终于破水而出，[Victim:Name]被拖在[Rescuer:him/her]身后。",
    4699: "哼，[i]那根[/i]绳子看起来[i]半点儿[/i]也不可疑。",
    5286: "[Impressed:Name]看上去简直连[Impressed:his/her]下巴的肌肉都管不住了。",
    5591: "你在山间的跋涉一路还算太平。[Klutz:Name]正贴着岩架，小心翼翼地择着[Klutz:his/her]归路，就在这时，一道掠食的暗影自上方巉岩间猛扑而下，羽影与动作模糊成一片。",
    5623: "[Scout:Name]结束了[Scout:his/her]巡逻归来，报告说没有发现那猎人的踪迹。",
    5689: "[Player:He/She]杀了斯泰因！你这[Player:bikkju-sonr/bikkja]！",
    5696: "准还有[i]什么法子[/i]是咱没试过的。",
    5734: "[Finder:Name]一脸难以置信地盯着你，可当[Finder:his/her]目光对上你的眼睛，[Finder:he/she]看出了你话语中的决绝。[Finder:He/She]把[Finder:his/her]小刀抵上奴隶的脖颈，割开了这年轻人的喉咙。",
    5910: "嘿，近来可好？",
    6110: "你挑的使者着实有些古怪，可我终究还是瞧出了其中的明智。若你派来的是[i]能耐[/i]稍逊之辈……只怕我今日便不会站在你面前了。",
    6741: "那是[i]我的[/i]事，斯库勒。",
    6760: "啊！哦，我亲爱的[Player:boy/girl]，你还活着，我真是太欢喜了！",
    6906: "你和你的侍卫各自挑了一名袭击者搜身。[Finder:Name]举起[Finder:his/her]手，指间捏着一样在光下微微闪亮的东西。",
    7138: "这就是那种遭[i]诅咒的[/i]恶疾！我必须做点什么——我们[i]非得[/i]把它彻底根除不可！",
    7153: "你觉得[i]那[/i]也算重击？！呸！",
    7166: "那话我不知该怎么说。他们的意思我听得懂，可我[i]说[/i]不来那门话！",
    7168: "喔！那[i]到底[/i]是个什么？莫不是[i]金子[/i]？",
    7177: "午夜前后我瞧见她离开，只当她是去打猎。如今细想，她[i]当时[/i]带的东西可真不少。",
    7255: "你？！他居然派[i]你[/i]来担保此事？！看在诸圣的名分上，他怎会觉得[i]这[/i]能行得通？",
    7276: "你这[i]贱人！[/i]",
    7759: "[Insulted:Name]压低了[Insulted:his/her]嗓子咕哝着。",
    7766: "操，他们究竟把你[i]怎么着了[/i]？",
    7775: "哈！说句掏心窝子的话，如今可是那小子养着[i]我[/i]，压根轮不着我养他。",
    7810: "就[i]一身[/i]换洗衣裳？",
    7870: "[Archer01:Name]抱起[Archer01:his/her]双臂，[Archer01:his/her]声音里透出一丝懊恼。",
    8047: "[Drinker:Name]呛住了，麦酒喷溅出杯沿。[Drinker:He/She]猛地把杯子甩到一旁，[Drinker:he/she]被一阵剧咳攫住，向前扑倒，[Drinker:his/her]双手双膝撑地。涕泪顺着[Drinker:Name]的脸横流，[Drinker:he/she]大口大口地喘着气。",
    8327: "若此言属实，赫罗德盖尔达的行径必叫斯库勒领主颜面扫地。我这就差人把那首领押来，我要听[i]他[/i]亲口说出这些话。",
    8528: "[Cougher:Name]浮出水面时咳出了特别大的一口水，[Cougher:he/she]每咳一声便大口喘气。[Cougher:He/She]游完这一趟，脸色瞧着糟透了。",
    8954: "诸神在上，她见我这般模样，[i]简直[/i]乐开了花。这事儿她准得念叨一辈子。",
    9513: "把东西给[Player:him/her]便是，诺特。你用不上它，没有它你照样能打。",
    9778: "[Drinker:Name]大口灌着麦酒，[Drinker:he/she]被呛得直喘。[Drinker:He/She]只得暂把杯子放低，拼命顺气——[Drinker:his/her]脸上满是绝望。",
    10084: "[Pessimist:Name]毫不掩饰地翻了翻[Pessimist:his/her]白眼。",
    10332: "[Stuck:Name]被猛地拽脱出来，[Stuck:he/she]顿失[Stuck:his/her]平衡，朝前踉跄了几步，一头栽倒在地。",
    10341: "终于，[Fisher:Name]筋疲力尽，钓线自[Fisher:his/her]指间滑脱，那头海中巨物就此消失在波涛之下。",
    10519: "[Lover:Name]在[Lover:his/her]睡梦中翻了个身，含糊地呢喃了几句宽慰的话。[Lover:His/Her]手在黑暗中摸索着，寻到了你的手，虚弱地握了握。",
    10543: "斯基恩的领主[Player:Name][Player:Lastname]与[Player:his/her]麾下骁勇的战士们，为这个王国立下了汗马功劳。鉴于此，[Player:Name]，我立誓支持你出征日德兰。",
    10551: "哦，唔……这个嘛。如今细想，我听说上游那段儿做陶器的姑娘苏森，跟卡尔特拉姆有[i]一腿[/i]。",
    10646: "谁是[i]我们[/i]？[i]你[/i]又是谁？！",
    10658: "告诉我：你[i]究竟[/i]打算如何治理我们？",
    10857: "[Initial:Name]手持兵器从船上跳下那几英尺，[Initial:he/she]的靴子陷进了沙里。",
    11548: "[Stuck:Name]在烂泥里奋力挣扎。尽管[Stuck:his/her]处境艰难，[Stuck:he/she]还是借着近旁一根树枝稳住身子，把[Stuck:himself/herself]拔了出来。",
    11580: "你[i]准是在[/i]说笑。",
    11583: "[Player:Velkominn/Velkomin]，欢迎您回来，仁慈的领主。您可是要补充些随行物资？",
    11595: "你管谁叫蛮子呢，[i]贱民！[/i]",
    11656: "这么多当兵的扎在一处，造出来的垃圾可[i]真不少[/i]。",
    11780: "[Slippy:Name]可不是个轻易认怂的人，重新爬起来又试了一次。这一回，[Slippy:he/she]费了九牛二虎之力，总算登上了平台。",
    11822: "哦……？可我本以为卡尔特拉姆早[i]跟[/i]康纳尔在一起了。",
    12207: "你的扈从大多攀了上去，唯独[Slippy:Name]一失[Slippy:his/her]手，跌回底下，摔伤了[Slippy:his/her]腿。",
    12418: "[Random01:Name]挣扎着重新站稳了[Random01:his/her]脚跟。",
    12472: "哦！[i]原来[/i]你是跑那儿去了。",
    12516: "{在决斗圈中面对阿斯莱夫。}您的提议令我不胜荣幸，但这是[i]我自己的[/i]战斗。",
    12766: "匠人们麻利地收拾起家什，由着[CraftsmenEscort:Name]去作[CraftsmenEscort:his/her]道别。",
    12970: "随你的便吧，[i]修士[/i]。",
    12996: "{向[Partner:Name]示意干掉老的，由你来解决小的。}我奉命来给你看这件信物。主教说，你一看自会明白。",
    13391: "你是个明智又通情达理的[Player:man/woman]。我只盼你今日的决定，不会为你招来更多麻烦。",
    13656: "我想，这几个就是[Player:Name]提到的孤儿——是[Player:he/she]在埃塞尔雷德的营地审过那名间谍后说起来的。",
    13767: "[Hurt01:Name]在湿滑的岩架上脚下一滑，险些坠入[Hurt01:his/her]死劫，多亏另一名扈从眼疾手快，及时拽住了[Hurt01:him/her]。",
    13863: "真到了那个地步，总会有更好的解法。阿斯莱夫这人，有骡子的见识[i]更有[/i]骡子的犟劲，可他终究是家人。",
    13871: "[Handler:Name]竭尽[Handler:he/she]所能地处理那两具肿胀的尸体。这名[Handler:archetype]被那股恶臭熏得直往后缩，完事后一脸作呕的模样。",
    13982: "若[Player:he/she]能活下来，落败的[Player:he/she]可向胜者宣誓效忠，否则[Player:his/her]性命便就此抵偿。我二人谁在决斗中倒下，尸身便葬于此地。",
    14066: "[Helper:Name]伸出[Helper:his/her]手，开始用力拖拽。显然，两个人都吃力得很。最终，[Helper:Name]孤注一掷地猛地一拽，总算把[Stuck:Name]拉了出来。",
    14111: "付钱给他们，你这狂妄的[i]nidingr[/i]！[i]否则[/i]……",
    14120: "你[i]果真[/i]是[Player:Father]的[Player:son/daughter]。只是切记，切莫因急切护民，反而忘了体察他们的疾苦。",
    14474: "[Random01:Name]压着[Random01:his/her breath]嘟哝了一句。",
    14740: "[Helper:Name]伸出[Helper:his/her]手，开始用力拖拽。[Stuck:Name]终于被拉了出来，所幸没再出别的岔子。",
    15212: "[Random01:Name]点头应了一声，一个打挺重新站起[Random01:his/her]身来。",
    15297: "这么说，你[i]当真[/i]是在替奥斯雷德做探子。多谢你亲口认下。",
    15336: "[Naysayer:Name]尴尬地清了清[Naysayer:his/her]嗓子。",
    15356: "[ScoutCapturer:Name]急中生智，闪身将[ScoutCapturer:himself/herself]挡在了一名旅伴与其武器之间。",
    15378: "等我亲眼看着所有人都死绝，[i]到那时[/i]我才会跟你走。之后哪怕你带我去天涯海角，我也无所谓。",
    15423: "你要知道，我也是位好领主。[i]你[/i]何不臣服于[i]我[/i]？斯基恩可是个好地方——清新的海风，兴许对你大有好处。",
    15924: "一个矮壮的女人正按某种约莫只有她自己才懂的玄妙章法，把麻袋堆里值钱的零星小件分拣进三只木箱。这些小件瞧着并不沉，可她每拾起一件，都会极轻地发出一声[size=8]“嘿呀”[/size]。",
    16065: "给这么个[i]狗屎[/i]领主办这么气派的宴席！",
    16080: "什么都没了！我如今只剩个[i]一无所有[/i]！",
    16099: "你这[i]bikkju-sonr[/i]！我真该就地把你了结了！",
    16430: "不[i]——咳——[/i]别再打了……我认输……",
    16734: "你用溪水冲掉了树汁，但也仅此而已。[Victim:Name]有些沮丧，[Victim:his/her]脸上浮起痛楚之色，点了点头。你继续处理时，[Victim:He/She]疼得直咧嘴，接下来几个时辰，那片红肿恶化成了一片狰狞的皮疹。",
    17068: "奥塔尔，你这灌饱了黄汤的泼才！你怎[i]敢[/i]在[Player:his/her]自家的宴席上，折辱你家领主的颜面！你的家眷就等着为此偿债吧！",
    17172: "唉，可我也知道，你们这些年轻[Player:men/women]一旦拿定主意，任谁也拦不住。行吧行吧，我来瞧瞧手里有些什么。",
    17195: "[Laugher:Name]瞧着[Stuck:Name]给[Stuck:himself/herself]惹上的这档子麻烦，笑得直不起腰。[Stuck:Name]也跟着讪笑，笑声里却透着一丝绝望。",
    17402: "这破陷阱，连头[i]母牛[/i]都唬不住。",
    17436: "内芙娅，你若是为我而战该多好。若你这回赢了，我只盼[Player:Name]能比[Player:his/her]父亲当个更像样的领主。",
    17539: "[Klutz:Name]一头栽进峡谷，[Klutz:he/she]一路翻滚磕碰，狼狈不堪。",
    17787: "那位隐修士受我等庇护。若你敢动他，定叫你被[i]碾成齑粉[/i]。",
    17855: "你拼尽最后一口气向前一挣，猛地破开水面。等在那儿接应你的正是[Diver:Name]，一边架着你起身，任你咳出呛进的水、大口喘气。瞧得出，这一潜对[Diver:him/her]来说也不轻松。",
    17859: "[Victim:He/She]在水草壅塞的溪流里扑腾着，[Victim:he/she]发出一声懊恼的低吼。这名[Victim:archetype]拨开那又长又阔、叶尖如矛的水草茎，嘴里絮絮叨叨地抱怨着，笨拙地爬回了岸上。",
    17963: "你不记得自己说过的话了？“与其随人俯仰，不如昂然引领。”那可是[i]你的[/i]原话。好了，如今我终于拿定主意，要听从你这番劝告。",
    18173: "三大份下肚，[Eater:Name]已是神情恍惚。[Eater:His/Her]下巴仍在机械地咀嚼，尽管[Eater:his/her]嘴里早已空空如也。",
    18265: "[Eater:Name]打着嗝，身子晃了几晃，随即发疯似的挣扎着想把[Eater:him/her]self从桌边挪开。[Eater:He/She]勉力挪出几步，便猛地弯下腰呕吐起来，秽物混着胆汁与酸臭的食糜淌了一地，恶臭熏人。",
    18611: "[Hunter/Huntress]",
    19300: "[year]年[month]月[daynumber][dayend]日，[day]",
}

TAG = re.compile(r"\[[^\[\]]*\]")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    with open(SRC, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.reader(f) if r and r[0].isdigit()]

    src_map = {int(r[0]): r[1] for r in rows}
    assert set(src_map) == set(T), (
        f"行号覆盖不全: 缺 {sorted(set(src_map) - set(T))}, 多 {sorted(set(T) - set(src_map))}"
    )

    errors = []
    for lineno, src_text in sorted(src_map.items()):
        s_tags = sorted(TAG.findall(src_text))
        d_tags = sorted(TAG.findall(T[lineno]))
        if s_tags != d_tags:
            errors.append((lineno, s_tags, d_tags))

    if errors:
        print(f"[自检失败] {len(errors)} 行标签不一致：")
        for lineno, s, d in errors:
            print(f"  行{lineno}: 原{s}")
            print(f"          译{d}")
        return 1

    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["行号", "原文", "译文"])
        for lineno in sorted(src_map):
            w.writerow([lineno, src_map[lineno], T[lineno]])

    print(f"[成功] {len(T)} 行全部通过标签自检 -> {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
