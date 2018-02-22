var options = process.argv;

if (options[i].indexOf("后端只返回1组数据")==0) {
    var resp = {
        "sb": [
            "{\"name\":\"新浪微博\",\"count\":\"1551374\"}"
        ]
    };
    console.log(JSON.stringify(resp));
}



