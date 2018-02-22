#coding: utf-8

import logging
import os
import json
import collections
import shutil
import subprocess
import sys
import importlib
import getopt
from Naked.toolshed.shell import muterun_js


logging.basicConfig(level="DEBUG")
CURRENT_DIR = os.path.split(os.path.realpath(__file__))[0]
MOCK_JS_PATH = CURRENT_DIR + "/mockjs/mock.js"
WIREMOCK_JAR_PATH = CURRENT_DIR + "/Jar/wiremock-standalone-2.8.0.jar"


def run(mockdir, scene, target, rewrite=False, debug_flag=None):
    """
    根据mappings.json文件、scene和target参数，生成wiremock/scene目录，
    以及scene目录下的__files和mappings两个目录，
    __files目录下保存response中body体内的json内容，
    mappings目录下保存request和response之间的映射关系
    """

    # 检查文件目录是否存在
    if not os.path.isdir(mockdir):
        logging.error(mockdir + " 不存在")
        raise Exception()

    mappings_file = mockdir + "/mappings.json"
    if not os.path.exists(mappings_file):
        logging.error(mappings_file + " 不存在")
        raise Exception()

    # 读取mappings.json
    logging.debug("读取" + mappings_file + "...")
    try:
        with open(mappings_file, encoding="utf-8") as f:
            mappings = json.loads(f.read())
    except Exception as ex:
        logging.error("加载" + mappings_file + "失败:" + str(ex))
        raise ex

    # 创建场景目录
    # TODO: 这里这个删除目录的操作会不会有危险？
    scene_dir = mockdir + "/wiremock/" + scene
    if os.path.exists(scene_dir):
        # shutil.rmtree(scene_dir)
        pass
    else:
        os.mkdir(scene_dir)
        logging.debug("创建目录成功: " + scene_dir)

    scene_file_dir = scene_dir + "/__files"
    if os.path.exists(scene_file_dir):
        # shutil.rmtree(scene_file_dir)
        pass
    else:
        os.mkdir(scene_file_dir)
        logging.debug("创建目录成功: " + scene_file_dir)

    scene_mappings_dir = scene_dir + "/mappings"
    if os.path.exists(scene_mappings_dir):
        # shutil.rmtree(scene_mappings_dir)
        pass
    else:
        os.mkdir(scene_mappings_dir)
        logging.debug("创建目录成功: " + scene_mappings_dir)

    # path中添加python目录
    python_dir = mockdir + "/python" 
    sys.path.append(os.path.abspath(python_dir)) #

    js_dir = mockdir + "/js"
    json_dir = mockdir + "/json"
    config = {
        "scene": scene,
        "scene_dir": scene_dir,
        "target": target,
        "scene_file_dir": scene_file_dir,
        "scene_mappings_dir": scene_mappings_dir,
        "python_dir": python_dir,
        "js_dir": js_dir,
        "json_dir": json_dir
    }
    logging.debug("生成配置文件: " + json.dumps(config))

    # 对mappings中所有的mapping做处理
    if debug_flag != None:
        mappings = mappings[debug_flag:debug_flag+1]

    for mapping in mappings:
        mapping2wiremock(mapping, config, rewrite)

# 处理mapping里的request和response，生成mappings文件夹里的json文件和__files里的json文件
def mapping2wiremock(mapping, config, rewrite=False):

    mapping_name = mapping.get("mapping_name")
    request = mapping.get("request")
    response = mapping.get("response")

    logging.debug("开始处理mapping信息: " + mapping_name)

    # mappings里的json文件由request和response主体组成，文件名为mapping_name
    # request 这里不做处理，全部拷贝后传给wiremock
    # response里的内容需要做一些替换
    # response中的内容会生成__files里的json文件
    # TODO: 处理mapping_name中的特殊字符

    mapping_name = mapping_name.replace(" ", "_")
    mapping_name = mapping_name.replace("/", "_")

    mappings_json_file_path = config.get("scene_mappings_dir") + "/" + mapping_name + ".json"

    

    mapping_dict = {
        "request": request,
        "response": None
    }

    # 处理response
    # 先找指定场景名称下的response内容，如果没有就找默认场景下的response内容
    if config.get("scene") in response:
        logging.debug("开始处理场景 " + config.get("scene") + " 下的response")
        resp_json = response.get(config.get("scene"))
        mapping_dict["response"] = response2json(resp_json, config, rewrite)
    elif "default" in response:
        logging.debug("没有找到对用的场景 " + config.get("scene") + ", 使用默认场景生成数据")
        resp_json = response.get("default")
        mapping_dict["response"] = response2json(resp_json, config, rewrite)
    else:
        logging.error("没有找到对用的场景: " + config.get("scene") + ", 也没有默认场景可以使用")
        raise Exception()
    
    if os.path.exists(mappings_json_file_path) and rewrite == False:
        logging.info(mappings_json_file_path + " 已存在，不覆盖，跳过...")
    else:
        with open(mappings_json_file_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(mapping_dict, indent=4))
            logging.debug("保存mapping文件成功: " + mappings_json_file_path)


# 处理response内容，默认格式与wiremock保持一致，只修改定制的内容
def response2json(resp_json, config, rewrite=False):

    if resp_json.get("fault") == None:

        # 替换 target 字符串 为url地址
        if resp_json.get("proxyBaseUrl") == "target":
            resp_json["proxyBaseUrl"] = config.get("target")
            logging.debug("替换proxyBaseUrl为" + config.get("target"))

        # 如果不写status则默认填上200
        if resp_json.get("proxyBaseUrl") == None and resp_json.get("status") == None:
            resp_json["status"] = 200
            logging.debug("添加status为200")
        # 如果不写header信息则填写默认header
        if resp_json.get("proxyBaseUrl") == None and resp_json.get("headers") == None:
            resp_json["headers"] = {
                "Date": "Wed, 24 Jan 2018 03:45:27 GMT",
                "Content-Type": "application/json; charset=utf-8",
                "Connection": "keep-alive",
                "X-DNS-Prefetch-Control": "off",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "SAMEORIGIN",
                "X-Download-Options": "noopen",
                "X-XSS-Protection": "1; mode=block",
                "ETag": "W/\"8c-hmAYfc9iFQt2H4iztNLuwg\""
            }

    # 处理bodyFileName里的内容，按照json、python、js的顺序生成json数据
    if resp_json.get("bodyFileName") != None:

        body_json = resp_json.get("bodyFileName").get("json")

        body_python = resp_json.get("bodyFileName").get("python")
        python_args = resp_json.get("bodyFileName").get("python_args")

        body_js = resp_json.get("bodyFileName").get("js")
        js_args = resp_json.get("bodyFileName").get("js_args")

        if body_json != None:
            resp_json["bodyFileName"] = body2json(body_type="json", file_name=body_json, \
                                                    config=config, rewrite=rewrite, args=None)
        elif body_python != None:
            resp_json["bodyFileName"] = body2json(body_type="python", file_name=body_python, \
                                                    config=config, rewrite=rewrite, args=python_args)
        elif body_js != None:
            resp_json["bodyFileName"] = body2json(body_type="js", file_name=body_js, \
                                                    config=config, rewrite=rewrite, args=js_args)
        else:
            logging.error("bodyFileName中必须包含 json、python 和 js 中的一项")
            raise Exception()

    return resp_json

def body2json(body_type, file_name, config, rewrite=False, args=None):
    logging.debug("开始处理body中的" + body_type + "数据...")

    if body_type == "json":
        file_path = config.get("json_dir") + "/" + file_name
    elif body_type == "python":
        file_path = config.get("python_dir") + "/" + file_name
    elif body_type == "js":
        file_path = config.get("js_dir") + "/" + file_name
    else:
        logging.error("不支持的bodyfile格式: " + body_type)
        raise Exception()

    body_file_name = "".join(file_name.split(".")[:-1]) + ".txt"
    body_file_path = config.get("scene_file_dir") + "/" + body_file_name

    if os.path.exists(body_file_path) and rewrite == False:
        logging.info(body_file_path + " 已存在，不覆盖，跳过...")
        return body_file_name

    if not os.path.exists(file_path):
        logging.error("文件不存在: " + file_path)
        raise Exception()

    if body_type == "json":
        json_dict = node_exec(MOCK_JS_PATH, "-f " + file_path)
    elif body_type == "python":
        json_dict = python_exec(file_path, args)
    elif body_type == "js":
        json_dict = node_exec(file_path, args)
    else:
        logging.error("不支持的bodyfile格式: " + body_type)
        raise Exception()

    if os.path.exists(body_file_path) and rewrite == False:
        logging.info(body_file_path + " 已存在，不覆盖，跳过...")
    else:
        with open(body_file_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(json_dict, indent=4))
            logging.debug("保存json文件成功: " + body_file_path)
    return body_file_name
    
def python_exec(python_file_path, python_args=None):
    m_path = "".join(python_file_path.split(".")[:-1])
    m_str = m_path.replace("/", ".")
    try:
        m = importlib.import_module(m_str)
        logging.debug("加载" + m_str + "成功")
    except Exception as ex:
        logging.error("加载" + m_str + "失败: " + str(ex))
        raise ex
    logging.debug("执行" + m_str +".main(" + str(python_args) + ")...")
    v = m.main(python_args)
    logging.debug("执行结果: " + str(v))
    return v

def node_exec(js_file_path, js_args=None):
    node_cmd = js_file_path + " " + str(js_args)
    try:
        ret = muterun_js(node_cmd)
        logging.debug("执行 " + node_cmd)
        ret_json = ret.stdout
        ret_dict = json.loads(ret_json.decode("utf-8"))
        logging.debug("执行结果: " + str(ret_dict))
        if ret.exitcode != 0:
            raise Exception("nodejs return not 0")
        return ret_dict
    except BaseException as ex:
        logging.warn("nodejs error: " + str(ex))

def generate(mockdir):
    logging.debug("正在生成目录 " + os.path.realpath(mockdir))
    if os.path.exists(mockdir):
        logging.error(mockdir + " 已存在，请先删除")
        sys.exit(2)
    if mockdir.find(".") > 0:
        logging.info("目录名不支持'.'，自动替换为'_'")
        mockdir = mockdir.replace(".", "_")

    os.mkdir(mockdir)
    logging.debug("创建目录成功: " + mockdir)

    js_dir = mockdir + "/js"
    json_dir = mockdir + "/json"
    python_dir = mockdir + "/python"
    wiremock_dir = mockdir + "/wiremock"
    mappings_file_path = mockdir + "/mappings.json"

    # TODO: 这些可以写到配置文件中
    mapping_info = [
        {
            "mapping_name": "request url not start with /api",
            "request": {
                "urlPattern":"/(?!api).*",
                "method": "ANY"
            },
            "response": {
                "default": {
                    "proxyBaseUrl": "target"
                }
            } 
        }
    ]

    for i in js_dir, json_dir, python_dir, wiremock_dir:
        os.mkdir(i)
        logging.debug("创建目录成功: " + i)
        with open(i + "/readme.md", "w", encoding="utf-8") as f:
            f.write("这个文件是自动生成的\n")

    with open( mappings_file_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(mapping_info, indent=4))
    logging.debug("创建文件成功：" + mappings_file_path)

    logging.debug("生成目录完成：" + os.path.realpath(mockdir))


def usage():
    logging.info("\n\nUsage:\n\t%s [--mockdir|--scene|--target|--proxy_port|--generate|--wiremock|--rewrite] args...." %sys.argv[0])
    logging.info("\n\nOr generate new folders:\n\t%s [-g] path" % sys.argv[0])
    logging.info("\n\nOr just run wiremock:\n\t%s [-w] path" % sys.argv[0])


if __name__ == "__main__":

    mockdir = ""
    scene = ""
    target = ""
    proxy_port = 5506
    generate_path = None
    wiremock = False
    rewrite = False

    try:  
        opts,args = getopt.getopt(sys.argv[1:], "m:s:t:p:g:wr", ["mockdir=", "scene=", "target=", "proxy_port=", "generate=", "wiremock", "rewrite"])

        for opt,arg in opts:  
            if opt in ("-m", "--mockdir"):  
                mockdir = arg 
            elif opt in ("-s", "--scene"): 
                scene = arg
            elif opt in ("-t", "--target"):
                target = arg
            elif opt in ("-p", "--proxy_port"):
                proxy_port = arg
            elif opt in ("-g", "--generate"):
                generate_path = arg
            elif opt in ("-w", "--wiremock"):
                wiremock = True
            elif opt in ("-r", "--rewrite"):
                rewrite = True
            else:  
                usage()
                sys.exit(1)
    except getopt.GetoptError:  
        usage()
        sys.exit(1) 

    logging.debug("mockdir=" + mockdir + ", scene=" + scene + ", target=" + target \
                    + ", proxy_port=" + str(proxy_port) + ", generate=" + str(generate_path) \
                    + ", wiremock=" + str(wiremock) + ", rewrite=" + str(rewrite))


    if generate_path != None:
        generate(generate_path)
        sys.exit(0)

    # 只运行wiremock，不生成mock数据，针对以及生成好数据的情况
    if wiremock != True:
        #TODO: 输入检查
        run(mockdir=mockdir, scene=scene, target=target, rewrite=rewrite)

    java_cmd = 'java -jar ' + WIREMOCK_JAR_PATH \
            + ' --port ' + str(proxy_port) \
            + ' --root-dir "' + mockdir + '/wiremock/' + scene + '"'\
            + ' --match-headers Content-Type,SOAPAction'
    logging.info(java_cmd)
    try:
        p = subprocess.Popen(java_cmd, shell=True)
        if p.wait() != 0:
            raise Exception("wiremock.jar return not 0")
    except BaseException as ex:
        logging.warn("wiremock error: " + str(ex))
        p.kill()
        logging.debug("java process stoped.")
    #TODO: 考虑与wiremockUI的目录兼容

