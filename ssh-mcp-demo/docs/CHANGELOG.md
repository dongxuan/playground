# 更新日志

## 新增功能 - 默认配置

### 新增配置项

在 `config.json` 中新增了两个配置项:

1. **`default_remote_dir`** - 默认的远程上传目录
   - 当调用 `upload_file` 或 `upload_and_execute` 时，如果不指定 `remote_dir` 参数，将使用此默认值

2. **`default_script`** - 默认的执行脚本名称
   - 当调用 `execute_remote_script` 或 `upload_and_execute` 时，如果不指定 `script_path` 参数，将自动使用 `default_remote_dir/default_script` 作为脚本路径

### 配置示例

```json
{
  "host": "your.server.com",
  "port": 22,
  "username": "your_username",
  "password": "your_password",
  "key_file": "/path/to/your/private/key",
  "default_remote_dir": "/home/user/scripts",
  "default_script": "run.sh"
}
```

### 使用示例

配置好默认值后，你可以这样使用:

**简化版（使用默认配置）:**
```
上传 my.py 并执行
```

这相当于:
```
上传 my.py 到 /home/user/scripts，然后执行 /home/user/scripts/run.sh
```

**完整版（指定参数）:**
```
上传 my.py 到 /home/user/custom_dir，然后执行 /home/user/custom_dir/custom.sh
```

### 更新的工具

1. **`upload_file`**
   - `remote_dir` 参数现在是可选的
   - 如果不提供，将使用 `config.json` 中的 `default_remote_dir`

2. **`execute_remote_script`**
   - `script_path` 参数现在是可选的
   - 如果不提供，将使用 `config.json` 中的 `default_remote_dir/default_script`

3. **`upload_and_execute`**
   - `remote_dir` 和 `script_path` 参数都是可选的
   - 可以完全使用默认配置，只需要提供 `local_file`

### 向后兼容

这些更新是向后兼容的：
- 如果你显式提供参数，仍然会使用你提供的值
- 如果不在 `config.json` 中配置默认值，需要在调用时提供相应参数
- 现有的调用方式不受影响
