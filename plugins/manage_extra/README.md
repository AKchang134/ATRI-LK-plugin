使用本插件时，可自行修改执行命令所需的权限等级。  

`SPECPERM` 是本插件新增的权限，你可以在本插件的配置中修改具有 SPECPERM 权限的成员的 QQ 号。  

e.g.:  
（添加命令）
```
your_cmd = plugin.on_command("your_cmd", "your_cmd_docs", permission=SPECPERM)
```

（配置文件）
```
"special_perms": [
  "10001",
  "10002",
  ...
]
```
