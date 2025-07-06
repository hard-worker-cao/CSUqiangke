import re
import sys
import requests
import configparser

CONFIG_FILE = './peizhi.conf'

# 配置检测函数
REQUIRED_KEYS = [
    'username', 'password', 'semester_code',
    'public_course_count', 'major_course_count'
]


def validate_config(config):
    # 检查基础参数
    for key in REQUIRED_KEYS:
        if key not in config:
            print(f'配置文件缺少必要参数: {key}')
            sys.exit(1)
    # 检查课程数量和ID匹配
    try:
        public_count = int(config['public_course_count'])
        major_count = int(config['major_course_count'])
    except Exception:
        print('课程数量参数必须为整数')
        sys.exit(1)
    for i in range(1, public_count + 1):
        if f'public_course_id{i}' not in config:
            print(f'缺少公选课ID: public_course_id{i}')
            sys.exit(1)
    for i in range(1, major_count + 1):
        if f'major_course_id{i}' not in config:
            print(f'缺少专业课/体育课ID: major_course_id{i}')
            sys.exit(1)


def read_config():
    con = configparser.ConfigParser()
    con.read(CONFIG_FILE, encoding='utf-8')
    config = dict(con.items('config'))
    validate_config(config)
    return config


def build_class_urls(config, base_url):
    semester = config['semester_code']
    public_count = int(config['public_course_count'])
    major_count = int(config['major_course_count'])
    urls = []
    for i in range(1, public_count + 1):
        cid = config[f'public_course_id{i}']
        urls.append(
            f'{base_url}/jsxsd/xsxkkc/ggxxkxkOper?jx0404id={semester}{cid}&xkzy=&trjf='
        )
    for i in range(1, major_count + 1):
        cid = config[f'major_course_id{i}']
        urls.append(
            f'{base_url}/jsxsd/xsxkkc/bxqjhxkOper?jx0404id={semester}{cid}&xkzy=&trjf='
        )
    return urls


def work(base_url, url, cookie_jar):
    try:
        # 使用cookie进行GET请求
        response = requests.get(url, cookies=cookie_jar)

        if re.search('true', response.text):
            print("成功抢课!")
            return True
        if re.search('冲突', response.text):
            print(re.search('"选课失败：(.+)"', response.text).group())
            print("课程冲突，已暂停该课程选课\n")
            return True
        if re.search('当前教学班已选择！', response.text):
            print(re.search('"选课失败：(.+)"', response.text).group())
            print("当前教学班已选择！\n")
            return True
        if re.search('null', response.text):
            print("没有该 ID 所对应的课程\n")
            return False
        else:
            print(response.text)
            print("\n")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False


def main():
    config = read_config()
    base_url = 'http://csujwc.its.csu.edu.cn'

    # 直接使用自己的cookie
    cookie_jar = {
        # 填入你的cookie，格式为键值对
        'JSESSIONID': 'B0CCB93746C1C50AF0B0756CCFB875FF',
        'SF_cookie_350': '42184460'
    }

    # 验证登录状态
    main_url = f'{base_url}/jsxsd/framework/xsMain.jsp'
    response = requests.get(main_url, cookies=cookie_jar)
    if '登录' in response.text and '用户名' in response.text:
        print('cookie无效，请检查cookie是否正确或是否已过期')
        sys.exit()
    else:
        print('成功使用cookie登录教务系统')

    class_urls = build_class_urls(config, base_url)
    # 进入选课页面
    while True:
        xklc_url = f'{base_url}/jsxsd/xsxk/xklc_list'
        response = requests.get(xklc_url, cookies=cookie_jar)
        key = re.findall('href="(.+?)" target="blank">进入选课', response.text)

        if len(key) >= 1:
            break
        print('寻找选课列表中')
    response = requests.get(f'{base_url}' + key[0], cookies=cookie_jar)
    print('成功进入选课页面')
    # 抢课主循环
    while True:
        class_urls = [url for url in class_urls if not work(base_url, url, cookie_jar)]
        if len(class_urls) == 0:
            print('选课已完成，程序退出')
        # break


if __name__ == '__main__':
    main()
