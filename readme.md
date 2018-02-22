# wiremock-py

wiremock-py 是基于[WireMock](http://www.wiremock.org)实现的，使用Python批量生成不同场景下mock数据的工具

## 需求背景

在web应用的开发过程中，前后端的开发是分开进行的，为了能够尽早介入测试，前后端的测试也分开分别测。

前端测试时需要依赖后端提供的数据，为了减少对后端的依赖，前端一般使用mock出来的数据；另外，对于一些真实场景中少见的数据，前端也可以通过mock数据来测试。

举个例子：

新浪[微舆情](http://wyq.sina.com/goSearch.shtml)的「传播分析」页面里有4张图表

![](img/sina.png)

对于第1张条形图(信息来源)的测试，测试点至少应该包括:

- 后端无响应的情况下图表展示是否正常
- 后端返回为空的情况下图表展示是否正常
- 后端只返回1组数据的情况下图表展示是否正常
- 后端返回50组数据的情况下图表展示是否正常
- 后端返回2组差异很大的数据时图表展示是否正常

典型的测试方法是，通过[Fiddler](https://www.telerik.com/fiddler)或者[Burp](https://portswigger.net/burp)这类工具，将后端的响应数据拦截后修改返回数据，从而达到响应的测试目的。对每张图，每个测试点，分别做这样的操作: 拦截响应包-修改响应包-返回给前端，每次只能测试一张图的一个测试点。

这样做比较低效！

wiremock-py 可以针对某个测试场景下所有的图，批量生成mock数据，然后批量检查前端图表是否显示正常。针对某个测试场景，同时测试所有的图表，而不是只能测试单个图表。


## 演示


## 功能列表

- 使用Python代码动态生成mock数据
- 使用js代码动态生成mock数据
- 使用json文件生成mock数据，并支持[mock.js](http://mockjs.com/)

## 依赖环境

- Java 1.8.0_144
- Node v8.6.0
- Python 3.4.3

## 快速开始

生成目录

  > 执行 `python mock.py -g "example/mockdir"` 来生成目录结构

填写 mappings.json、json、python、js 数据
  
  > 按照格式（下方详细内容）填写对应的数据，用于生成mock数据

运行起来

  > 执行 `python mock.py --mockdir "example/mockdir" --scene "返回差异很大的几组数据" --target "https://mall-data.com" --proxy_port 5506`

浏览器访问 [http://localhost:5506](http://localhost:5506) 来测试～


## wiremock

mock功能参考 [wiremock文档](http://wiremock.org/docs/getting-started/)，这个需要多看一下

## mockdir目录以及文件格式 

mockdir 目录结构应该是这样：


```

mockdir
    |__mappings.json              // 保存当前测试环境下所有request和response的映射关系
    |__python                     // 保存python代码，python chart_x.py --场景1 这样的调用方式可以返回一个json字符串
    |  |_chart1.py                // 这个json字符串将作为response的body体保存在 wiremock/某个场景目录/__files 目录下
    |  |_chart2.py                
    |__js                         // 保存js代码，作用类似于python代码，最终生成json数据
    |  |_chart3.js                // 最终的json数据也是作为response的body体保存在 wiremock/某个场景目录/__files 目录下
    |  |_chart4.js
    |__json                       // 保存json数据，json数据支持mock.js规则，
    |  |_chart5.json              // 最终的json数据也是作为response的body体保存在 wiremock/某个场景目录/__files 目录下
    |  |_chart6.json
    |__wiremock                   // 最终wiremock读取的目录
    |  |__scene1                  // 场景目录
    |  |  |__ mappings            // request和response的映射关系
    |  |  |  |_mapping1.json
    |  |  |  |_mapping2.json
    |  |  |__ __files             // response中的body体内容
    |  |  |  |_chart1.json
    |  |  |  |_chart2.json

```

### mappings.json

mappings.json 文件中保存了request和response之间的映射关系，即满足某些条件的request应该映射到什么样的response上。文件内容格式为：

```
[
    {
        "mapping_name": "非图表请求",
        "request": {
            "urlPathPattern":"/(?!api).*",
            "method": "ANY"
        },
        "response": {
            "默认场景": {
                "proxyBaseUrl": "target"
            },
            "场景2": {
                "status": 200
            }
        } 
    }
]
```

#### mapping_name

`mapping_name`为映射关系名称，只是个名称而已

#### request

`request` 为要拦截的request请求格式，当匹配到特定匹配条件的request后，request匹配格式可以参考wiremock的[Request Matching部分](http://wiremock.org/docs/request-matching/)

**注意细节**

如果 mappings.json 里所有的mapping规则都无法匹配某个request，这个request对应的response将会是`404`，而不是走`target`的真实请求。

比如 一个 request 为 [http://localhost:5506/abcde](http://localhost:5506/abcde)，target 为 [https://mall-data.com](https://mall-data.com)，当 mappings.json 里能够匹配到这个 request 时，就返回匹配规则中的 response (可以是返回某个特定的信息，也可能是返回 target 真实的返回数据，视 response 信息而定)，但如果 mappings.json 中没有匹配到这个 request，那这个 request 的 response 值就只能是`404`。

#### response

`response`为要返回的response数据，response里需要指定 **测试场景** 的名称，比如 **默认场景** 下的response是啥，**场景2** 下的response是啥。

response 的格式，可以参考wiremock的[stubbing文档](http://wiremock.org/docs/stubbing/) 和 [simulating-faults文档](http://wiremock.org/docs/simulating-faults/)

**response 中支持使用json文件**

如果想直接返回一个json文件里的json数据，可以指定 `"json"` 为目标文件（目标json文件必须放在 `json` 目录中）

```

    {
        "mapping_name": "客流变化趋势",
        "request": {
            "urlPathPattern": "/api/v1/mall_data/overview/customer_day\\?(.*)",
            "method": "POST"
        },
        "response": {
            "默认场景": {
                "bodyFileName": {
                    "json": "客流变化趋势.json"
                } 
            }
        }
    }

```

##### json文件

json文件内容可参考：

```
{
    "success": true,
    "code": null,
    "message": null,
    "content": {
        "meta": {},
        "multi": {},
        "tab": {
            "currentValue": 99999,
            "chainValue": -0.22916559652349008
        }
    }
}
```

**json数据会自动转换成按照[mock.js](https://github.com/nuysoft/Mock/wiki)规则mock后的json数据**

比如json数据：

```

"result": [
    {
        "value": [
            "@integer(1,10000)",
            "@integer(1,10000)"
        ],
        "id": "customer_count",
        "name": "\u4eba\u6570"
    }
]

```

会按照[mock.js](https://github.com/nuysoft/Mock/wiki)规则转换成:

```
"result": [
    {
        "value": [
            7798,
            1768
        ],
        "name": "\u4eba\u6570",
        "id": "customer_count"
    }
]

```


**response 中支持使用python代码生成数据**

如果想使用python代码根据不同场景生成不同的数据作为 response 的话，可以指定 `"python"` 为指定的 目标python文件（目标python文件必须放在 `python` 目录中），`"python_args"` 为运行指定 python 代码时传的参数

```
    {
        "mapping_name": "老客数",
        "request": {
            "urlPattern": "/api/v1/mall_data/overview/customer_old\\?(.*)",
            "method": "POST"
        },
        "response": {
            "默认场景": {
                "status": 200,
                "bodyFileName": {
                    "python": "老客数.py",
                    "python_args": "默认场景"
                }
            }
        }
    }
```

**response 中支持使用js代码生成数据** 

如果想使用js代码根据不同场景生成不同的数据作为 response 的话，可以指定 `"js"` 为指定的 目标js文件（目标js文件必须放在 `js` 目录中），`"js_args"` 为运行指定 js 代码时传的参数

```
    {
        "mapping_name": "老客数",
        "request": {
            "urlPattern": "/api/v1/mall_data/overview/customer_old\\?(.*)",
            "method": "POST"
        },
        "response": {
            "默认场景": {
                "status": 200,
                "bodyFileName": {
                    "js": "老客数.js",
                    "js_args": "默认场景"
                }
            }
        }
    }
```

##### python文件

python代码中，必须包含一个 `main(scene)` 函数，内容可参考：

```

def main(scene):
    return {"kk": scene}

```

##### js文件

python中会使用Naked运行js脚本，运行方式就是 `muterun_js("js_file args")`，所以js文件需要能够从命令行中读取参数

## scene

根据 scene 参数，在 mappings.json 中选择不同的场景来返回不同的 response 数据，比如 `scene` 指定为 "场景2"时，会去 `mappings.json`中找所有规则中 response 在 "场景2" 下的应该返回的数据。**当指定的scene不存在时，会使用"默认场景"**

## target

当 response 中指定了 proxyBaseUrl 时，proxyBaseUrl 的值可以选择 `"target"`，request请求会转到target地址并将target的response返回

## proxy_port

mock server 要监听的本地端口

## rewrite

默认情况下，不会覆盖一生成的json文件，如果要覆盖，可以添加 `--rewrite`选项，比如：

`python mock.py --mockdir "mall-data_v1_1_0" --scene "一组数据" --target "https://mall-data.com" --proxy_port 5506 --rewrite`

## wiremock

如果不想生成数据，指向运行woremock来测试，可以添加 `--wiremock`选项，比如：

`python mock.py --mockdir "mall-data_v1_1_0" --scene "一组数据" --target "https://mall-data.com" --proxy_port 5506 --wiremock`


## TODO

## CHANGELOG
