# IP-Parser

解析特定函数：
```bash
python main.py <function_name> <project_path>(optional, default=input) <output_path>(optional, default=output)
```

配置库函数：在 `config` 文件夹下创建 `.json` 文件即可并填写，格式可以参考给出的两个样例，配置后程序会自动解析该文件夹下所有文件中的所有函数。给出的两个配置文件名仅为样例，实际配置时对文件名没有任何要求。