var fs = require("fs")
var Mock = require('mockjs');
var program = require('commander');


program
    .option('-f, --file [path]', 'json file path')
    .parse(process.argv)

fs.readFile(program.file, function (err, data) {
    if (err) {
       return console.error(err);
    }

    var return_data = {};

    try {
        var jsonObject = JSON.parse(data.toString());
        var return_data = Mock.mock(jsonObject);
    }catch(e) {
        console.log(e)
    }
    console.log(JSON.stringify(return_data, null, 4));
    return JSON.stringify(return_data, null, 4)
});
