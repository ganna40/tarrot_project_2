#!/usr/bin/env python3
"""Build the reviewable Tarot Engine v1 CSV package from public-domain sources.

The historical wording is not copied into runtime records. Each meaning is a
short Korean editorial paraphrase tied to an exact source section. Golden Dawn
correspondences are normalized from Book T / Liber LXXVIII (1912).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "backend" / "data" / "curated"


@dataclass(frozen=True)
class TagProfile:
    name_ko: str
    description: str
    metrics: tuple[float, float, float, float, float]
    advice: str
    warning: str | None = None


TAGS: dict[str, TagProfile] = {
    "ABUNDANCE": TagProfile("풍요", "생산성·보살핌·물질적 또는 정서적 풍요", (4, 3, 2, 4, 0), "이미 가진 자원과 성장 조건을 구체적으로 활용하세요."),
    "ABUSE": TagProfile("권력 남용", "힘이나 권한이 해로운 방식으로 사용됨", (-4, 3, 3, 0, 1), "권한과 책임의 경계를 다시 세우세요.", "상대의 권위만으로 판단하지 마세요."),
    "ADAPTATION": TagProfile("적응", "여러 조건을 조율하며 균형을 유지함", (1, 4, 3, 2, 0), "우선순위를 정하고 동시에 다룰 일의 수를 줄이세요."),
    "ANXIETY": TagProfile("불안", "걱정·두려움·심리적 압박", (-4, 0, 0, 0, 0), "사실과 예상 걱정을 분리해 적어보세요.", "불안을 확정된 결과로 받아들이지 마세요."),
    "APATHY": TagProfile("무관심", "권태·싫증·기회에 대한 반응 저하", (-2, 0, 0, 1, 0), "놓치고 있는 선택지가 있는지 한 번 더 살펴보세요."),
    "ATTACHMENT": TagProfile("속박", "욕망·물질·관계에 대한 강한 집착", (-3, 3, 2, 1, 0), "내 선택을 제한하는 욕망이나 이해관계를 확인하세요.", "충동과 필요를 혼동하지 마세요."),
    "AUTHORITY": TagProfile("권위", "규칙·판단·지도력·공식 권한", (2, 3, 2, 4, 0), "권한의 근거와 책임 범위를 문서로 확인하세요."),
    "AWAKENING": TagProfile("갱신", "판단·재평가·새로운 국면으로의 갱신", (3, 3, 3, 3, 2), "지금까지의 결과를 평가하고 다음 기준을 명확히 하세요."),
    "BALANCE": TagProfile("균형", "조화·절제·공정한 균형", (2, 2, 2, 4, 0), "양쪽 조건을 비교해 지속 가능한 중간점을 찾으세요."),
    "BEGINNING": TagProfile("시작", "새로운 가능성·출발·첫 동력", (3, 4, 3, 1, 0), "범위를 작게 잡고 첫 결과물을 만드세요."),
    "BIAS": TagProfile("편향", "불공정·과도한 엄격함·한쪽으로 치우친 판단", (-3, 2, 1, 1, 0), "판단 기준이 모두에게 동일하게 적용되는지 확인하세요."),
    "BREAKTHROUGH": TagProfile("돌파", "강한 결단·승부·문제의 절단", (3, 5, 4, 2, 0), "결정해야 할 핵심 쟁점을 한 문장으로 명확히 하세요.", "힘으로 밀어붙이는 방식이 부작용을 만들 수 있습니다."),
    "BURDEN": TagProfile("부담", "책임·성과·업무가 과도하게 쌓임", (-3, 4, 2, 1, 2), "직접 해야 할 일과 위임할 일을 나누세요.", "성과 욕심 때문에 감당 범위를 넘기지 마세요."),
    "CELEBRATION": TagProfile("축하", "완료·화합·기쁨을 함께 나눔", (4, 4, 3, 4, 1), "완료된 성과를 인정하고 다음 단계의 기준을 정하세요."),
    "CLARITY": TagProfile("명료함", "숨겨진 것이 드러나고 이해가 선명해짐", (3, 3, 3, 3, 1), "새롭게 드러난 사실을 기준으로 계획을 다시 정리하세요."),
    "COMPLETION": TagProfile("완성", "한 주기의 성취·보상·마무리", (5, 3, 2, 5, 4), "완료 기준을 확인하고 다음 주기로 넘어갈 준비를 하세요."),
    "COMPULSION": TagProfile("강박", "강한 힘·충동·피하기 어려운 압력", (-3, 4, 3, 0, 0), "멈추기 어려운 행동의 대가를 먼저 계산하세요.", "운명이나 충동을 책임 회피의 근거로 삼지 마세요."),
    "CONFLICT": TagProfile("갈등", "경쟁·논쟁·마찰·대립", (-2, 5, 4, 1, 0), "싸워야 할 쟁점과 양보 가능한 쟁점을 구분하세요.", "승패에만 집중하면 장기 관계가 손상될 수 있습니다."),
    "CONFORMITY": TagProfile("순응", "집단·관행에 맞추며 개인 기준이 약해짐", (-1, 1, 1, 3, 0), "따라야 할 원칙과 바꿀 수 있는 관행을 구분하세요."),
    "CONTROL": TagProfile("통제", "소유·권력·상황을 붙잡으려는 힘", (0, 2, 1, 4, 0), "지켜야 할 것과 놓아도 되는 것을 분리하세요.", "통제가 경직성으로 변하지 않는지 점검하세요."),
    "CORRUPTION": TagProfile("부패", "능력이나 자원이 왜곡되고 해로운 방향으로 사용됨", (-4, 2, 2, 0, 2), "이익 구조와 책임 소재를 투명하게 확인하세요."),
    "COURAGE": TagProfile("용기", "힘·인내·담대함으로 어려움을 다룸", (4, 4, 3, 3, 0), "힘을 과시하기보다 꾸준히 통제해 사용하세요."),
    "DECEPTION": TagProfile("기만", "거짓·숨김·교묘한 조작", (-3, 3, 3, 0, 0), "말보다 검증 가능한 사실과 기록을 확인하세요.", "확인되지 않은 약속을 믿고 선행하지 마세요."),
    "DEFEAT": TagProfile("패배", "손실·불명예·승부에서의 후퇴", (-4, 1, 2, 0, 3), "손실을 인정하고 더 잃지 않도록 종료 기준을 정하세요."),
    "DELAY": TagProfile("지연", "대기·방해·일정 지연", (-1, 1, 0, 1, 0), "지연 원인과 재개 조건을 명확히 정하세요."),
    "DEPARTURE": TagProfile("떠남", "이동·이탈·기존 관심사에서 벗어남", (0, 3, 3, 1, 2), "떠나는 이유와 도착하려는 목표를 함께 확인하세요."),
    "DETERMINATION": TagProfile("결의", "희망을 실행 가능한 의지와 계획으로 좁힘", (3, 4, 3, 2, 0), "바라는 것을 실행 항목과 기한으로 바꾸세요."),
    "DIMINISHED_JOY": TagProfile("약화된 기쁨", "긍정적 흐름은 남지만 강도가 줄어듦", (2, 2, 2, 3, 0), "좋은 조건을 당연시하지 말고 유지 요인을 확인하세요."),
    "DISCLOSURE": TagProfile("공개", "고백·선언·정보가 밖으로 드러남", (1, 3, 4, 2, 0), "공개할 내용과 시점을 사전에 정리하세요."),
    "DISHARMONY": TagProfile("불화", "관계·이해관계·가치의 충돌", (-3, 3, 2, 1, 1), "합의되지 않은 기대와 역할을 말로 확인하세요."),
    "DISRUPTION": TagProfile("붕괴", "예상 밖의 충격·구조적 파괴", (-4, 4, 5, 0, 4), "무너진 가정과 실제로 남은 자원을 분리하세요.", "충격 속에서 추가 결정을 서두르지 마세요."),
    "DOUBT": TagProfile("의심", "불신·불확실성·확신 부족", (-2, 1, 1, 1, 0), "의심을 해소할 수 있는 증거와 질문을 정하세요."),
    "EMOTION": TagProfile("감정", "정서·공감·마음의 흐름", (2, 2, 2, 2, 0), "감정을 억누르기보다 무엇을 필요로 하는지 확인하세요."),
    "ENDING": TagProfile("종료", "한 국면의 끝·정리·소멸", (-2, 1, 1, 1, 5), "끝내야 할 부분과 남겨야 할 자산을 구분하세요."),
    "EXCESS": TagProfile("과잉", "좋은 것이라도 지나쳐 부담이 됨", (-1, 4, 4, 1, 0), "양을 늘리기보다 적정 수준과 중단 기준을 정하세요."),
    "FAMILY": TagProfile("가정", "가족·공동체·정서적 안정", (4, 2, 2, 5, 1), "공동체가 기대하는 역할과 내가 원하는 역할을 맞춰보세요."),
    "FANTASY": TagProfile("환상", "상상·가능성은 많지만 실체가 약함", (-1, 1, 1, 0, 0), "선택지를 실제 비용·기한·가능성으로 비교하세요.", "매력적인 그림을 실행 가능성으로 착각하지 마세요."),
    "FEAR": TagProfile("두려움", "위험에 대한 경계가 행동을 위축시킴", (-3, 0, 0, 1, 0), "가장 두려운 결과와 그 대응책을 구체화하세요."),
    "FORMALIZATION": TagProfile("공식화", "관계나 계획이 계약·제도·절차로 정리됨", (2, 2, 2, 5, 1), "구두 약속을 역할·기한·조건이 적힌 문서로 바꾸세요."),
    "FORTUNE": TagProfile("운의 전환", "예측하기 어려운 외부 변화와 기회", (4, 3, 5, 2, 1), "기회가 왔을 때 실행할 준비와 손실 한도를 함께 정하세요."),
    "GENEROSITY": TagProfile("나눔", "자원·기회·도움을 주고받음", (3, 3, 2, 4, 0), "주는 조건과 받는 책임을 서로 명확히 하세요."),
    "GREED": TagProfile("탐욕", "소유욕·질투·과도한 욕망", (-3, 3, 2, 0, 0), "필요한 몫과 과도한 욕심을 구분하세요."),
    "HEALING": TagProfile("치유", "회복·위안·상처의 완화", (3, 2, 2, 4, 1), "회복을 확인할 수 있는 작은 변화를 꾸준히 이어가세요."),
    "HIDDEN": TagProfile("숨겨짐", "비밀·침묵·아직 드러나지 않은 정보", (0, 1, 1, 2, 0), "판단 전에 드러나지 않은 정보가 무엇인지 확인하세요."),
    "HOPE": TagProfile("희망", "회복 가능성·밝은 전망·방향성", (4, 3, 2, 4, 0), "희망을 유지할 수 있는 현실적 행동을 하나 정하세요."),
    "ILLUSION": TagProfile("환영", "착각·불분명함·왜곡된 인식", (-2, 1, 1, 0, 0), "추측과 사실을 구분하고 확인 가능한 정보부터 모으세요."),
    "IMPERFECTION": TagProfile("불완전", "성과는 있으나 결함·실수·미완성이 남음", (0, 2, 2, 2, 0), "완벽을 기대하기보다 수정할 결함을 우선순위화하세요."),
    "IMPULSIVITY": TagProfile("충동", "계획보다 즉흥성과 과감함이 앞섬", (-1, 5, 5, 0, 0), "행동 전에 최소한의 손실 한도와 되돌릴 방법을 정하세요.", "흥분 상태에서 장기 약속을 확정하지 마세요."),
    "INDECISION": TagProfile("결정 지연", "상충하는 선택지 사이에서 결정을 미룸", (-1, 0, 0, 2, 0), "결정 기준을 세 가지 이하로 줄이고 기한을 정하세요."),
    "INDEPENDENCE": TagProfile("자립", "스스로 구축한 안정·성과·분별", (4, 3, 2, 5, 0), "성과를 유지할 수 있는 독립적 기반을 강화하세요."),
    "INTUITION": TagProfile("직관", "감수성·통찰·내면의 이해", (3, 2, 1, 3, 0), "직감이 가리키는 바를 기록한 뒤 사실과 대조하세요."),
    "JOY": TagProfile("기쁨", "만족·행복·밝은 성취", (5, 4, 4, 5, 0), "좋은 흐름을 함께 나누고 유지할 조건을 마련하세요."),
    "JUSTICE": TagProfile("공정", "균형 잡힌 판단·책임·정당한 결과", (3, 2, 2, 5, 1), "감정과 별개로 기준·증거·책임을 확인하세요."),
    "LEADERSHIP": TagProfile("지도력", "정직한 지휘·비전·책임 있는 영향력", (3, 4, 3, 4, 0), "목표와 기대 행동을 명확히 전달하세요."),
    "LEARNING": TagProfile("학습", "연구·기술 습득·준비 단계", (2, 2, 2, 3, 0), "배울 내용을 실제 결과물로 연결하는 계획을 세우세요."),
    "LEGACY": TagProfile("유산", "가족·재산·장기적 기반과 전승", (4, 2, 1, 5, 3), "단기 이익보다 오래 남길 구조와 책임을 확인하세요."),
    "LOSS": TagProfile("손실", "상실·실망·남은 것에 대한 재평가", (-4, 1, 1, 0, 3), "잃은 것과 아직 남아 있는 것을 따로 확인하세요.", "손실을 만회하려 같은 선택을 반복하지 마세요."),
    "MASTERY": TagProfile("숙련", "현실적 능력·사업 감각·전문성", (4, 4, 3, 5, 0), "검증된 능력을 구체적인 성과와 책임으로 연결하세요."),
    "MATERIAL_OPPORTUNITY": TagProfile("물질적 기회", "돈·자원·현실적 기반의 새로운 기회", (4, 4, 3, 4, 0), "기회의 실제 가치와 유지 비용을 함께 계산하세요."),
    "MEDIOCRITY": TagProfile("미숙함", "기술·성과·기준이 기대에 미치지 못함", (-2, 1, 1, 1, 0), "부족한 기준을 인정하고 다시 연습할 항목을 정하세요."),
    "MEMORY": TagProfile("회상", "과거·추억·익숙한 관계의 영향", (2, 1, 1, 3, 0), "과거의 좋은 점을 살리되 현재 조건과 같은지 확인하세요."),
    "MESSAGE": TagProfile("소식", "연락·제안·정보의 전달", (2, 3, 4, 2, 0), "소식의 출처와 구체적인 다음 행동을 확인하세요."),
    "MISUSE": TagProfile("오용", "능력·힘·기술이 잘못된 방향으로 쓰임", (-3, 3, 3, 0, 1), "수단이 목적을 해치지 않는지 다시 점검하세요."),
    "MOVEMENT": TagProfile("진행", "빠른 이동·실행·사건의 전개", (3, 5, 5, 2, 0), "속도가 붙기 전에 결정 기준과 담당을 정하세요.", "속도 때문에 조건 검토를 생략하지 마세요."),
    "NURTURE": TagProfile("돌봄", "따뜻함·매력·성장을 돕는 힘", (3, 3, 2, 4, 0), "사람과 자원이 성장할 수 있는 환경을 만드세요."),
    "OFFER": TagProfile("제안", "접근·초대·감정 또는 기회의 제안", (3, 3, 3, 2, 0), "제안의 의도와 실제 조건을 분리해 확인하세요."),
    "OVERINDULGENCE": TagProfile("과도한 향락", "즐거움·감각적 만족이 지나침", (-2, 3, 3, 1, 0), "즐거움의 비용과 다음 날의 책임까지 고려하세요."),
    "PAUSE": TagProfile("정지", "통찰·희생·관점 전환을 위한 멈춤", (0, 0, 0, 2, 2), "기다리는 동안 얻어야 할 정보와 종료 기한을 정하세요."),
    "PLANNING": TagProfile("계획", "영역·가능성·다음 수를 내다봄", (2, 3, 2, 3, 0), "가능성보다 실행 조건과 선택 기준을 먼저 정하세요."),
    "POVERTY": TagProfile("궁핍", "물질적 어려움·소외·지원 부족", (-4, 1, 1, 0, 2), "혼자 버티기보다 이용 가능한 지원과 비용 절감책을 찾으세요."),
    "PRETENCE": TagProfile("가식", "겉으로만 즐겁거나 안정된 모습을 유지함", (-2, 2, 2, 1, 0), "겉모습과 실제 부담 사이의 차이를 인정하세요."),
    "PRUDENCE": TagProfile("신중", "관찰·절약·현명한 관리", (2, 2, 1, 4, 0), "결정 전에 위험·비용·증거를 차분히 확인하세요."),
    "RECOVERY": TagProfile("회복", "어려움 이후 다시 살아나는 흐름", (3, 2, 2, 3, 1), "회복 신호를 확인하고 재발 원인을 정리하세요."),
    "RELATIONSHIP": TagProfile("관계", "사랑·우정·협력·상호 연결", (4, 3, 2, 4, 0), "서로 기대하는 바와 실제 약속을 직접 확인하세요."),
    "RENEWAL": TagProfile("새로움", "미래·재생·새로운 관계나 환경", (3, 3, 3, 3, 1), "과거 방식에 머물지 말고 새 조건에 맞는 행동을 정하세요."),
    "RESPONSIBILITY": TagProfile("책임", "성실·실용성·맡은 일을 꾸준히 수행함", (3, 3, 1, 5, 0), "작은 약속을 일정하게 지키며 신뢰를 쌓으세요."),
    "REST": TagProfile("휴식", "활동을 멈추고 힘을 회복하거나 거리를 둠", (1, 0, 0, 3, 1), "회복에 필요한 시간과 다시 움직일 조건을 정하세요."),
    "RESTRICTION": TagProfile("제약", "현실적·심리적 제한과 억압", (-3, 1, 1, 1, 1), "바꿀 수 있는 제한과 바꿀 수 없는 제한을 구분하세요.", "제약을 영구적인 운명으로 단정하지 마세요."),
    "RETURN": TagProfile("귀환", "사람·소식·과거의 문제가 다시 돌아옴", (1, 2, 3, 2, 1), "돌아온 것이 실제로 달라졌는지 조건을 확인하세요."),
    "RIGIDITY": TagProfile("경직", "통제·규칙·태도가 지나치게 굳어짐", (-2, 1, 0, 3, 0), "원칙을 지키면서도 수정 가능한 부분을 찾으세요."),
    "SACRIFICE": TagProfile("희생", "기다림·관점 전환·대가를 감수함", (0, 0, 0, 2, 2), "무엇을 포기하고 무엇을 얻는지 명확히 하세요."),
    "SATISFACTION": TagProfile("만족", "충족·편안함·원하는 결과의 향유", (4, 2, 2, 5, 0), "만족을 누리되 다음 단계의 과도한 낙관은 경계하세요."),
    "SECURITY": TagProfile("안정", "소유·보호·확실한 물질적 기반", (3, 2, 1, 5, 0), "안정을 지키되 자원이 묶여 기회를 막지 않는지 보세요."),
    "SELF_INTEREST": TagProfile("이기심", "공동 목적보다 개인 이익을 앞세움", (-2, 2, 1, 1, 0), "내 이익과 공동의 책임 사이의 균형을 확인하세요."),
    "SETBACK": TagProfile("후퇴", "장애·실패·진행의 약화", (-2, 1, 1, 1, 1), "실패 원인을 작게 나누고 다시 시도할 조건을 정하세요."),
    "SKILL": TagProfile("기술", "의지·능숙함·수단을 활용하는 힘", (4, 4, 3, 4, 0), "보유한 자원과 기술을 하나의 분명한 목표에 집중하세요."),
    "STAGNATION": TagProfile("정체", "움직임 없는 상태·무기력·고착", (-2, 0, 0, 2, 0), "정체를 깨기 위한 가장 작은 행동을 기한과 함께 정하세요."),
    "STRATEGY": TagProfile("전략", "계획·기지·간접적인 접근", (1, 3, 3, 2, 0), "목표·위험·대안을 숨김없이 점검하세요.", "영리한 계획이 기만으로 변하지 않게 하세요."),
    "SUCCESS": TagProfile("성과", "승리·인정·목표 달성", (4, 4, 3, 4, 1), "성과를 객관적인 결과와 다음 기회로 연결하세요."),
    "SUPERFICIALITY": TagProfile("피상성", "깊은 이해 없이 겉모습과 자만에 머묾", (-2, 2, 2, 1, 0), "아는 척하기보다 모르는 부분을 확인하고 더 깊이 조사하세요."),
    "TRANSITION": TagProfile("전환", "한 상태에서 다른 상태로 이동함", (1, 3, 3, 2, 3), "이동 과정의 비용과 도착 후의 계획을 함께 준비하세요."),
    "UNCERTAINTY": TagProfile("불확실", "놀람·혼란·결과를 예측하기 어려움", (-1, 1, 2, 0, 0), "확실한 사실과 아직 모르는 조건을 분리하세요."),
    "UNPREPARED": TagProfile("준비 부족", "예상하지 못한 상황과 대비 부족", (-3, 1, 2, 0, 0), "최악의 경우에 필요한 최소 대응책을 준비하세요."),
    "VICTORY": TagProfile("승리", "추진력·성공·경쟁에서 앞섬", (4, 5, 4, 3, 1), "승리 이후 책임과 유지 계획까지 준비하세요."),
    "VIGILANCE": TagProfile("경계", "관찰·조사·정보 수집·감시", (1, 3, 3, 3, 0), "의심만 키우지 말고 확인할 항목과 방법을 정하세요."),
    "WASTE": TagProfile("낭비", "자원·돈·능력을 계획 없이 소비함", (-3, 2, 3, 0, 0), "지출과 에너지 사용에서 당장 끊을 항목을 정하세요."),
    "WITHDRAWAL": TagProfile("위축", "두려움과 지나친 조심성으로 숨거나 물러남", (-2, 0, 0, 2, 0), "혼자 판단하지 말고 신뢰할 사람에게 사실을 점검받으세요."),
    "WORK": TagProfile("작업", "숙련·노동·반복을 통한 성취", (3, 4, 2, 4, 0), "결과의 품질 기준을 정하고 꾸준히 반복하세요."),
}


@dataclass(frozen=True)
class Meaning:
    text: str
    primary: str
    secondary: tuple[str, ...] = ()
    locator: str = ""
    metrics: tuple[float, float, float, float, float] | None = None


def m(text: str, primary: str, *secondary: str, locator: str = "", metrics=None) -> Meaning:
    return Meaning(text, primary, tuple(secondary), locator, metrics)


# Each record is an editorial Korean paraphrase of Waite Part III, not a modern
# consensus definition. The source locator makes contradictory historical cases visible.
MEANINGS: dict[str, tuple[Meaning, Meaning]] = {
    "FOOL": (
        m("분별보다 충동과 과장이 앞서 어디로 튈지 예측하기 어려운 출발", "IMPULSIVITY", "BEGINNING", locator="Part III §3 — Zero. The Fool"),
        m("주의와 책임감이 약해져 기회를 흘려보내거나 무기력해지는 상태", "APATHY", "WASTE", locator="Part III §3 — Zero. The Fool"),
    ),
    "MAGICIAN": (
        m("기술·외교력·의지와 자신감을 활용해 상황을 능숙하게 다루는 힘", "SKILL", "LEADERSHIP", locator="Part III §3 — 1. The Magician"),
        m("능력이나 영향력이 불안·기만·불명예를 만드는 방향으로 잘못 쓰이는 상태", "MISUSE", "DECEPTION", locator="Part III §3 — 1. The Magician"),
    ),
    "HIGH_PRIESTESS": (
        m("아직 드러나지 않은 비밀과 미래를 침묵·인내·지혜로 관찰하는 상태", "HIDDEN", "INTUITION", locator="Part III §3 — 2. The High Priestess"),
        m("강한 열정이나 자만 때문에 깊은 지혜보다 겉핥기식 이해에 머무는 상태", "SUPERFICIALITY", "IMPULSIVITY", locator="Part III §3 — 2. The High Priestess"),
    ),
    "EMPRESS": (
        m("풍요·생산성·주도성이 살아나며 새로운 것을 길러내는 단계", "ABUNDANCE", "NURTURE", locator="Part III §3 — 3. The Empress"),
        m("얽힌 사실이 드러나지만 결정을 번복하거나 방향을 망설일 수 있는 단계", "CLARITY", "INDECISION", locator="Part III §3 — 3. The Empress"),
    ),
    "EMPEROR": (
        m("안정·보호·이성·의지로 현실을 조직하고 책임 있게 권한을 행사하는 상태", "AUTHORITY", "SECURITY", locator="Part III §3 — 4. The Emperor"),
        m("권한과 구조가 미성숙하거나 경직되어 오히려 진행을 막는 상태", "RIGIDITY", "SETBACK", locator="Part III §3 — 4. The Emperor"),
    ),
    "HIEROPHANT": (
        m("관계나 약속이 동맹·결혼·조언·제도 같은 공식 구조로 묶이는 단계", "FORMALIZATION", "RELATIONSHIP", locator="Part III §3 — 5. The Hierophant"),
        m("집단의 조화와 호의를 지나치게 우선해 자기 기준과 힘이 약해지는 상태", "CONFORMITY", "DISHARMONY", locator="Part III §3 — 5. The Hierophant"),
    ),
    "LOVERS": (
        m("매력과 사랑이 상호 결합으로 이어지고 어려움을 함께 넘어서는 관계", "RELATIONSHIP", "VICTORY", locator="Part III §3 — 6. The Lovers"),
        m("어리석은 계획과 엇갈린 가치 때문에 결합이나 약속이 좌절되는 흐름", "DISHARMONY", "SETBACK", locator="Part III §3 — 6. The Lovers"),
    ),
    "CHARIOT": (
        m("도움과 강한 추진력으로 갈등을 뚫고 승리를 향해 나아가는 흐름", "VICTORY", "MOVEMENT", locator="Part III §3 — 7. The Chariot"),
        m("다툼·분쟁·과도한 자신감이 패배나 법적 충돌로 번지는 흐름", "DEFEAT", "CONFLICT", locator="Part III §3 — 7. The Chariot"),
    ),
    "STRENGTH": (
        m("용기·활력·관대함으로 힘을 통제해 완전한 성과를 이루는 흐름", "COURAGE", "SUCCESS", locator="Part III §3 — 8. Fortitude"),
        m("힘을 과도하게 사용하거나 통제하지 못해 약함과 불화를 만드는 상태", "MISUSE", "DISHARMONY", locator="Part III §3 — 8. Fortitude"),
    ),
    "HERMIT": (
        m("신중한 관찰과 분별로 위험을 살피되 숨은 의도도 함께 경계하는 상태", "PRUDENCE", "VIGILANCE", locator="Part III §3 — 9. The Hermit"),
        m("두려움과 과도한 조심성 때문에 숨거나 불필요하게 물러나는 상태", "WITHDRAWAL", "FEAR", locator="Part III §3 — 9. The Hermit"),
    ),
    "WHEEL_OF_FORTUNE": (
        m("운과 외부 조건이 바뀌며 성공·상승·기회가 빠르게 들어오는 흐름", "FORTUNE", "SUCCESS", locator="Part III §3 — 10. Wheel of Fortune"),
        m("증가와 풍요가 지나쳐 관리되지 않는 과잉으로 변할 수 있는 흐름", "EXCESS", "ABUNDANCE", locator="Part III §3 — 10. Wheel of Fortune"),
    ),
    "JUSTICE": (
        m("증거와 원칙에 따른 공정한 판단이 책임 있는 결과로 이어지는 상태", "JUSTICE", "BALANCE", locator="Part III §3 — 11. Justice"),
        m("법·규칙·신념이 편향되거나 지나치게 엄격해 복잡한 분쟁을 만드는 상태", "BIAS", "CONFLICT", locator="Part III §3 — 11. Justice"),
    ),
    "HANGED_MAN": (
        m("시련과 희생을 받아들이며 멈춰서 다른 관점과 직관을 얻는 단계", "SACRIFICE", "PAUSE", locator="Part III §3 — 12. The Hanged Man"),
        m("공동의 문제보다 개인 이익이나 집단 압력에 끌려 통찰 없이 머무는 상태", "SELF_INTEREST", "CONFORMITY", locator="Part III §3 — 12. The Hanged Man"),
    ),
    "DEATH": (
        m("기존 국면이 끝나고 낡은 구조가 해체되는 강한 종료와 전환", "ENDING", "TRANSITION", locator="Part III §3 — 13. Death"),
        m("끝내야 할 것을 놓지 못해 무기력·고착·희망 상실로 이어지는 상태", "STAGNATION", "APATHY", locator="Part III §3 — 13. Death"),
    ),
    "TEMPERANCE": (
        m("절약·절제·관리와 타협으로 서로 다른 조건을 실용적으로 조율하는 상태", "BALANCE", "PRUDENCE", locator="Part III §3 — 14. Temperance"),
        m("서로 다른 이해관계가 섞이지 못하고 분열·경쟁·불운한 결합으로 흐르는 상태", "DISHARMONY", "CONFLICT", locator="Part III §3 — 14. Temperance"),
    ),
    "DEVIL": (
        m("강한 욕망과 압력이 행동을 몰아붙여 스스로 멈추기 어려워지는 상태", "COMPULSION", "ATTACHMENT", locator="Part III §3 — 15. The Devil"),
        m("두려움과 무력감 때문에 해로운 구조를 보면서도 벗어나지 못하는 상태", "FEAR", "RESTRICTION", locator="Part III §3 — 15. The Devil"),
    ),
    "TOWER": (
        m("예상하지 못한 재난이나 폭로가 기존 구조를 급격히 무너뜨리는 흐름", "DISRUPTION", "ENDING", locator="Part III §3 — 16. The Tower"),
        m("충격은 약해졌지만 억압·구속·불안정한 구조가 여전히 남아 있는 상태", "RESTRICTION", "RIGIDITY", locator="Part III §3 — 16. The Tower"),
    ),
    "STAR": (
        m("상실 가능성이 함께 존재해도 밝은 전망과 회복의 방향을 다시 발견하는 흐름", "HOPE", "RECOVERY", "LOSS", locator="Part III §3 — 17. The Star"),
        m("자만이나 무력감 때문에 남아 있는 가능성을 제대로 활용하지 못하는 상태", "SETBACK", "SUPERFICIALITY", locator="Part III §3 — 17. The Star"),
    ),
    "MOON": (
        m("숨은 위험·오해·기만과 불분명한 정보가 판단을 흐리는 상태", "ILLUSION", "HIDDEN", "DECEPTION", locator="Part III §3 — 18. The Moon"),
        m("큰 기만은 약해져도 불안정과 의심이 남아 확신하기 어려운 상태", "DOUBT", "UNCERTAINTY", locator="Part III §3 — 18. The Moon"),
    ),
    "SUN": (
        m("물질적 행복·관계의 성취·만족이 밝고 분명하게 드러나는 흐름", "JOY", "SUCCESS", locator="Part III §3 — 19. The Sun"),
        m("좋은 흐름은 남아 있지만 기대보다 규모나 만족감이 작아지는 상태", "DIMINISHED_JOY", "IMPERFECTION", locator="Part III §3 — 19. The Sun"),
    ),
    "JUDGEMENT": (
        m("지위와 상황이 바뀌며 지난 과정을 평가하고 새롭게 갱신되는 결과", "AWAKENING", "RENEWAL", locator="Part III §3 — 20. The Last Judgment"),
        m("판단을 오래 미루거나 자신감이 약해져 결론과 책임을 확정하지 못하는 상태", "INDECISION", "SETBACK", locator="Part III §3 — 20. The Last Judgment"),
    ),
    "WORLD": (
        m("한 주기가 확실한 성공·보상·이동으로 마무리되는 완성의 흐름", "COMPLETION", "SUCCESS", "MOVEMENT", locator="Part III §3 — 21. The World"),
        m("끝내야 할 단계가 고정과 관성에 묶여 완성되지 못하고 정체되는 상태", "STAGNATION", "DELAY", locator="Part III §3 — 21. The World"),
    ),
    "ACE_OF_WANDS": (
        m("창조·발명·사업·출생처럼 새로운 힘이 처음 시작되는 원점", "CREATION", "BEGINNING", locator="Part III §2 — Wands, Ace"),
        m("시작의 힘이 쇠퇴하거나 무너져 기쁨과 성장이 흐려지는 상태", "SETBACK", "LOSS", locator="Part III §2 — Wands, Ace"),
    ),
    "TWO_OF_WANDS": (
        m("넓은 영역과 가능성을 바라보지만 성취와 불만이 함께 존재하는 계획 단계", "PLANNING", "CONTROL", "UNCERTAINTY", locator="Part III §2 — Wands, Two"),
        m("예상 밖의 감정과 놀람이 두려움·혼란과 뒤섞이는 상태", "UNCERTAINTY", "FEAR", locator="Part III §2 — Wands, Two"),
    ),
    "THREE_OF_WANDS": (
        m("사업·교역·탐색이 협력과 함께 넓은 시장으로 확장되는 흐름", "EXPANSION", "WORK", "RELATIONSHIP", locator="Part III §2 — Wands, Three"),
        m("고난과 실망이 멈추고 문제가 끝나면서 회복 여지가 생기는 흐름", "RECOVERY", "ENDING", locator="Part III §2 — Wands, Three"),
    ),
    "FOUR_OF_WANDS": (
        m("안식처·화합·번영과 완성된 일을 함께 기뻐하는 안정된 상태", "CELEBRATION", "SECURITY", locator="Part III §2 — Wands, Four"),
        m("정방향과 마찬가지로 번영·증가·행복이 이어지는 흐름", "ABUNDANCE", "CELEBRATION", locator="Part III §2 — Wands, Four"),
    ),
    "FIVE_OF_WANDS": (
        m("성과와 자원을 얻기 위해 여러 사람이 치열하게 경쟁하고 부딪히는 상태", "CONFLICT", "WORK", locator="Part III §2 — Wands, Five"),
        m("경쟁이 소송·논쟁·속임수와 모순으로 악화되는 상태", "CONFLICT", "DECEPTION", locator="Part III §2 — Wands, Five"),
    ),
    "SIX_OF_WANDS": (
        m("승리·좋은 소식·기대하던 인정을 얻어 성과가 공개되는 흐름", "SUCCESS", "MESSAGE", "VICTORY", locator="Part III §2 — Wands, Six"),
        m("승리를 앞두고 배신·두려움·불확실한 지연이 끼어드는 상태", "SETBACK", "DELAY", "DECEPTION", locator="Part III §2 — Wands, Six"),
    ),
    "SEVEN_OF_WANDS": (
        m("유리한 위치에서 경쟁과 협상을 버티며 자신의 성과를 지키는 상태", "DEFENCE", "CONFLICT", "SUCCESS", locator="Part III §2 — Wands, Seven"),
        m("당황·불안·우유부단 때문에 방어와 협상이 흔들리는 상태", "ANXIETY", "INDECISION", locator="Part III §2 — Wands, Seven"),
    ),
    "EIGHT_OF_WANDS": (
        m("일·연락·감정이 목표를 향해 매우 빠르게 움직이는 흐름", "MOVEMENT", "MESSAGE", locator="Part III §2 — Wands, Eight"),
        m("속도가 질투·양심의 가책·말다툼과 내부 갈등으로 흩어지는 상태", "CONFLICT", "ANXIETY", locator="Part III §2 — Wands, Eight"),
    ),
    "NINE_OF_WANDS": (
        m("공격을 예상하면서도 버틸 힘을 유지하고 경계를 늦추지 않는 상태", "DEFENCE", "VIGILANCE", "DELAY", locator="Part III §2 — Wands, Nine"),
        m("장애·역경·재난 때문에 버티는 힘과 진행이 크게 약해지는 상태", "SETBACK", "RESTRICTION", locator="Part III §2 — Wands, Nine"),
    ),
    "TEN_OF_WANDS": (
        m("성공과 이익을 얻었어도 책임·압박·가식이 무겁게 짓누르는 상태", "BURDEN", "SUCCESS", "DECEPTION", locator="Part III §2 — Wands, Ten"),
        m("어려움·모순·책략이 얽혀 부담을 내려놓기조차 쉽지 않은 상태", "CONFLICT", "BURDEN", locator="Part III §2 — Wands, Ten"),
    ),
    "PAGE_OF_WANDS": (
        m("충실한 전달자나 새로운 소식이 낯설지만 활기찬 가능성을 알리는 흐름", "MESSAGE", "BEGINNING", locator="Part III §2 — Wands, Page"),
        m("나쁜 소식과 소문이 우유부단·불안정과 함께 들어오는 상태", "INDECISION", "MESSAGE", "SETBACK", locator="Part III §2 — Wands, Page"),
    ),
    "KNIGHT_OF_WANDS": (
        m("출발·이주·빠른 이동으로 생활 환경이나 관심사가 크게 바뀌는 흐름", "MOVEMENT", "DEPARTURE", locator="Part III §2 — Wands, Knight"),
        m("이동이 단절·분열·중단과 불화로 바뀌는 상태", "DISRUPTION", "DISHARMONY", locator="Part III §2 — Wands, Knight"),
    ),
    "QUEEN_OF_WANDS": (
        m("따뜻하고 명예로운 매력으로 사람을 돕고 사업적 성과도 끌어오는 힘", "NURTURE", "SUCCESS", "RELATIONSHIP", locator="Part III §2 — Wands, Queen"),
        m("겉으로는 유능하고 도움을 주지만 질투·대립·기만 가능성이 섞이는 상태", "DECEPTION", "CONFLICT", locator="Part III §2 — Wands, Queen"),
    ),
    "KING_OF_WANDS": (
        m("정직·열정·책임감으로 사람과 일을 이끌며 뜻밖의 좋은 소식도 받는 흐름", "LEADERSHIP", "MESSAGE", locator="Part III §2 — Wands, King"),
        m("선의는 남아 있어도 태도가 지나치게 엄격하고 융통성 없이 굳어지는 상태", "RIGIDITY", "AUTHORITY", locator="Part III §2 — Wands, King"),
    ),
    "ACE_OF_CUPS": (
        m("진실한 마음·기쁨·풍요·돌봄이 넘쳐 새로운 정서적 기반이 생기는 흐름", "EMOTION", "ABUNDANCE", "BEGINNING", locator="Part III §2 — Cups, Ace"),
        m("마음의 기반이 흔들리고 감정·관계·생활이 불안정하게 바뀌는 상태", "DISHARMONY", "UNCERTAINTY", locator="Part III §2 — Cups, Ace"),
    ),
    "TWO_OF_CUPS": (
        m("사랑·우정·공감·합의가 서로 주고받는 결합으로 이어지는 관계", "RELATIONSHIP", "BALANCE", locator="Part III §2 — Cups, Two"),
        m("강한 열정이 이성적 합의보다 앞서 관계를 급하게 몰아가는 상태", "IMPULSIVITY", "RELATIONSHIP", locator="Part III §4 — Cups, Two (main §2 has no reversed line)"),
    ),
    "THREE_OF_CUPS": (
        m("일이 풍성하게 마무리되고 승리·치유·기쁨을 함께 나누는 흐름", "CELEBRATION", "HEALING", "SUCCESS", locator="Part III §2 — Cups, Three"),
        m("빠른 성취와 마무리가 감각적 즐거움의 과잉으로 치우칠 수 있는 상태", "OVERINDULGENCE", "ENDING", locator="Part III §2 — Cups, Three"),
    ),
    "FOUR_OF_CUPS": (
        m("권태와 싫증 때문에 눈앞의 새로운 기회에도 위안을 느끼지 못하는 상태", "APATHY", "UNCERTAINTY", locator="Part III §2 — Cups, Four"),
        m("새로운 소식·배움·관계가 들어와 정체된 감정을 깨우는 흐름", "BEGINNING", "MESSAGE", "RELATIONSHIP", locator="Part III §2 — Cups, Four"),
    ),
    "FIVE_OF_CUPS": (
        m("기대했던 것을 잃고 실망하지만 아직 남은 자원과 관계가 존재하는 상태", "LOSS", "RELATIONSHIP", locator="Part III §2 — Cups, Five"),
        m("과거의 사람·소식·연결이 돌아오지만 잘못된 계획도 함께 재등장할 수 있는 흐름", "RETURN", "DECEPTION", locator="Part III §2 — Cups, Five"),
    ),
    "SIX_OF_CUPS": (
        m("어린 시절·과거 관계·사라진 행복의 기억이 현재에 영향을 주는 상태", "MEMORY", "RELATIONSHIP", locator="Part III §2 — Cups, Six"),
        m("새로운 관계·환경·미래의 일이 곧 현실로 들어오는 갱신의 흐름", "RENEWAL", "BEGINNING", locator="Part III §2 — Cups, Six"),
    ),
    "SEVEN_OF_CUPS": (
        m("상상과 감정적 선택지는 많지만 오래 지속될 실체가 부족한 상태", "FANTASY", "ILLUSION", locator="Part III §2 — Cups, Seven"),
        m("흩어진 욕망을 구체적인 의지·결정·계획으로 좁히는 단계", "DETERMINATION", "PLANNING", locator="Part III §2 — Cups, Seven"),
    ),
    "EIGHT_OF_CUPS": (
        m("중요하다고 믿었던 일의 가치가 줄어들어 익숙한 만족을 떠나는 흐름", "DEPARTURE", "ENDING", locator="Part III §2 — Cups, Eight"),
        m("떠남의 공백이 큰 기쁨·만족·축제로 채워지는 흐름", "JOY", "CELEBRATION", locator="Part III §2 — Cups, Eight"),
    ),
    "NINE_OF_CUPS": (
        m("원하던 만족·편안함·승리와 물질적 여유를 누리는 상태", "SATISFACTION", "SUCCESS", locator="Part III §2 — Cups, Nine"),
        m("진실과 자유를 얻어도 실수·결함·불완전한 결과가 함께 남는 상태", "IMPERFECTION", "CLARITY", locator="Part III §2 — Cups, Nine"),
    ),
    "TEN_OF_CUPS": (
        m("가족·사랑·우정이 깊은 만족과 안정된 공동체로 완성되는 흐름", "FAMILY", "RELATIONSHIP", "JOY", locator="Part III §2 — Cups, Ten"),
        m("겉으로 평온해 보여도 분노·폭력·거짓된 마음이 관계를 흔드는 상태", "DISHARMONY", "DECEPTION", locator="Part III §2 — Cups, Ten"),
    ),
    "PAGE_OF_CUPS": (
        m("다정한 소식·배움·성찰이 감정과 상상을 현실적인 형태로 가져오는 흐름", "MESSAGE", "LEARNING", "EMOTION", locator="Part III §2 — Cups, Page"),
        m("매력과 호감이 유혹·속임수·교묘한 의도로 변질될 수 있는 상태", "DECEPTION", "ATTACHMENT", locator="Part III §2 — Cups, Page"),
    ),
    "KNIGHT_OF_CUPS": (
        m("감정적 제안·초대·접근이나 반가운 전달자가 다가오는 흐름", "OFFER", "MESSAGE", "RELATIONSHIP", locator="Part III §2 — Cups, Knight"),
        m("매력적인 제안 뒤에 속임수·이중성·사기 가능성이 숨은 상태", "DECEPTION", "OFFER", locator="Part III §2 — Cups, Knight"),
    ),
    "QUEEN_OF_CUPS": (
        m("사랑과 직관을 함께 사용해 사람을 돕고 정서적 행복을 만드는 힘", "INTUITION", "NURTURE", "JOY", locator="Part III §2 — Cups, Queen"),
        m("감수성과 매력이 불신·부도덕·기만으로 흐를 수 있는 상태", "DECEPTION", "DOUBT", locator="Part III §2 — Cups, Queen"),
    ),
    "KING_OF_CUPS": (
        m("책임감·공정함·창조적 지성으로 감정과 현실을 성숙하게 다루는 힘", "MASTERY", "JUSTICE", "EMOTION", locator="Part III §2 — Cups, King"),
        m("권위와 감정 조절이 이중성·불의·착취·큰 손실로 왜곡되는 상태", "DECEPTION", "ABUSE", "LOSS", locator="Part III §2 — Cups, King"),
    ),
    "ACE_OF_SWORDS": (
        m("강한 결단과 힘으로 문제를 가르고 승리와 돌파를 만드는 흐름", "BREAKTHROUGH", "VICTORY", locator="Part III §2 — Swords, Ace"),
        m("같은 강한 힘이 파괴적 결과와 과도한 충돌을 만드는 상태", "MISUSE", "CONFLICT", locator="Part III §2 — Swords, Ace"),
    ),
    "TWO_OF_SWORDS": (
        m("대립 속에서도 균형과 합의를 유지하지만 긴장이 완전히 해소되지는 않은 상태", "BALANCE", "INDECISION", locator="Part III §2 — Swords, Two"),
        m("거짓·이중성·배신이 균형을 깨고 신뢰를 약화시키는 상태", "DECEPTION", "DISHARMONY", locator="Part III §2 — Swords, Two"),
    ),
    "THREE_OF_SWORDS": (
        m("이별·분리·지연·단절이 마음에 직접적인 상처를 만드는 흐름", "HEARTBREAK", "LOSS", locator="Part III §2 — Swords, Three"),
        m("상처가 혼란·오류·정신적 분산으로 남아 판단까지 흐리는 상태", "UNCERTAINTY", "LOSS", locator="Part III §2 — Swords, Three"),
    ),
    "FOUR_OF_SWORDS": (
        m("일선에서 물러나 고독과 휴식 속에서 힘을 보존하는 상태", "REST", "WITHDRAWAL", locator="Part III §2 — Swords, Four"),
        m("신중한 관리·절약·예방을 통해 다시 움직일 준비를 갖추는 상태", "PRUDENCE", "SECURITY", locator="Part III §2 — Swords, Four"),
    ),
    "FIVE_OF_SWORDS": (
        m("승부 뒤에 불명예·파괴·철회와 손실이 남는 패배의 흐름", "DEFEAT", "LOSS", locator="Part III §2 — Swords, Five"),
        m("손실과 슬픔의 여파가 계속되어 애도와 정리가 필요한 상태", "LOSS", "ENDING", locator="Part III §2 — Swords, Five"),
    ),
    "SIX_OF_SWORDS": (
        m("더 나은 길을 찾기 위해 현재 문제에서 다른 장소·방법으로 이동하는 흐름", "TRANSITION", "MOVEMENT", locator="Part III §2 — Swords, Six"),
        m("숨겨진 내용이 고백·선언·공개되며 관계나 제안이 밖으로 드러나는 흐름", "DISCLOSURE", "MESSAGE", locator="Part III §2 — Swords, Six"),
    ),
    "SEVEN_OF_SWORDS": (
        m("계획과 기지를 사용하지만 실패·다툼·불확실성이 섞여 있는 전략", "STRATEGY", "UNCERTAINTY", locator="Part III §2 — Swords, Seven"),
        m("조언과 정보가 들어오지만 소문·비방·말의 과잉도 함께 섞이는 상태", "MESSAGE", "DECEPTION", locator="Part III §2 — Swords, Seven"),
    ),
    "EIGHT_OF_SWORDS": (
        m("위기와 비난 속에서 권한과 행동이 묶여 선택지가 제한된 상태", "RESTRICTION", "CONFLICT", locator="Part III §2 — Swords, Eight"),
        m("예상 못한 방해·사고·배신이 제약을 더 복잡하게 만드는 상태", "SETBACK", "UNPREPARED", "DECEPTION", locator="Part III §2 — Swords, Eight"),
    ),
    "NINE_OF_SWORDS": (
        m("실패·지연·기만·실망이 극심한 걱정과 절망으로 이어지는 상태", "ANXIETY", "LOSS", locator="Part III §2 — Swords, Nine"),
        m("의심·수치·두려움이 마음을 가두어 실제 위험보다 더 크게 느끼게 하는 상태", "FEAR", "RESTRICTION", locator="Part III §2 — Swords, Nine"),
    ),
    "TEN_OF_SWORDS": (
        m("고통과 상실이 한계에 도달해 기존 국면이 사실상 끝난 상태", "ENDING", "LOSS", locator="Part III §2 — Swords, Ten"),
        m("불리한 국면 뒤에 일시적인 이익·호의·회복이 나타나는 흐름", "RECOVERY", "SUCCESS", locator="Part III §2 — Swords, Ten"),
    ),
    "PAGE_OF_SWORDS": (
        m("경계·조사·감시를 통해 숨은 위험과 정보를 적극적으로 살피는 상태", "VIGILANCE", "HIDDEN", locator="Part III §2 — Swords, Page"),
        m("준비하지 못한 사건과 악의적 감시·예상 밖의 문제가 들어오는 상태", "UNPREPARED", "DECEPTION", locator="Part III §2 — Swords, Page"),
    ),
    "KNIGHT_OF_SWORDS": (
        m("기술과 용기를 앞세워 매우 빠르게 맞서고 돌파하려는 공격적 움직임", "MOVEMENT", "CONFLICT", "COURAGE", locator="Part III §2 — Swords, Knight"),
        m("성급함·무능·과장이 행동을 통제하지 못해 손실을 만드는 상태", "IMPULSIVITY", "SETBACK", locator="Part III §2 — Swords, Knight"),
    ),
    "QUEEN_OF_SWORDS": (
        m("상실과 분리를 겪은 뒤 감정을 절제하고 냉정하게 현실을 보는 상태", "LOSS", "CLARITY", locator="Part III §2 — Swords, Queen"),
        m("슬픔과 엄격함이 악의·편견·기만으로 굳어지는 상태", "DECEPTION", "BIAS", locator="Part III §2 — Swords, Queen"),
    ),
    "KING_OF_SWORDS": (
        m("판단·법·명령·지성을 사용해 질서와 결정을 세우는 권위", "AUTHORITY", "JUSTICE", locator="Part III §2 — Swords, King"),
        m("권력과 판단이 잔혹함·배신·악의로 변하는 권력 남용", "ABUSE", "DECEPTION", locator="Part III §2 — Swords, King"),
    ),
    "ACE_OF_PENTACLES": (
        m("돈·자원·안락함과 현실적인 번영을 시작할 수 있는 강한 기회", "MATERIAL_OPPORTUNITY", "ABUNDANCE", locator="Part III §2 — Pentacles, Ace"),
        m("부는 커질 수 있지만 탐욕·나쁜 소식·소유의 부작용이 함께 커지는 상태", "EXCESS", "ATTACHMENT", locator="Part III §2 — Pentacles, Ace"),
    ),
    "TWO_OF_PENTACLES": (
        m("여러 일과 소식을 유연하게 돌리지만 장애와 소란도 함께 관리해야 하는 상태", "ADAPTATION", "MESSAGE", locator="Part III §2 — Pentacles, Two"),
        m("겉으로 즐거운 척하며 실제 부담을 숨기거나 문서·거래가 복잡해지는 상태", "PRETENCE", "UNCERTAINTY", locator="Part III §2 — Pentacles, Two"),
    ),
    "THREE_OF_PENTACLES": (
        m("숙련된 노동과 협업이 명예·평판·전문적 성과로 이어지는 흐름", "WORK", "SKILL", "SUCCESS", locator="Part III §2 — Pentacles, Three"),
        m("기준과 숙련이 부족해 결과가 평범하고 미숙하게 머무는 상태", "MEDIOCRITY", "SETBACK", locator="Part III §2 — Pentacles, Three"),
    ),
    "FOUR_OF_PENTACLES": (
        m("보유한 재산과 기반을 단단히 지키지만 놓지 못하는 성향도 강한 상태", "SECURITY", "CONTROL", "ATTACHMENT", locator="Part III §2 — Pentacles, Four"),
        m("소유와 계획이 지연·반대·긴장에 묶여 움직이지 못하는 상태", "DELAY", "RESTRICTION", locator="Part III §2 — Pentacles, Four"),
    ),
    "FIVE_OF_PENTACLES": (
        m("돈·생활 기반·지원이 부족해 소외와 물질적 어려움을 겪는 상태", "POVERTY", "LOSS", locator="Part III §2 — Pentacles, Five"),
        m("궁핍이 혼란·낭비·불화와 결합해 구조적인 붕괴로 번지는 상태", "DISRUPTION", "WASTE", locator="Part III §2 — Pentacles, Five"),
    ),
    "SIX_OF_PENTACLES": (
        m("선물·도움·자원을 주고받으며 현재의 번영을 나누는 흐름", "GENEROSITY", "ABUNDANCE", locator="Part III §2 — Pentacles, Six"),
        m("도움과 돈의 관계에 욕심·질투·소유욕이 개입하는 상태", "GREED", "ATTACHMENT", locator="Part III §2 — Pentacles, Six"),
    ),
    "SEVEN_OF_PENTACLES": (
        m("돈·사업·교환의 결과를 지켜보며 더 투자할지 평가하는 상태", "ASSESSMENT", "WORK", locator="Part III §2 — Pentacles, Seven"),
        m("돈을 빌리거나 더 투자하는 문제 때문에 불안과 의심이 커지는 상태", "ANXIETY", "DOUBT", locator="Part III §2 — Pentacles, Seven"),
    ),
    "EIGHT_OF_PENTACLES": (
        m("반복 작업과 기술 연마로 실제 쓸 수 있는 숙련을 만드는 단계", "WORK", "SKILL", locator="Part III §2 — Pentacles, Eight"),
        m("기술이 허영·탐욕·착취·교묘한 술수에 사용되는 상태", "MISUSE", "GREED", locator="Part III §2 — Pentacles, Eight"),
    ),
    "NINE_OF_PENTACLES": (
        m("신중한 판단과 성취를 바탕으로 안전하고 독립적인 기반을 누리는 상태", "INDEPENDENCE", "SECURITY", "SUCCESS", locator="Part III §2 — Pentacles, Nine"),
        m("사기·나쁜 믿음·잘못된 계획 때문에 구축한 기반이 흔들리는 상태", "DECEPTION", "SETBACK", locator="Part III §2 — Pentacles, Nine"),
    ),
    "TEN_OF_PENTACLES": (
        m("부·가족·집·기록과 전통이 오래 지속되는 기반으로 축적되는 흐름", "LEGACY", "FAMILY", "ABUNDANCE", locator="Part III §2 — Pentacles, Ten"),
        m("우연·도박·절도·손실이 재산과 가족 기반을 흔드는 상태", "LOSS", "UNCERTAINTY", locator="Part III §2 — Pentacles, Ten"),
    ),
    "PAGE_OF_PENTACLES": (
        m("공부·연구·실무 준비와 관리 능력을 키우며 현실적인 소식을 받는 단계", "LEARNING", "MESSAGE", "WORK", locator="Part III §2 — Pentacles, Page"),
        m("낭비·사치·산만함 때문에 학습과 자원의 가치가 새어 나가는 상태", "WASTE", "SETBACK", locator="Part III §2 — Pentacles, Page"),
    ),
    "KNIGHT_OF_PENTACLES": (
        m("실용성·책임감·정직함으로 맡은 일을 느리지만 꾸준히 수행하는 상태", "RESPONSIBILITY", "WORK", locator="Part III §2 — Pentacles, Knight"),
        m("느림이 무기력·게으름·정체와 부주의로 굳어지는 상태", "STAGNATION", "APATHY", locator="Part III §2 — Pentacles, Knight"),
    ),
    "QUEEN_OF_PENTACLES": (
        m("풍요·관대함·안정과 자유를 현실적인 돌봄으로 제공하는 힘", "ABUNDANCE", "GENEROSITY", "SECURITY", locator="Part III §2 — Pentacles, Queen"),
        m("안정이 의심·두려움·불신에 흔들려 자원을 편안히 쓰지 못하는 상태", "DOUBT", "FEAR", locator="Part III §2 — Pentacles, Queen"),
    ),
    "KING_OF_PENTACLES": (
        m("사업 감각·현실 판단·전문성과 계산 능력으로 안정된 성공을 만드는 힘", "MASTERY", "SUCCESS", "SECURITY", locator="Part III §2 — Pentacles, King"),
        m("능력과 부가 탐욕·부패·무책임으로 변해 위험을 만드는 상태", "CORRUPTION", "GREED", locator="Part III §2 — Pentacles, King"),
    ),
}

# Tags used above but defined after the main profile block to keep related terms visible.
TAGS.update({
    "ASSESSMENT": TagProfile("평가", "기다리며 투자·노력·성과를 재평가함", (1, 1, 0, 3, 0), "추가 투자 전에 지금까지의 수익과 비용을 계산하세요."),
    "CREATION": TagProfile("창조", "새로운 아이디어·사업·생명의 시작", (4, 5, 4, 2, 0), "아이디어를 가장 작은 실행 가능한 형태로 만드세요."),
    "DEFENCE": TagProfile("방어", "입장·성과·영역을 지키며 버팀", (2, 4, 2, 3, 0), "지켜야 할 핵심 기준과 소모적인 싸움을 구분하세요."),
    "EXPANSION": TagProfile("확장", "사업·교역·시야·협력의 확장", (3, 4, 3, 3, 0), "확장 전에 필요한 자원과 협력 조건을 점검하세요."),
    "HEARTBREAK": TagProfile("상심", "분리·이별·단절로 인한 직접적 상처", (-4, 1, 1, 0, 3), "상처를 부정하지 말고 회복에 필요한 거리와 지원을 확보하세요."),
})

# Golden Dawn / Book T normalized correspondences.
MAJOR_GD = {
    "FOOL": ("The Spirit of Aether", "ALEPH", "11 KETHER-CHOKMAH", "ELEMENT", "AIR", "AIR"),
    "MAGICIAN": ("The Magus of Power", "BETH", "12 KETHER-BINAH", "PLANET", "MERCURY", "AIR"),
    "HIGH_PRIESTESS": ("The Priestess of the Silver Star", "GIMEL", "13 KETHER-TIPHARETH", "PLANET", "MOON", "WATER"),
    "EMPRESS": ("The Daughter of the Mighty Ones", "DALETH", "14 CHOKMAH-BINAH", "PLANET", "VENUS", "EARTH"),
    "EMPEROR": ("Son of the Morning, Chief among the Mighty", "HEH", "15 CHOKMAH-TIPHARETH", "ZODIAC", "ARIES", "FIRE"),
    "HIEROPHANT": ("The Magus of the Eternal", "VAV", "16 CHOKMAH-CHESED", "ZODIAC", "TAURUS", "EARTH"),
    "LOVERS": ("The Children of the Voice; the Oracles of the Mighty Gods", "ZAYIN", "17 BINAH-TIPHARETH", "ZODIAC", "GEMINI", "AIR"),
    "CHARIOT": ("The Child of the Powers of the Waters; the Lord of the Triumph of Light", "CHETH", "18 BINAH-GEBURAH", "ZODIAC", "CANCER", "WATER"),
    "STRENGTH": ("The Daughter of the Flaming Sword", "TETH", "19 CHESED-GEBURAH", "ZODIAC", "LEO", "FIRE"),
    "HERMIT": ("The Magus of the Voice of Power; the Prophet of the Eternal", "YOD", "20 CHESED-TIPHARETH", "ZODIAC", "VIRGO", "EARTH"),
    "WHEEL_OF_FORTUNE": ("The Lord of the Forces of Life", "KAPH", "21 CHESED-NETZACH", "PLANET", "JUPITER", "FIRE"),
    "JUSTICE": ("The Daughter of the Lords of Truth; the Ruler of the Balance", "LAMED", "22 GEBURAH-TIPHARETH", "ZODIAC", "LIBRA", "AIR"),
    "HANGED_MAN": ("The Spirit of the Mighty Waters", "MEM", "23 GEBURAH-HOD", "ELEMENT", "WATER", "WATER"),
    "DEATH": ("The Child of the Great Transformers; the Lord of the Gates of Death", "NUN", "24 TIPHARETH-NETZACH", "ZODIAC", "SCORPIO", "WATER"),
    "TEMPERANCE": ("The Daughter of the Reconcilers; the Bringer-Forth of Life", "SAMEKH", "25 TIPHARETH-YESOD", "ZODIAC", "SAGITTARIUS", "FIRE"),
    "DEVIL": ("The Lord of the Gates of Matter; the Child of the Forces of Time", "AYIN", "26 TIPHARETH-HOD", "ZODIAC", "CAPRICORN", "EARTH"),
    "TOWER": ("The Lord of the Hosts of the Mighty", "PEH", "27 NETZACH-HOD", "PLANET", "MARS", "FIRE"),
    "STAR": ("The Daughter of the Firmament; the Dweller between the Waters", "TZADDI", "28 NETZACH-YESOD", "ZODIAC", "AQUARIUS", "AIR"),
    "MOON": ("The Ruler of Flux and Reflux; the Child of the Sons of the Mighty", "QOPH", "29 NETZACH-MALKUTH", "ZODIAC", "PISCES", "WATER"),
    "SUN": ("The Lord of the Fire of the World", "RESH", "30 HOD-YESOD", "PLANET", "SUN", "FIRE"),
    "JUDGEMENT": ("The Spirit of the Primal Fire", "SHIN", "31 HOD-MALKUTH", "ELEMENT", "FIRE", "FIRE"),
    "WORLD": ("The Great One of the Night of Time", "TAV", "32 YESOD-MALKUTH", "PLANET", "SATURN", "EARTH"),
}

SUIT_ELEMENT = {"WANDS": "FIRE", "CUPS": "WATER", "SWORDS": "AIR", "PENTACLES": "EARTH"}
SEPHIRAH_BY_RANK = {"TWO": "CHOKMAH", "THREE": "BINAH", "FOUR": "CHESED", "FIVE": "GEBURAH", "SIX": "TIPHARETH", "SEVEN": "NETZACH", "EIGHT": "HOD", "NINE": "YESOD", "TEN": "MALKUTH"}

PIP_GD = {
    "TWO_OF_WANDS": ("The Lord of Dominion", "MARS", "ARIES", "0-10"),
    "THREE_OF_WANDS": ("The Lord of Established Strength", "SUN", "ARIES", "10-20"),
    "FOUR_OF_WANDS": ("The Lord of Perfected Work", "VENUS", "ARIES", "20-30"),
    "FIVE_OF_PENTACLES": ("The Lord of Material Trouble", "MERCURY", "TAURUS", "0-10"),
    "SIX_OF_PENTACLES": ("The Lord of Material Success", "MOON", "TAURUS", "10-20"),
    "SEVEN_OF_PENTACLES": ("The Lord of Success Unfulfilled", "SATURN", "TAURUS", "20-30"),
    "EIGHT_OF_SWORDS": ("The Lord of Shortened Force", "JUPITER", "GEMINI", "0-10"),
    "NINE_OF_SWORDS": ("The Lord of Despair and Cruelty", "MARS", "GEMINI", "10-20"),
    "TEN_OF_SWORDS": ("The Lord of Ruin", "SUN", "GEMINI", "20-30"),
    "TWO_OF_CUPS": ("The Lord of Love", "VENUS", "CANCER", "0-10"),
    "THREE_OF_CUPS": ("The Lord of Abundance", "MERCURY", "CANCER", "10-20"),
    "FOUR_OF_CUPS": ("The Lord of Blended Pleasure", "MOON", "CANCER", "20-30"),
    "FIVE_OF_WANDS": ("The Lord of Strife", "SATURN", "LEO", "0-10"),
    "SIX_OF_WANDS": ("The Lord of Victory", "JUPITER", "LEO", "10-20"),
    "SEVEN_OF_WANDS": ("The Lord of Valour", "MARS", "LEO", "20-30"),
    "EIGHT_OF_PENTACLES": ("The Lord of Prudence", "SUN", "VIRGO", "0-10"),
    "NINE_OF_PENTACLES": ("The Lord of Material Gain", "VENUS", "VIRGO", "10-20"),
    "TEN_OF_PENTACLES": ("The Lord of Wealth", "MERCURY", "VIRGO", "20-30"),
    "TWO_OF_SWORDS": ("The Lord of Peace Restored", "MOON", "LIBRA", "0-10"),
    "THREE_OF_SWORDS": ("The Lord of Sorrow", "SATURN", "LIBRA", "10-20"),
    "FOUR_OF_SWORDS": ("The Lord of Rest from Strife", "JUPITER", "LIBRA", "20-30"),
    "FIVE_OF_CUPS": ("The Lord of Loss in Pleasure", "MARS", "SCORPIO", "0-10"),
    "SIX_OF_CUPS": ("The Lord of Pleasure", "SUN", "SCORPIO", "10-20"),
    "SEVEN_OF_CUPS": ("The Lord of Illusionary Success", "VENUS", "SCORPIO", "20-30"),
    "EIGHT_OF_WANDS": ("The Lord of Swiftness", "MERCURY", "SAGITTARIUS", "0-10"),
    "NINE_OF_WANDS": ("The Lord of Great Strength", "MOON", "SAGITTARIUS", "10-20"),
    "TEN_OF_WANDS": ("The Lord of Oppression", "SATURN", "SAGITTARIUS", "20-30"),
    "TWO_OF_PENTACLES": ("The Lord of Harmonious Change", "JUPITER", "CAPRICORN", "0-10"),
    "THREE_OF_PENTACLES": ("The Lord of Material Works", "MARS", "CAPRICORN", "10-20"),
    "FOUR_OF_PENTACLES": ("The Lord of Earthly Power", "SUN", "CAPRICORN", "20-30"),
    "FIVE_OF_SWORDS": ("The Lord of Defeat", "VENUS", "AQUARIUS", "0-10"),
    "SIX_OF_SWORDS": ("The Lord of Earned Success", "MERCURY", "AQUARIUS", "10-20"),
    "SEVEN_OF_SWORDS": ("The Lord of Unstable Effort", "MOON", "AQUARIUS", "20-30"),
    "EIGHT_OF_CUPS": ("The Lord of Abandoned Success", "SATURN", "PISCES", "0-10"),
    "NINE_OF_CUPS": ("The Lord of Material Happiness", "JUPITER", "PISCES", "10-20"),
    "TEN_OF_CUPS": ("The Lord of Perfected Success", "MARS", "PISCES", "20-30"),
}

ACE_TITLES = {
    "ACE_OF_WANDS": "The Root of the Powers of Fire",
    "ACE_OF_CUPS": "The Root of the Powers of Water",
    "ACE_OF_SWORDS": "The Root of the Powers of Air",
    "ACE_OF_PENTACLES": "The Root of the Powers of Earth",
}

COURT_TITLES = {
    "WANDS": {
        "KNIGHT": "The Lord of the Flame and the Lightning; the King of the Spirits of Fire",
        "QUEEN": "The Queen of the Thrones of Flame",
        "KING": "The Prince of the Chariot of Fire",
        "PAGE": "The Princess of the Shining Flame; the Rose of the Palace of Fire",
    },
    "CUPS": {
        "KNIGHT": "The Lord of the Waves and the Waters; the King of the Hosts of the Sea",
        "QUEEN": "The Queen of the Thrones of the Waters",
        "KING": "The Prince of the Chariot of the Waters",
        "PAGE": "The Princess of the Waters; the Lotus of the Palace of the Floods",
    },
    "SWORDS": {
        "KNIGHT": "The Lord of the Wind and the Breezes; the King of the Spirits of Air",
        "QUEEN": "The Queen of the Thrones of Air",
        "KING": "The Prince of the Chariot of the Winds",
        "PAGE": "The Princess of the Rushing Winds; the Lotus of the Palace of Air",
    },
    "PENTACLES": {
        "KNIGHT": "The Lord of the Wide and Fertile Land; the King of the Spirits of Earth",
        "QUEEN": "The Queen of the Thrones of Earth",
        "KING": "The Prince of the Chariot of Earth",
        "PAGE": "The Princess of the Echoing Hills; the Rose of the Palace of Earth",
    },
}
COURT_RANK_ELEMENT = {"KNIGHT": "FIRE", "QUEEN": "WATER", "KING": "AIR", "PAGE": "EARTH"}

RELATION_RULES = [
    ("ENDING", "BEGINNING", "REVERSE", "기존 국면이 끝난 뒤 새로운 가능성이 열린다", 0.4),
    ("ENDING", "MOVEMENT", "ACCELERATE", "끝나던 국면 뒤로 상황이 빠르게 움직이기 시작한다", 0.4),
    ("ENDING", "RECOVERY", "RESOLVE", "끝과 손실을 인정한 뒤 회복 단계가 시작된다", 0.5),
    ("ENDING", "FORMALIZATION", "FORMALIZE", "마무리된 일이 공식 절차와 새 구조로 정리된다", 0.2),
    ("LOSS", "RECOVERY", "RESOLVE", "손실 이후 남은 자원을 바탕으로 회복한다", 0.5),
    ("LOSS", "HOPE", "RESOLVE", "상실을 지나 다시 기대할 방향을 찾는다", 0.5),
    ("LOSS", "MATERIAL_OPPORTUNITY", "IMPROVE", "손실 뒤 현실적인 보완 기회가 들어온다", 0.4),
    ("DISRUPTION", "HOPE", "RESOLVE", "큰 흔들림 이후 회복 방향과 희망이 나타난다", 0.6),
    ("DISRUPTION", "RECOVERY", "RESOLVE", "무너진 구조를 정리한 뒤 회복이 시작된다", 0.5),
    ("DISRUPTION", "SECURITY", "RESOLVE", "불안정한 상황이 다시 안전한 기반을 찾는다", 0.4),
    ("RESTRICTION", "MOVEMENT", "RELEASE", "제약이 풀리며 멈췄던 일이 움직인다", 0.4),
    ("RESTRICTION", "PAUSE", "SLOW_DOWN", "제약을 밀어붙이기보다 멈춰 조건을 다시 본다", -0.1),
    ("RESTRICTION", "BREAKTHROUGH", "REVERSE", "막힌 조건을 강한 결단으로 돌파하려 한다", 0.2),
    ("DELAY", "MOVEMENT", "ACCELERATE", "지연되던 일이 실행과 연락으로 전환된다", 0.4),
    ("STAGNATION", "BEGINNING", "REVERSE", "고착된 상태를 벗어나 새로운 출발을 시도한다", 0.4),
    ("STAGNATION", "MOVEMENT", "ACCELERATE", "멈춰 있던 흐름에 다시 속도가 붙는다", 0.4),
    ("PAUSE", "CLARITY", "RESOLVE", "멈춰 관찰한 결과 판단이 선명해진다", 0.3),
    ("PAUSE", "MOVEMENT", "ACCELERATE", "충분히 살핀 뒤 실제 행동으로 넘어간다", 0.3),
    ("ILLUSION", "CLARITY", "RESOLVE", "불분명한 상황에서 사실과 방향이 드러난다", 0.5),
    ("FANTASY", "DETERMINATION", "FORMALIZE", "흩어진 가능성을 구체적인 계획으로 좁힌다", 0.4),
    ("DOUBT", "CLARITY", "RESOLVE", "의심하던 조건을 확인해 판단이 선명해진다", 0.3),
    ("ANXIETY", "REST", "SLOW_DOWN", "불안한 흐름이 휴식과 거리 두기로 완화된다", 0.2),
    ("ANXIETY", "CLARITY", "RESOLVE", "걱정을 사실과 분리하면서 판단이 또렷해진다", 0.3),
    ("HEARTBREAK", "HEALING", "RESOLVE", "상처를 인정한 뒤 치유와 회복으로 넘어간다", 0.5),
    ("CONFLICT", "BALANCE", "RESOLVE", "대립하던 조건이 타협과 균형을 찾는다", 0.3),
    ("CONFLICT", "FORMALIZATION", "FORMALIZE", "갈등을 규칙·계약·절차로 정리한다", 0.2),
    ("CONFLICT", "VICTORY", "IMPROVE", "경쟁과 대립을 뚫고 우위를 확보한다", 0.4),
    ("PLANNING", "MOVEMENT", "ACCELERATE", "검토하던 계획이 실제 실행으로 넘어간다", 0.3),
    ("PLANNING", "EXPANSION", "CONTINUE", "계획이 협력과 더 넓은 기회로 확장된다", 0.3),
    ("MESSAGE", "MOVEMENT", "ACCELERATE", "소식이 들어오며 실제 진행 속도가 빨라진다", 0.3),
    ("OFFER", "FORMALIZATION", "FORMALIZE", "제안이 구체적인 약속과 공식 조건으로 발전한다", 0.3),
    ("MOVEMENT", "FORMALIZATION", "FORMALIZE", "빠르게 진행되던 일이 계약과 절차로 구체화된다", 0.3),
    ("MOVEMENT", "SUCCESS", "IMPROVE", "빠른 실행이 눈에 보이는 성과로 이어진다", 0.4),
    ("SKILL", "WORK", "CONTINUE", "보유한 능력이 반복 작업과 실제 결과물로 연결된다", 0.3),
    ("SKILL", "SUCCESS", "IMPROVE", "능력을 집중해 인정받는 결과를 만든다", 0.4),
    ("LEARNING", "SKILL", "IMPROVE", "학습과 준비가 실제로 쓸 수 있는 능력으로 발전한다", 0.3),
    ("WORK", "SUCCESS", "IMPROVE", "꾸준한 작업이 성과와 인정을 만든다", 0.4),
    ("WORK", "COMPLETION", "CONTINUE", "반복해 쌓은 일이 완성 단계에 도달한다", 0.4),
    ("MATERIAL_OPPORTUNITY", "WORK", "CONTINUE", "현실적인 기회를 구체적인 실행과 노동으로 키운다", 0.3),
    ("SUCCESS", "COMPLETION", "CONTINUE", "성과가 보상과 완전한 마무리로 이어진다", 0.4),
    ("SUCCESS", "BURDEN", "DECLINE", "성과가 커진 만큼 책임과 압박도 무거워진다", -0.2),
    ("ABUNDANCE", "GENEROSITY", "CONTINUE", "풍요로운 자원이 나눔과 지원으로 확장된다", 0.2),
    ("GENEROSITY", "GREED", "DECLINE", "주고받던 관계에 욕심과 불균형이 개입한다", -0.4),
    ("RELATIONSHIP", "FORMALIZATION", "FORMALIZE", "상호 관계가 약속·동맹·공식 구조로 굳어진다", 0.3),
    ("RELATIONSHIP", "DISHARMONY", "DECLINE", "연결되어 있던 관계에 기대 차이와 불화가 드러난다", -0.4),
    ("DISHARMONY", "RELATIONSHIP", "RESOLVE", "엇갈린 관계가 다시 대화와 연결을 시도한다", 0.2),
    ("FORTUNE", "SUCCESS", "IMPROVE", "외부 기회가 실제 성과와 상승으로 연결된다", 0.4),
    ("AUTHORITY", "JUSTICE", "CONTINUE", "권한이 증거와 공정한 기준에 따라 행사된다", 0.2),
    ("AUTHORITY", "ABUSE", "DECLINE", "권한이 책임을 잃고 통제와 해로운 강압으로 변한다", -0.5),
    ("CONTROL", "STAGNATION", "BLOCK", "붙잡으려는 태도가 변화와 이동을 막는다", -0.3),
    ("ATTACHMENT", "ENDING", "RELEASE", "집착하던 대상을 놓으며 한 국면을 끝낸다", 0.2),
    ("DECEPTION", "DISCLOSURE", "RESOLVE", "숨기던 사실이 밖으로 드러나며 판단 근거가 생긴다", 0.3),
    ("PRUDENCE", "MATERIAL_OPPORTUNITY", "IMPROVE", "신중한 판단이 현실적인 기회를 포착한다", 0.3),
    ("RESPONSIBILITY", "SECURITY", "CONTINUE", "꾸준한 책임 이행이 안정된 기반을 만든다", 0.3),
    ("INDEPENDENCE", "LEGACY", "CONTINUE", "개인의 성취가 오래 남는 기반과 유산으로 이어진다", 0.3),
]


def _card_metadata() -> list[dict[str, str | int | None]]:
    major = [
        ("FOOL", "바보", "The Fool"), ("MAGICIAN", "마법사", "The Magician"),
        ("HIGH_PRIESTESS", "여사제", "The High Priestess"), ("EMPRESS", "여황제", "The Empress"),
        ("EMPEROR", "황제", "The Emperor"), ("HIEROPHANT", "교황", "The Hierophant"),
        ("LOVERS", "연인", "The Lovers"), ("CHARIOT", "전차", "The Chariot"),
        ("STRENGTH", "힘", "Strength"), ("HERMIT", "은둔자", "The Hermit"),
        ("WHEEL_OF_FORTUNE", "운명의 수레바퀴", "Wheel of Fortune"), ("JUSTICE", "정의", "Justice"),
        ("HANGED_MAN", "매달린 사람", "The Hanged Man"), ("DEATH", "죽음", "Death"),
        ("TEMPERANCE", "절제", "Temperance"), ("DEVIL", "악마", "The Devil"),
        ("TOWER", "탑", "The Tower"), ("STAR", "별", "The Star"),
        ("MOON", "달", "The Moon"), ("SUN", "태양", "The Sun"),
        ("JUDGEMENT", "심판", "Judgement"), ("WORLD", "세계", "The World"),
    ]
    cards: list[dict[str, str | int | None]] = []
    for number, (code, ko, en) in enumerate(major):
        cards.append({"code": code, "name_ko": ko, "name_en": en, "arcana": "MAJOR", "suit": None, "rank": None, "number": number})
    ranks = [("ACE", 1), ("TWO", 2), ("THREE", 3), ("FOUR", 4), ("FIVE", 5), ("SIX", 6), ("SEVEN", 7), ("EIGHT", 8), ("NINE", 9), ("TEN", 10), ("PAGE", None), ("KNIGHT", None), ("QUEEN", None), ("KING", None)]
    for suit in ("WANDS", "CUPS", "SWORDS", "PENTACLES"):
        for rank, number in ranks:
            cards.append({"code": f"{rank}_OF_{suit}", "name_ko": "", "name_en": "", "arcana": "MINOR", "suit": suit, "rank": rank, "number": number})
    return cards


def _write(name: str, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build() -> None:
    cards = _card_metadata()
    card_by_code = {card["code"]: card for card in cards}
    missing = sorted(set(card_by_code) - set(MEANINGS))
    extra = sorted(set(MEANINGS) - set(card_by_code))
    if missing or extra:
        raise SystemExit(f"Meaning catalogue mismatch. missing={missing}, extra={extra}")

    source_rows = [
        {
            "code": "WAITE_PKD_1910",
            "title": "The Pictorial Key to the Tarot, Part III",
            "author": "Arthur Edward Waite",
            "publication_year": 1910,
            "source_type": "BOOK",
            "license_status": "PUBLIC_DOMAIN",
            "source_url": "https://en.wikisource.org/wiki/The_Pictorial_Key_to_the_Tarot/Part_3",
            "rights_basis": "Published 1910; validated Wikisource transcription and public-domain source scan.",
            "priority": 10,
            "is_active": "true",
        },
        {
            "code": "GOLDEN_DAWN_BOOK_T_1912",
            "title": "A Description of the Cards of the Tarot with Their Attributions (Liber LXXVIII)",
            "author": "Hermetic Order of the Golden Dawn material, published in The Equinox",
            "publication_year": 1912,
            "source_type": "MANUSCRIPT",
            "license_status": "PUBLIC_DOMAIN",
            "source_url": "https://100thmonkeypress.com/biblio/acrowley/books/equinox_1_8_1912/equinox_1_8_text.pdf",
            "rights_basis": "Published in The Equinox I(8), 1912; normalized tables only, no modern-edition text.",
            "priority": 20,
            "is_active": "true",
        },
    ]

    tag_rows = [
        {"code": code, "name_ko": profile.name_ko, "description": profile.description}
        for code, profile in sorted(TAGS.items())
    ]

    meaning_rows: list[dict[str, object]] = []
    meaning_tag_rows: list[dict[str, object]] = []
    for card in cards:
        card_code = str(card["code"])
        for orientation, spec in zip(("UPRIGHT", "REVERSED"), MEANINGS[card_code]):
            profile = TAGS[spec.primary]
            metrics = spec.metrics or profile.metrics
            meaning_rows.append({
                "card_code": card_code,
                "source_code": "WAITE_PKD_1910",
                "orientation": orientation,
                "context": "GENERAL",
                "meaning_text": spec.text,
                "advice_text": profile.advice,
                "warning_text": profile.warning or "",
                "polarity": metrics[0],
                "action_level": metrics[1],
                "speed_level": metrics[2],
                "stability_level": metrics[3],
                "ending_level": metrics[4],
                "origin": "DERIVED",
                "source_locator": spec.locator,
                "page_start": "",
                "page_end": "",
                "priority": 10,
                "review_status": "APPROVED",
                "review_method": "SOURCE_PARAPHRASE_EDITORIAL_V1",
                "review_notes": "Waite Part III paraphrase; source wording is historically inconsistent and should not be treated as modern consensus.",
                "is_active": "true",
            })
            tag_sequence = (spec.primary,) + spec.secondary
            for index, tag_code in enumerate(dict.fromkeys(tag_sequence)):
                meaning_tag_rows.append({
                    "card_code": card_code,
                    "orientation": orientation,
                    "context": "GENERAL",
                    "tag_code": tag_code,
                    "weight": 1.0 if index == 0 else max(0.55, 0.85 - 0.1 * (index - 1)),
                    "is_primary": "true" if index == 0 else "false",
                })

    correspondence_rows: list[dict[str, object]] = []

    def add_corr(card_code: str, kind: str, value: str, locator: str) -> None:
        correspondence_rows.append({
            "card_code": card_code,
            "source_code": "GOLDEN_DAWN_BOOK_T_1912",
            "correspondence_type": kind,
            "value": value,
            "source_locator": locator,
            "page_start": "",
            "page_end": "",
            "priority": 10,
            "review_status": "APPROVED",
            "review_method": "PRIMARY_TABLE_NORMALIZATION_V1",
            "review_notes": "Normalized from the 1912 Book T tables; RWS card order retained.",
            "is_active": "true",
        })

    for card_code, (title, letter, path, kind, value, element) in MAJOR_GD.items():
        locator = f"Liber LXXVIII — Trumps — {card_code}"
        add_corr(card_code, "GD_TITLE", title, locator)
        add_corr(card_code, "HEBREW_LETTER", letter, locator)
        add_corr(card_code, "TREE_PATH", path, locator)
        add_corr(card_code, kind, value, locator)
        if kind != "ELEMENT" or value != element:
            add_corr(card_code, "ELEMENT", element, locator)
        if card_code == "JUDGEMENT":
            add_corr(card_code, "ADDITIONAL_ATTRIBUTION", "SPIRIT", locator)
        if card_code == "WORLD":
            add_corr(card_code, "ADDITIONAL_ATTRIBUTION", "EARTH", locator)

    for card in cards:
        if card["arcana"] != "MINOR":
            continue
        card_code = str(card["code"])
        suit = str(card["suit"])
        rank = str(card["rank"])
        locator = f"Liber LXXVIII — Minor Arcana — {card_code}"
        add_corr(card_code, "ELEMENT", SUIT_ELEMENT[suit], locator)
        if rank == "ACE":
            add_corr(card_code, "GD_TITLE", ACE_TITLES[card_code], locator)
            add_corr(card_code, "SEPHIRAH", "KETHER", locator)
        elif card_code in PIP_GD:
            title, planet, zodiac, decan = PIP_GD[card_code]
            add_corr(card_code, "GD_TITLE", title, locator)
            add_corr(card_code, "PLANET", planet, locator)
            add_corr(card_code, "ZODIAC", zodiac, locator)
            add_corr(card_code, "DECAN", decan, locator)
            add_corr(card_code, "SEPHIRAH", SEPHIRAH_BY_RANK[rank], locator)
        else:
            add_corr(card_code, "GD_TITLE", COURT_TITLES[suit][rank], locator)
            add_corr(card_code, "COURT_ELEMENT", f"{COURT_RANK_ELEMENT[rank]}_OF_{SUIT_ELEMENT[suit]}", locator)

    relation_rows = [
        {
            "from_tag_code": left,
            "to_tag_code": right,
            "context": "",
            "relation_type": relation_type,
            "transition_text": text,
            "score_delta": delta,
            "priority": 100,
            "source_code": "",
            "source_locator": "Editorial relation grammar v1",
            "origin": "DESIGNED",
            "review_status": "APPROVED",
            "review_method": "EDITORIAL_RULE_REVIEW_V1",
            "review_notes": "Reusable semantic transition; not attributed to Waite or Golden Dawn.",
            "is_active": "true",
        }
        for left, right, relation_type, text, delta in RELATION_RULES
    ]

    _write("sources.csv", list(source_rows[0]), source_rows)
    _write("interpretation_tags.csv", ["code", "name_ko", "description"], tag_rows)
    _write("card_meanings.csv", list(meaning_rows[0]), meaning_rows)
    _write("card_meaning_tags.csv", ["card_code", "orientation", "context", "tag_code", "weight", "is_primary"], meaning_tag_rows)
    _write("card_correspondences.csv", list(correspondence_rows[0]), correspondence_rows)
    _write("relation_rules.csv", list(relation_rows[0]), relation_rows)

    readme = """# Curated Tarot Knowledge v1\n\nThis directory is the review surface for the runtime PostgreSQL seed.\n\n- `card_meanings.csv`: 156 Korean editorial paraphrases of Waite Part III (78 cards × upright/reversed).\n- `card_correspondences.csv`: Golden Dawn / Book T titles and normalized correspondences.\n- `card_meaning_tags.csv`: controlled semantic tags used by the rule engine.\n- `relation_rules.csv`: transition grammar marked `origin=DESIGNED`; these rules are **not** historical-source claims.\n\nHistorical wording is not copied into the service response. `APPROVED` means the record passed the project source/structure/editorial review, not that a professional diviner or academic institution endorsed it.\n\nSpecial decisions:\n\n1. Two of Cups has no reversed line in Waite Part III §2; the reversed value is normalized from Part III §4.\n2. RWS Strength=8 and Justice=11 are retained.\n3. Court mapping follows the source-aware RWS visual labels: mounted Knight=Fire, Queen=Water, seated King=Golden Dawn Prince/Air, Page=Earth.\n4. Judgement keeps Fire plus Spirit; World keeps Saturn plus Earth.\n5. Major-card `ELEMENT` values are normalized for elemental-dignity calculation and do not replace the primary planet/zodiac/element attribution.\n"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    print(f"Wrote {len(meaning_rows)} meanings, {len(meaning_tag_rows)} meaning-tag links, {len(correspondence_rows)} correspondences, {len(relation_rows)} relation rules.")


if __name__ == "__main__":
    build()
