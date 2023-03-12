import sys
import os
import json
from enum import Enum

# 随机次数，100000次还算勉强，1000000次就太慢了
times = 10000
# 开始步骤
firstStepId = "WIyWlLk6GJQsqaUBKTNV-3"

# 定义步骤类，包含id、文本类型、参数


class Step:
    def __init__(self, id, textType, text, attributes={}):
        self.id = id
        self.textType = textType
        self.text = text
        self.count = 0
        self.attributes = attributes

# 定义箭头类，包含id、上一步骤id、下一步骤id
# 箭头的id是由上一步骤id和下一步骤id组成的


class Arrow:
    def __init__(self, id, source, target):
        self.id = id
        self.source = source
        self.target = target

# 定义文本类型的5种枚举：普通文本、玩家选项、属性变化、传送门、结局


class TextType(Enum):
    Normal = 0
    Option = 1
    Attribute = 2
    Portal = 3
    Ending = 4


class StepType(Enum):
    Step = 0
    Arrow = 1


# 定义步骤字典，用于存储步骤和箭头，key为步骤id，value为步骤或箭头，限制类型为Step或Arrow
steps: dict[str, Step] = {}
arrows: dict[str, Arrow] = {}

# 定义玩家属性字典，用于存储玩家属性，key为属性名，value为属性值
playerAttributes: dict[str, int] = {}

# 定义当前步骤
currentStep = None

# 定义当前步骤的上一步骤
lastStep = None

# 定义当前步骤的下一步骤
nextStep = None

# 定义当前步骤的选项
options = []

# 定义当前步骤的选项的id
optionIds = []

# 定义当前步骤的选项的文本
optionTexts = []

# 定义当前步骤的选项的文本类型
optionTextTypes = []

# 从utf-8的json文件中读取步骤


def loadStepsByFile(fileName):
    with open(fileName, "r", encoding="utf-8") as f:
        data = json.load(f)
        mxfile = data["mxfile"]
        diagram = mxfile["diagram"]
        mxGraphModel = diagram[0]["mxGraphModel"]
        root = mxGraphModel[0]["root"]
        mxCell = root[0].get("mxCell", None)
        # firstStep = None
        for step in mxCell:
            mxGeometry = step.get("mxGeometry", None)
            if (mxGeometry == None):
                continue
            # print step在mxCell中的index
            # print(mxCell.index(step))
            # mxGeometry[0]["$"].contains("relative")则为arrow，否则为step
            stepType = StepType.Step
            if ("relative" in mxGeometry[0]["$"]):
                stepType = StepType.Arrow
            if (stepType == StepType.Step):
                stepContent = step["$"]
                id = stepContent["id"]
                value = stepContent.get("value", None)
                steps[id] = Step(
                    id, 0, value)
            else:
                arrowContent = step["$"]
                id = arrowContent["id"]
                if (arrowContent.get("source", None) == None):
                    continue
                source = arrowContent["source"]
                target = arrowContent["target"]
                arrows[id] = Arrow(
                    id, source, target)
        object = root[0].get("object", None)
        if (object != None):
            for step in object:
                stepContent = step["$"]
                id = stepContent["id"]
                label = stepContent.get("label", None)
                # 除id和label外，均为属性
                attributes = {}
                for key in stepContent:
                    if (key != "id" and key != "label"):
                        attributes[key] = stepContent[key]
                # 如果label不为空，则为普通文本
                if (label != None):
                    steps[id] = Step(id, TextType.Normal, label, attributes)

        return steps, arrows


def printSteps():
    # loadStepsByFile("test_tbstep.json")
    steps, arrows = loadStepsByFile("test.json")
    if (firstStepId == None):
        firstStep = checkFirstStep()
    else:
        firstStep = steps[firstStepId]
    printTest("firstStep:", firstStep.id)
    # 重复100次，每次都从第一个步骤开始
    for i in range(times):
        doStep(firstStep)
    # 输出所有步骤的id和count
    for stepId in steps:
        step = steps[stepId]
        if (not isinstance(step, Step)):
            continue
        # count/times的百分比,取两位小数
        percent = round(step.count*100/times, 4)
        printResult(step.id, step.text, percent, "%")

# 获取第一个步骤，即没有箭头指向的步骤


def checkFirstStep():
    firstStep = None
    for stepId in steps:
        step = steps[stepId]
        if (not isinstance(step, Step)):
            continue
        # 遍历所有步骤，如果有箭头指向该步骤，则该步骤不是第一个步骤
        for arrowId in arrows:
            arrow = arrows[arrowId]
            # 如果arrow的类型不是Arrow，则跳过
            if (not isinstance(arrow, Arrow)):
                continue
            if (arrow.target == stepId):
                step = None
                break
        if (step != None):
            firstStep = step
            break
    return firstStep

# 获取下一个步骤，即被箭头指向的步骤


def getNextStepId(step: Step):
    # 记录可选的下一步骤id
    nextStepIds = []
    for arrowId in arrows:
        arrow = arrows[arrowId]
        # 如果arrow的类型不是Arrow，则跳过
        if (not isinstance(arrow, Arrow)):
            continue
        # printTest(arrow.id, arrow.source, arrow.target)
        if (arrow.source == step.id):
            # printTest("=>" + arrow.id)
            # 如果nextStepIds已经有arrow.target，则跳过
            if (arrow.target in nextStepIds):
                continue
            nextStep = steps[arrow.target]
            if (checkAttribute(nextStep.attributes)):
                nextStepIds.append(arrow.target)
    if (len(nextStepIds) == 0):
        return None
    # 随机选择一个下一步骤id
    import random
    nextStepId = random.choice(nextStepIds)
    return nextStepId

# def getStepById(id):
#     return steps[id]

# 执行步骤=


def doStep(step: Step):
    # printTest("步骤：")
    # printTest(step.id, step.text)
    step.count += 1
    nextStepId = getNextStepId(step)
    if (nextStepId == None):
        return
    nextStep = steps[nextStepId]
    solveAttribute(step.attributes)
    return doStep(steps[nextStepId])


def solveAttribute(attribute: dict[str, str]):
    # 如果attribute内容为空，则直接返回
    if (len(attribute) == 0):
        return
    printTest("变化：", attribute)
    for key in attribute:
        value = attribute[key]
        # 如果value是数字，则直接赋值
        if (value.isdigit()):
            playerAttributes[key] = int(value)
        # 如果value是字符串，则需要解析
        # 如果以+开头，则为增加
        # 如果以-开头，则为减少
        # 如果以*开头，则为乘以
        # 如果以/开头，则为除以
        # 如果以%开头，则为取余
        # 如果以=开头，则为赋值
        # 如果是true或false，则为布尔值
        # 如果以<、>、<=、>=、==、!=开头，则为比较，不需要处理
        elif (value.startswith("+")):
            playerAttributes[key] += int(value[1:])
        elif (value.startswith("-")):
            playerAttributes[key] -= int(value[1:])
        elif (value.startswith("*")):
            playerAttributes[key] *= int(value[1:])
        elif (value.startswith("/")):
            playerAttributes[key] /= int(value[1:])
        elif (value.startswith("%")):
            playerAttributes[key] %= int(value[1:])
        elif (value.startswith("=") and value[1:].isdigit()):
            playerAttributes[key] = int(value[1:])
        elif (value == "true"):
            playerAttributes[key] = True
        elif (value == "false"):
            playerAttributes[key] = False
        elif (value.startswith("<") or value.startswith(">") or value.startswith("<=") or value.startswith(">=") or value.startswith("==") or value.startswith("!=")):
            pass
        else:
            Warning("未知属性", key, value)
    printTest("结果", playerAttributes)


def checkAttribute(attribute: dict[str, str]):
    # 如果attribute内容为空，则直接返回
    if (len(attribute) == 0):
        return True
    for key in attribute:
        value = attribute[key]
        # 如果以<、>、<=、>=、==、!=开头，则为比较
        if (value.startswith("<")):
            if (playerAttributes[key] >= int(value[1:])):
                return False
        elif (value.startswith(">")):
            if (playerAttributes[key] <= int(value[1:])):
                return False
        elif (value.startswith("<=")):
            if (playerAttributes[key] > int(value[2:])):
                return False
        elif (value.startswith(">=")):
            if (playerAttributes[key] < int(value[2:])):
                return False
        elif (value.startswith("==")):
            if (playerAttributes[key] != int(value[2:])):
                return False
        elif (value.startswith("!=")):
            if (playerAttributes[key] == int(value[2:])):
                return False
    return True


def printTest(*str):
    # print(*str)
    return


def printResult(*str):
    print(*str)
    return


printSteps()
