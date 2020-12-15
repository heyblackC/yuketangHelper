# -*- coding: utf-8 -*-
# version:5.0
# developed by zk chen and MR.Li
# V3版本仅能刷项目管理概论作业题
# V4版本由李同学改良，可以刷用户名下所有的课程的线上作业
# V5版本旨在跨学院使用，在微电子学院网课中发现了填空题类型，因此兼容了填空题，另外增加了交互，可以选择想刷哪个课程
import time
import requests
import re
import json

# 以下的csrftoken和sessionid需要改成自己登录后的cookie中对应的字段！！！！而且脚本需在登录雨课堂状态下使用
# 登录上华工研究生雨课堂，然后按F12-->选Application-->找到它的cookies，寻找csrftoken和sessionid字段，并复制到下面两行即可
csrftoken = "yours" #需改成自己的
sessionid = "yours" #需改成自己的

# 会自动跳过已经完成的题目，无须担心，如果运行一遍后，仍有遗漏，再次运行即可。
# 因为作业答案在网页接口中返回了，因此本脚本才能自动答题
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:83.0) Gecko/20100101 Firefox/83.0',
    'Content-Type': 'application/json;charset=UTF-8',
    'Cookie': 'csrftoken=' + csrftoken + '; sessionid=' + sessionid + '; university_id=3078; platform_id=3',
    'x-csrftoken': csrftoken,
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'university-id': '3078',
    'xtbz': 'cloud',
}

leaf_type = {
    "video": 0,
    "homework": 6,
    "exam": 5,
    "recommend": 3,
    "discussion": 4
}

def do_homework(submit_url, classroom_id, course_sign, course_name):
    # second, need to get homework ids
    get_homework_ids = "https://gsscut.yuketang.cn/mooc-api/v1/lms/learn/course/chapter?cid="+str(classroom_id)+"&term=latest&uv_id=3078&sign="+course_sign
    homework_ids_response = requests.get(url=get_homework_ids, headers=headers)
    homework_json = json.loads(homework_ids_response.text)
    homework_ids = []
    try:
        for i in homework_json["data"]["course_chapter"]:
            for j in i["section_leaf_list"]:
                if "leaf_list" in j:
                    for z in j["leaf_list"]:
                        #print(z['leaf_type'], z['name'], z['id'])
                        if z['leaf_type'] == leaf_type["homework"]:
                            print(z['name'], z['leaf_type'], leaf_type["homework"], z['id'])
                            homework_ids.append(z["id"])
                else:
                    if j['leaf_type'] == leaf_type["homework"]:
                        homework_ids.append(j["id"])
        print(course_name+"共有"+str(len(homework_ids))+"个作业喔！")
        print(homework_ids)
    except:
        print("fail while getting homework_ids!!! please re-run this program!")
        raise Exception("fail while getting homework_ids!!! please re-run this program!")

    # finally, we have all the data needed
    for homework in homework_ids:
        get_leaf_type_id_url = "https://gsscut.yuketang.cn/mooc-api/v1/lms/learn/leaf_info/"+str(classroom_id)+"/"+str(homework)+"/?term=latest&uv_id=3078"
        leaf_response = requests.get(url=get_leaf_type_id_url, headers=headers)
        try:
            leaf_id = json.loads(leaf_response.text)["data"]["content_info"]["leaf_type_id"]
        except:
            continue
        problem_url = "https://gsscut.yuketang.cn/mooc-api/v1/lms/exercise/get_exercise_list/"+str(leaf_id)+"/?term=latest&uv_id=3078"
        id_response = requests.get(url=problem_url, headers=headers)
        dictionary = json.loads(id_response.text)
        for pro in dictionary["data"]["problems"]:
            if pro["user"]["is_show_answer"]:
                continue
            answer = ""
            answer_key = ""
            # 有的问题可能是填空题，比较难搞，它的key为answers
            try:
                if pro["content"]["Type"].find("FillBlank") < 0:
                    answer =  pro["user"]["answer"]
                    answer_key = "answer"
                else:
                    answer = pro["user"]["answers"]
                    for key,value in answer.items():
                        if isinstance(value,list):
                            answer[key] = value[0]
                    answer_key = "answers"
            except:
                print("问题类型很奇怪，安全起见跳过～")
                continue
            submit_json_data = {
                "classroom_id": int(classroom_id),
                "problem_id": pro["content"]["ProblemID"],
                answer_key: answer
            }
            response = requests.post(url=submit_url, headers=headers, data=json.dumps(submit_json_data))
            # 有可能网络阻塞，要延迟30s
            print(response.text)
            try:
                delay_time = re.search(r'Expected available in(.+?)second.',response.text).group(1).strip()
                print("由于网络阻塞，万恶的雨课堂，要阻塞" +str(delay_time)+"秒")
                time.sleep(float(delay_time)+0.5)
                print("恢复工作啦～～")
                response = requests.post(url=submit_url, headers=headers, data=json.dumps(submit_json_data))
            except:
                pass
            time.sleep(0.5)
        print(dictionary["data"]["name"] + "已经完成！！满分！！！")

if __name__ == "__main__":
    your_courses = []
    course = {}

    # first, need to get classroom_id
    get_classroom_id = "https://gsscut.yuketang.cn/mooc-api/v1/lms/user/user-courses/?status=1&page=1&no_page=1&term=latest&uv_id=3078"
    submit_url = "https://gsscut.yuketang.cn/mooc-api/v1/lms/exercise/problem_apply/?term=latest&uv_id=3078"
    classroom_id_response = requests.get(url=get_classroom_id, headers=headers)
    try:
        for ins in json.loads(classroom_id_response.text)["data"]["product_list"]:
            # print(ins["course_name"])
            course_name = ins["course_name"]
            classroom_id = ins["classroom_id"]
            course_sign = ins["course_sign"]
            your_courses.append({
                "course_name": course_name,
                "classroom_id": classroom_id,
                "course_sign": course_sign
            })
    except Exception as e:
        print("fail while getting classroom_id!!! please re-run this program!")
        raise Exception("fail while getting classroom_id!!! please re-run this program!")
    for index, value in enumerate(your_courses):
        print("编号："+str(index+1)+" 课名："+str(value["course_name"]))
    number = input("你想刷哪门课呢？请输入编号。输入0表示全部课程都刷一遍\n")
    if int(number)==0:
        for ins in your_courses:
            do_homework(submit_url, ins["classroom_id"], ins["course_sign"], ins["course_name"])
    else:
        number = int(number)-1
        do_homework(submit_url, your_courses[number]["classroom_id"], your_courses[number]["course_sign"], your_courses[number]["course_name"])

